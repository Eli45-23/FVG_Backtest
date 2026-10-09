"""Local-only Strategy Research Lab API. Run using run_app.sh."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal
import json, csv, io
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func
import pyarrow.parquet as pq
import pandas as pd
from backend.app import db, services
from backend.app.schemas import (
    StrategyResponse,
    VersionResponse,
    VariantResponse,
    ValidationResponse,
    RunResponse,
    Submitted,
)
from engine.legacy import ROOT, reference
from engine.canonical import clean


@asynccontextmanager
async def lifespan(app):
    services.seed()
    services.seed_managed()
    from backend.app.event_studies import recover_interrupted, cancel_active

    recover_interrupted()
    yield
    cancel_active()
    with db.Session() as s:
        unfinished = [
            r.id
            for r in s.scalars(
                select(db.Run).where(db.Run.status.in_(["queued", "running"]))
            )
        ]
    for rid in unfinished:
        services.cancel(rid)


app = FastAPI(title="Strategy Research Lab", version="1.0", lifespan=lifespan)
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
)


@app.middleware("http")
async def local_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and urlparse(origin).hostname not in ("127.0.0.1", "localhost"):
        return JSONResponse({"detail": "Local origins only"}, status_code=403)
    return await call_next(request)


@app.exception_handler(ValueError)
def value_error(request, e):
    return JSONResponse({"detail": str(e)}, status_code=422)


@app.exception_handler(FileNotFoundError)
def missing(request, e):
    return JSONResponse(
        {"detail": "Local data or artifact is missing. See Data page."}, status_code=409
    )


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StrategyBody(Payload):
    name: str = Field(min_length=1, max_length=160)
    source: str = Field(max_length=100000)
    description: str = ""
    tags: list[str] = []


class ValidateBody(Payload):
    source: str = Field(max_length=100000)
    parameters: dict[str, Any] = {}


class VariantBody(Payload):
    strategy_version_id: str
    name: str
    parameters: dict[str, Any] = {}
    config: dict[str, Any] = {}
    notes: str = ""


class RunSettings(Payload):
    dataset_profile: Literal["legacy_2024_2026", "research_2020_2026"] = (
        "legacy_2024_2026"
    )
    start: str = "2024-01-01"
    end: str = "2026-10-06"
    quantity: int = Field(default=1, ge=1, le=100)
    commission: str = "0"
    slippage: int = Field(default=0, ge=0)
    instrument: Literal["MNQ"] = "MNQ"
    timeframe: Literal["1m", "5m", "15m", "4h"] = "5m"
    execution_mode: Literal["legacy_v1", "extended_v1"] = "legacy_v1"
    session_policy: Literal["XNYS_FULL", "XNYS_ALL"] = "XNYS_FULL"
    max_trades_per_day: int | None = Field(default=1, ge=1)
    sizing_mode: Literal["FIXED_QUANTITY", "FIXED_DOLLAR_RISK"] = "FIXED_QUANTITY"
    risk_budget: str = "100"
    frame_config: dict = Field(
        default_factory=lambda: {
            "anchor": "00:00",
            "timezone": "UTC",
            "session": "extended",
        }
    )
    feature_config: dict = Field(default_factory=dict)


class RunBody(Payload):
    research_split_id: str | None = None
    strategy_version_id: str
    name: str = "Backtest"
    parameters: dict[str, Any] = {}
    settings: RunSettings = Field(default_factory=RunSettings)
    notes: str = ""
    variant_id: str | None = None
    segment: str = Field(
        default="development",
        pattern="^(development|validation|out-of-sample|full-sample|ad-hoc)$",
    )


class CompareBody(Payload):
    ids: list[str] = Field(min_length=1, max_length=12)


class SweepBody(Payload):
    advanced_validation: bool = False
    run: RunBody
    parameter: str
    values: list[Any] = Field(min_length=1, max_length=20)
    name: str = "Single-parameter sweep"


def get(s, model, id):
    row = s.get(model, id)
    if not row:
        raise HTTPException(404, "Not found")
    return row


def strategy_detail(s, row):
    v = s.scalar(
        select(db.Version).where(
            db.Version.strategy_id == row.id, db.Version.number == row.current_version
        )
    )
    return {
        **db.encode(row),
        "version_id": v.id,
        "source": v.source,
        "source_hash": v.source_hash,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "local_only": True}


@app.get("/api/template")
def template():
    return {"source": (ROOT / "strategies/builtins/template.py").read_text()}


@app.post("/api/strategies/validate", response_model=ValidationResponse)
def validation(body: ValidateBody):
    return services.validate(body.source, body.parameters)


@app.get("/api/strategies", response_model=list[StrategyResponse])
def strategies():
    with db.Session() as s:
        return [
            strategy_detail(s, r)
            for r in s.scalars(
                select(db.Strategy)
                .where(db.Strategy.archived == False)
                .order_by(db.Strategy.updated_at.desc())
            )
        ]


@app.post("/api/strategies", response_model=StrategyResponse)
def create_strategy(body: StrategyBody):
    with db.Session.begin() as s:
        row = db.Strategy(name=body.name, description=body.description, tags=body.tags)
        s.add(row)
        s.flush()
        services.version(s, row, body.source)
        return strategy_detail(s, row)


@app.get("/api/strategies/{id}", response_model=StrategyResponse)
def strategy(id: str):
    with db.Session() as s:
        return strategy_detail(s, get(s, db.Strategy, id))


@app.put("/api/strategies/{id}", response_model=StrategyResponse)
def save_strategy(id: str, body: StrategyBody):
    with db.Session.begin() as s:
        row = get(s, db.Strategy, id)
        row.name = body.name
        row.description = body.description
        row.tags = body.tags
        services.version(s, row, body.source)
        return strategy_detail(s, row)


@app.delete("/api/strategies/{id}")
def archive_strategy(id: str):
    with db.Session.begin() as s:
        get(s, db.Strategy, id).archived = True
    return {"archived": True}


@app.get("/api/strategies/{id}/versions", response_model=list[VersionResponse])
def versions(id: str):
    with db.Session() as s:
        return [
            {
                **db.encode(v),
                "run_count": s.scalar(
                    select(func.count())
                    .select_from(db.Run)
                    .where(db.Run.strategy_version_id == v.id)
                ),
                "variant_count": s.scalar(
                    select(func.count())
                    .select_from(db.Variant)
                    .where(db.Variant.strategy_version_id == v.id)
                ),
            }
            for v in s.scalars(
                select(db.Version)
                .where(db.Version.strategy_id == id)
                .order_by(db.Version.number.desc())
            )
        ]


@app.get("/api/variants", response_model=list[VariantResponse])
def variants():
    with db.Session() as s:
        return [db.encode(v) for v in s.scalars(select(db.Variant))]


@app.post("/api/variants", response_model=VariantResponse)
def variant(body: VariantBody):
    with db.Session.begin() as s:
        v = get(s, db.Version, body.strategy_version_id)
        check = services.validate(v.source, body.parameters)
        if not check["valid"]:
            raise ValueError(check.get("error", "Invalid inputs"))
        row = db.Variant(**body.model_dump())
        s.add(row)
        s.flush()
        return db.encode(row)


@app.post("/api/backtests", response_model=Submitted)
def submit(body: RunBody):
    if body.segment == "out-of-sample":
        raise ValueError(
            "Official OOS requires a frozen experiment and explicit RUN / REVEAL OOS"
        )
    if body.research_split_id:
        from backend.app.experiments import require

        with db.Session() as s:
            split = require(s, db.ResearchSplit, body.research_split_id)
            r = split.ranges.get(body.segment)
            if (
                not r
                or body.settings.start < r["start"]
                or body.settings.end > r["end"]
            ):
                raise ValueError("Run dates must lie inside selected research segment")
    return {
        "id": services.enqueue(
            body.strategy_version_id,
            body.parameters,
            body.settings.model_dump(),
            body.name,
            body.notes,
            body.variant_id,
            body.segment,
            extra_config={"research_split_id": body.research_split_id},
        )
    }


def run_detail(s, row):
    metric = s.get(db.RunMetric, row.id)
    p = db.STORE / "artifacts" / row.id / "progress.txt"
    return {
        **db.encode(row),
        "run_type": row.config.get(
            "run_type", row.config.get("segment", "ad-hoc").upper().replace("-", "_")
        ),
        "experiment_snapshot_id": row.config.get("experiment_snapshot_id"),
        "metrics": metric.payload if metric else None,
        "progress": (
            p.read_text() if row.status == "running" and p.exists() else row.progress
        ),
    }


@app.get("/api/backtests", response_model=list[RunResponse])
def runs():
    with db.Session() as s:
        return [
            run_detail(s, r)
            for r in s.scalars(select(db.Run).order_by(db.Run.created_at.desc()))
        ]


@app.get("/api/backtests/{id}", response_model=RunResponse)
def run(id: str):
    with db.Session() as s:
        return run_detail(s, get(s, db.Run, id))


@app.post("/api/backtests/{id}/cancel")
def cancel(id: str):
    return {"status": services.cancel(id)}


@app.post("/api/backtests/{id}/clone")
def clone_run(id: str):
    with db.Session() as s:
        row = get(s, db.Run, id)
        c = row.config
        return {
            "id": services.enqueue(
                row.strategy_version_id,
                c["parameters"],
                c["settings"],
                row.name + " copy",
                row.notes,
                row.variant_id,
                (
                    "ad-hoc"
                    if c.get("experiment_snapshot_id")
                    else c.get("segment", "development")
                ),
            )
        }


def artifact(id, kind):
    with db.Session() as s:
        row = get(s, db.Run, id)
        if row.status != "completed":
            raise HTTPException(409, "Run is not complete")
        ref = s.scalar(
            select(db.Artifact).where(
                db.Artifact.run_id == id, db.Artifact.kind == kind
            )
        )
        if not ref:
            raise HTTPException(404, "Artifact not available")
        return json.loads(Path(ref.path).read_text())


@app.get("/api/backtests/{id}/metrics")
def run_metrics(id: str):
    return run(id)["metrics"]


@app.get("/api/backtests/{id}/equity")
def equity(id: str):
    return artifact(id, "equity")


@app.get("/api/backtests/{id}/trades")
def trades(
    id: str,
    direction: str | None = None,
    outcome: str | None = None,
    start: str | None = None,
    end: str | None = None,
    year: int | None = None,
    month: int | None = None,
    weekday: str | None = None,
    time_from: str | None = None,
    time_to: str | None = None,
    risk_min: float | None = None,
    risk_max: float | None = None,
    exit_reason: str | None = None,
):
    rows = artifact(id, "trades")

    def keep(t):
        local = t["entry_time_ny"]
        day = local[:10]
        clock = local[11:16]
        pnl = float(t["net_pnl_usd"])
        return (
            (not direction or t["direction"] == direction)
            and (
                not outcome
                or (
                    pnl > 0
                    if outcome == "winner"
                    else pnl < 0 if outcome == "loser" else pnl == 0
                )
            )
            and (not start or day >= start)
            and (not end or day < end)
            and (year is None or t["year"] == year)
            and (month is None or t["month"] == month)
            and (not weekday or t["weekday"] == weekday)
            and (not time_from or clock >= time_from)
            and (not time_to or clock < time_to)
            and (risk_min is None or float(t["risk_points"]) >= risk_min)
            and (risk_max is None or float(t["risk_points"]) < risk_max)
            and (not exit_reason or t["exit_reason"] == exit_reason)
        )

    return [r for r in rows if keep(r)]


@app.get("/api/backtests/{id}/export.csv")
def export(id: str):
    rows = artifact(id, "trades")
    out = io.StringIO()
    if rows:
        w = csv.DictWriter(out, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return Response(
        out.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="trades.csv"'},
    )


@app.get("/api/backtests/{id}/candles/{trade_id}")
def candles(id: str, trade_id: str):
    payload = trade_chart(id, trade_id)
    return {**payload, "bars": payload["candles"]}


@app.get("/api/backtests/{id}/trades/{trade_id}/chart")
def trade_chart(id: str, trade_id: str, window: Literal["30", "60", "session"] = "30"):
    from backend.app.charts import chart_payload

    rows = artifact(id, "trades")
    if not any(t["trade_id"] == trade_id for t in rows):
        raise HTTPException(404, "Trade not found")
    result = artifact(id, "result")
    payload = chart_payload(
        rows,
        trade_id,
        window,
        result.get("management_events", []),
        run(id)["config"].get("dataset_profile", "legacy_2024_2026"),
    )
    with db.Session() as s:
        r = get(s, db.Run, id)
        v = get(s, db.Version, r.strategy_version_id)
        st = get(s, db.Strategy, v.strategy_id)
        variant = s.get(db.Variant, r.variant_id) if r.variant_id else None
        payload["run"] = {
            "name": r.name,
            "strategy_name": st.name,
            "variant": variant.name if variant else None,
        }
    return payload


@app.post("/api/compare")
def compare(body: CompareBody):
    selected = [run(id) for id in body.ids]
    if any(r["status"] != "completed" for r in selected):
        raise ValueError("Compare completed runs only")
    warnings = []
    for key in [
        "settings",
        "data_hashes",
        "engine_version",
        "segment",
        "research_split_id",
        "management",
        "source_hash",
    ]:
        if (
            len({json.dumps(r["config"].get(key), sort_keys=True) for r in selected})
            > 1
        ):
            warnings.append(
                f"Runs differ in {key}; inspect configurations before interpreting results."
            )
    return {
        "runs": selected,
        "equity": {r["id"]: equity(r["id"]) for r in selected},
        "warnings": warnings,
        "configurations": {r["id"]: r["config"] for r in selected},
    }


@app.post("/api/sweeps")
def sweep(body: SweepBody):
    from backend.app.experiments import sweep_guard

    sweep_guard(
        body.run.settings.model_dump(),
        body.run.segment,
        body.run.research_split_id,
        body.advanced_validation,
    )
    with db.Session() as s:
        v = get(s, db.Version, body.run.strategy_version_id)
        source = v.source
    check = services.validate(source, body.run.parameters)
    meta = next((x for x in check.get("inputs", []) if x["id"] == body.parameter), None)
    if not meta or meta["type"] not in ("float", "int", "choice"):
        raise ValueError("Sweep a numeric or choice input")
    # Validate every value before scheduling any child.
    for value in body.values:
        check = services.validate(
            source, {**body.run.parameters, body.parameter: value}
        )
        if not check["valid"]:
            raise ValueError(check.get("error", "Invalid sweep value"))
    with db.Session.begin() as s:
        row = db.Sweep(name=body.name, definition=body.model_dump())
        s.add(row)
        s.flush()
        sid = row.id
    for value in body.values:
        rid = services.enqueue(
            body.run.strategy_version_id,
            {**body.run.parameters, body.parameter: value},
            body.run.settings.model_dump(),
            f"{body.name}: {value}",
            body.run.notes,
            body.run.variant_id,
            body.run.segment,
            extra_config={
                "research_split_id": body.run.research_split_id,
                "validation_sweep_override": body.advanced_validation,
            },
        )
        with db.Session.begin() as s:
            s.add(db.SweepRun(sweep_id=sid, run_id=rid, value=value))
    return {"id": sid}


@app.get("/api/sweeps")
def sweeps():
    with db.Session() as s:
        return [
            {
                **db.encode(x),
                "children": [
                    {"value": c.value, **run_detail(s, get(s, db.Run, c.run_id))}
                    for c in s.scalars(
                        select(db.SweepRun).where(db.SweepRun.sweep_id == x.id)
                    )
                ],
            }
            for x in s.scalars(select(db.Sweep).order_by(db.Sweep.created_at.desc()))
        ]


@app.get("/api/data")
def data():
    result = []
    for kind, p in reference.INPUTS.items():
        if not p.exists():
            result.append({"kind": kind, "status": "missing"})
            continue
        table = pq.read_table(p)
        ts = next(
            k
            for k in ["ts_event", "timestamp_utc", "formation_bar_start_utc"]
            if k in table.column_names
        )
        col = table[ts].to_pandas()
        result.append(
            {
                "kind": kind,
                "rows": table.num_rows,
                "first": col.min().isoformat(),
                "last": col.max().isoformat(),
                "status": "available",
                "validation": "Preserved validated source; hash checked per run",
                "file": p.name,
            }
        )
    return {
        "datasets": result,
        "start": "2024-01-01",
        "end": "2026-10-06",
        "date_semantics": "NY calendar dates, end exclusive; final raw coverage ends 2026-10-06 00:00 UTC",
        "downloads_on_startup": False,
    }


@app.get("/api/research/fvgs")
def research(
    direction: str | None = None,
    start: str | None = None,
    end: str | None = None,
    touched: bool | None = None,
    fully_filled: bool | None = None,
    close_invalidated: bool | None = None,
    wick_invalidated: bool | None = None,
    opening_exception: bool | None = None,
    size_min: float | None = None,
    size_max: float | None = None,
    time_from: str | None = None,
    time_to: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    f = pq.read_table(reference.INPUTS["lifecycle"]).to_pandas()
    for col, value in [
        ("direction", direction),
        ("touched", touched),
        ("fully_filled", fully_filled),
        ("close_invalidated", close_invalidated),
        ("wick_invalidated", wick_invalidated),
        ("opening_exception", opening_exception),
    ]:
        if value is not None:
            f = f[f[col] == value]
    dates = f.formation_bar_start_ny.dt.strftime("%Y-%m-%d")
    times = f.formation_bar_start_ny.dt.strftime("%H:%M")
    mask = pd.Series(True, index=f.index)
    if start:
        mask &= dates >= start
    if end:
        mask &= dates < end
    if time_from:
        mask &= times >= time_from
    if time_to:
        mask &= times < time_to
    if size_min is not None:
        mask &= f.size_points.astype(float) >= size_min
    if size_max is not None:
        mask &= f.size_points.astype(float) < size_max
    f = f[mask]
    clean_rows = f[f.research_day_eligible]
    n = len(clean_rows)
    stats = {
        "count": len(f),
        "qualified_count": n,
        "touch_rate": 100 * clean_rows.touched.mean() if n else None,
        "fill_rate": 100 * clean_rows.fully_filled.mean() if n else None,
        "median_bars_to_touch": (
            clean_rows.loc[clean_rows.touched, "bars_until_first_touch"].median()
            if n
            else None
        ),
        "average_excursion": (
            clean_rows.maximum_points_away_before_touch.astype(float).mean()
            if n
            else None
        ),
        "median_excursion": (
            clean_rows.maximum_points_away_before_touch.astype(float).median()
            if n
            else None
        ),
    }
    columns = [
        "fvg_id",
        "direction",
        "formation_bar_start_ny",
        "size_points",
        "opening_exception",
        "touched",
        "fully_filled",
        "close_invalidated",
        "wick_invalidated",
        "research_day_eligible",
    ]
    return clean(
        {
            "stats": stats,
            "rows": f.iloc[offset : offset + limit][columns].to_dict("records"),
            "denominator": "Rates use qualified complete same-day histories only; descriptive hindsight, never strategy context.",
        }
    )


@app.get("/api/backtests/{id}/logs")
def logs(id: str):
    with db.Session() as s:
        get(s, db.Run, id)
    p = db.STORE / "artifacts" / id / "worker.log"
    return {
        "text": p.read_text(errors="replace")[-16000:] if p.exists() else "",
        "notice": "Trusted strategy stdout/stderr; local only.",
    }


@app.get("/api/backtests/{id}/management-events")
def management_events(id: str):
    return artifact(id, "result").get("management_events", [])


from backend.app.versions import router as versions_router

app.include_router(versions_router)

from backend.app.experiments import router as experiments_router

app.include_router(experiments_router)

from backend.app.event_studies import router as event_studies_router

app.include_router(event_studies_router)

# Additive annotation artifacts, separate from studies and production database.
from backend.app.zone_labels import router as zone_labels_router
app.include_router(zone_labels_router)
