"""Local research workflow safeguards. Raw OOS files are not a security boundary."""

from datetime import date
import threading
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from backend.app import db, services
from engine.runner import RunConfig
from engine.data import identities
from engine.execution_profiles import data_hashes, source_identity
from engine.canonical import digest
from engine.legacy import metrics

router = APIRouter(prefix="/api")
workflow_lock = threading.RLock()
SEGMENTS = ("development", "validation", "out-of-sample")


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Range(Body):
    start: str
    end: str


class SplitBody(Body):
    name: str = Field(min_length=1, max_length=160)
    description: str = ""
    ranges: dict[str, Range]
    dataset_profile: str = "legacy_2024_2026"


def validate_ranges(ranges, dataset_profile="legacy_2024_2026"):
    if set(ranges) != set(SEGMENTS):
        raise ValueError("Provide Development, Validation and Out-of-Sample ranges")
    warnings = []
    previous = None
    for segment in SEGMENTS:
        r = ranges[segment]
        RunConfig(
            start=r["start"], end=r["end"], dataset_profile=dataset_profile
        ).validate()
        if previous:
            if r["start"] < previous:
                raise ValueError("Research ranges overlap or are out of order")
            if r["start"] > previous:
                warnings.append(
                    f'Gap before {segment}: {previous} to {r["start"]} (end exclusive)'
                )
        previous = r["end"]
    return warnings


@router.post("/research-splits")
def create_split(body: SplitBody):
    ranges = {k: v.model_dump() for k, v in body.ranges.items()}
    warnings = validate_ranges(ranges, body.dataset_profile)
    with db.Session.begin() as s:
        row = db.ResearchSplit(
            name=body.name,
            description=body.description,
            ranges=ranges,
            warnings=warnings,
        )
        s.add(row)
        s.flush()
        s.add(
            db.ResearchSplitProfile(
                split_id=row.id, dataset_profile=body.dataset_profile
            )
        )
        return {**db.encode(row), "dataset_profile": body.dataset_profile}


def split_profile(s, id):
    p = s.get(db.ResearchSplitProfile, id)
    return p.dataset_profile if p else "legacy_2024_2026"


@router.get("/research-splits")
def splits():
    with db.Session() as s:
        return [
            {**db.encode(r), "dataset_profile": split_profile(s, r.id)}
            for r in s.scalars(
                select(db.ResearchSplit).order_by(db.ResearchSplit.created_at.desc())
            )
        ]


def require(s, model, id):
    row = s.get(model, id)
    if not row:
        raise HTTPException(404, "Research record not found")
    return row


class ExperimentBody(Body):
    name: str = Field(min_length=1, max_length=160)
    research_split_id: str
    strategy_version_id: str
    variant_id: str | None = None
    parameters: dict = {}
    settings: dict = {}


@router.post("/experiments")
def create_experiment(body: ExperimentBody):
    with db.Session.begin() as s:
        split = require(s, db.ResearchSplit, body.research_split_id)
        v = require(s, db.Version, body.strategy_version_id)
        if (
            body.variant_id
            and require(s, db.Variant, body.variant_id).strategy_version_id != v.id
        ):
            raise ValueError("Variant version mismatch")
        chosen_profile = split_profile(s, split.id)
        settings = RunConfig(**{"dataset_profile": chosen_profile, **body.settings})
        if settings.dataset_profile != chosen_profile:
            raise ValueError("Experiment dataset must match immutable research split")
        settings.validate()
        check = services.validate(v.source, body.parameters)
        if not check["valid"]:
            raise ValueError(check["error"])
        config = {
            "strategy_id": v.strategy_id,
            "strategy_version_id": v.id,
            "source": v.source,
            "source_hash": v.source_hash,
            "variant_id": body.variant_id,
            "parameters": check["parameters"],
            "settings": {
                k: value
                for k, value in settings.__dict__.items()
                if k not in ("start", "end")
            },
            "ranges": split.ranges,
            "research_split_id": split.id,
            "engine_version": services.engine_version(),
            "data_hashes": data_hashes(settings.dataset_profile),
            "dataset_profile": settings.dataset_profile,
            "dataset_identity": source_identity(settings.dataset_profile),
            "management": check.get("management", {}),
            "session": "XNYS full sessions / one entry per NY date",
            "execution": "stop-first, minute-close observation, next-minute activation, fixed target",
        }
        row = db.ExperimentSnapshot(
            name=body.name,
            research_split_id=split.id,
            strategy_version_id=v.id,
            config=config,
            snapshot_hash=digest(config),
        )
        s.add(row)
        s.flush()
        return db.encode(row)


def identity_check(config):
    if config["engine_version"] != services.engine_version():
        raise ValueError("Experiment engine changed; create a new snapshot")
    if config["data_hashes"] != data_hashes(
        config.get("dataset_profile", "legacy_2024_2026")
    ):
        raise ValueError("Experiment data changed; create a new snapshot")


@router.post("/experiments/{id}/freeze")
def freeze(id: str):
    with workflow_lock, db.Session.begin() as s:
        row = require(s, db.ExperimentSnapshot, id)
        completed = {
            r.segment
            for r in s.scalars(
                select(db.ExperimentRun).where(
                    db.ExperimentRun.experiment_snapshot_id == id
                )
            )
            if s.get(db.Run, r.run_id).status == "completed"
        }
        if not {"development", "validation"} <= completed:
            raise ValueError("Complete Development and Validation before freezing")
        identity_check(row.config)
        if not row.frozen_at:
            row.frozen_at = db.now()
        return db.encode(row)


class SegmentBody(Body):
    segment: str = Field(pattern="^(development|validation|out-of-sample)$")


@router.post("/experiments/{id}/run")
def run_segment(id: str, body: SegmentBody):
    with workflow_lock:
        with db.Session() as s:
            row = require(s, db.ExperimentSnapshot, id)
            config = row.config
            if body.segment == "out-of-sample" and not row.frozen_at:
                raise ValueError("Freeze experiment before RUN / REVEAL OOS")
            if body.segment == "validation" and not any(
                s.get(db.Run, x.run_id).status == "completed"
                for x in s.scalars(
                    select(db.ExperimentRun).where(
                        db.ExperimentRun.experiment_snapshot_id == id,
                        db.ExperimentRun.segment == "development",
                    )
                )
            ):
                raise ValueError("Complete Development before Validation")
            existing = list(
                s.scalars(
                    select(db.ExperimentRun).where(
                        db.ExperimentRun.experiment_snapshot_id == id,
                        db.ExperimentRun.segment == body.segment,
                    )
                )
            )
            for link in existing:
                if s.get(db.Run, link.run_id).status in (
                    "queued",
                    "running",
                    "completed",
                ):
                    return {"id": link.run_id}
            identity_check(config)
            name = row.name + " · " + body.segment.upper()
        rid = services.enqueue(
            config["strategy_version_id"],
            config["parameters"],
            {**config["settings"], **config["ranges"][body.segment]},
            name,
            variant_id=config["variant_id"],
            segment=body.segment,
            extra_config={
                "experiment_snapshot_id": id,
                "research_split_id": config["research_split_id"],
                "experiment_snapshot_hash": digest(config),
            },
            expected_identity=config,
        )
        with db.Session.begin() as s:
            row = s.get(db.ExperimentSnapshot, id)
            s.add(
                db.ExperimentRun(
                    run_id=rid, experiment_snapshot_id=id, segment=body.segment
                )
            )
            if body.segment == "out-of-sample":
                row.oos_run_at = db.now()
                row.oos_revealed_at = db.now()
        return {"id": rid}


def experiment_detail(s, row):
    from backend.app.main import run_detail, artifact

    links = list(
        s.scalars(
            select(db.ExperimentRun)
            .where(db.ExperimentRun.experiment_snapshot_id == row.id)
            .order_by(db.ExperimentRun.created_at)
        )
    )
    runs = {}
    for link in links:
        if link.segment == "out-of-sample" and not row.oos_revealed_at:
            continue
        runs[link.segment] = run_detail(s, s.get(db.Run, link.run_id))
    return {
        **db.encode(row),
        "runs": runs,
        "oos_status": "REVEALED" if row.oos_revealed_at else "SEALED",
    }


@router.get("/experiments")
def experiments():
    with db.Session() as s:
        return [
            experiment_detail(s, r)
            for r in s.scalars(
                select(db.ExperimentSnapshot).order_by(
                    db.ExperimentSnapshot.created_at.desc()
                )
            )
        ]


@router.get("/experiments/{id}")
def experiment(id: str):
    with db.Session() as s:
        return experiment_detail(s, require(s, db.ExperimentSnapshot, id))


@router.get("/experiments/{id}/combined")
def combined(id: str):
    from backend.app.main import artifact
    from decimal import Decimal as D
    import pandas as pd

    row = experiment(id)
    trades = []
    for run in row["runs"].values():
        if run["status"] == "completed":
            for trade in artifact(run["id"], "trades"):
                # Restore numeric/time types used by the preserved metric implementation.
                for k in (
                    "net_pnl_usd",
                    "gross_pnl_usd",
                    "risk_points",
                    "net_pnl_points",
                    "mfe_points",
                    "mae_points",
                ):
                    if k in trade:
                        trade[k] = D(str(trade[k]))
                for k in ("entry_time_utc", "exit_time_utc"):
                    trade[k] = pd.Timestamp(trade[k])
                trades.append(trade)
    trades.sort(key=lambda t: t["exit_time_utc"])
    return {
        "label": "Combined completed, explicitly revealed segments; not an independent backtest",
        "segments": list(row["runs"]),
        "metrics": metrics.performance(trades),
    }


def sweep_guard(settings, segment, split_id=None, advanced_validation=False):
    if segment == "out-of-sample":
        raise ValueError(
            "Official OOS sweeps are not allowed; create a new research profile for subsequent research"
        )
    if segment == "validation" and not advanced_validation:
        raise ValueError("Validation sweep requires explicit advanced override")
    if segment not in ("development", "validation"):
        raise ValueError(
            "Sweeps use Development by default; Validation requires advanced override"
        )
    with db.Session() as s:
        if split_id:
            split = require(s, db.ResearchSplit, split_id)
            r = split.ranges[segment]
            if settings["start"] < r["start"] or settings["end"] > r["end"]:
                raise ValueError(
                    "Sweep dates must lie inside the selected research segment"
                )
        else:
            # Prevent accidental bypass by dropping a frozen experiment's label.
            for exp in s.scalars(
                select(db.ExperimentSnapshot).where(
                    db.ExperimentSnapshot.frozen_at.is_not(None)
                )
            ):
                r = exp.config["ranges"]["out-of-sample"]
                if settings["start"] < r["end"] and settings["end"] > r["start"]:
                    raise ValueError(
                        "Sweep overlaps frozen OOS; create/select a new research split for further research"
                    )
