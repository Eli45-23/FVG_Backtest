"""Additive accepted-calendar collection; legacy labels are never touched."""

from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json, os
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from backend.app import db
from engine.canonical import clean, digest
from engine.zone_ground_truth import collection as c
from engine.zone_v2.provider import ratio

router = APIRouter(
    prefix="/api/zone-ground-truth-v2", tags=["Accepted calendar ground truth"]
)


@lru_cache(maxsize=1)
def foundation():
    bars, ident, zones = c.load()
    bundle = json.loads((c.OUT / "collection.json").read_text())
    if bundle["protocol"]["identity"] != ident:
        raise ValueError("Collection foundation changed")
    p = dict(bundle["protocol"])
    h = p.pop("protocol_sha256")
    if digest(p) != h:
        raise ValueError("Protocol hash mismatch")
    return bars, ident, zones, bundle


def store():
    p = db.STORE / "zone_ground_truth_v2_calendar_accepted"
    p.mkdir(parents=True, exist_ok=True)
    return p


def records():
    return [
        json.loads(p.read_text()) for p in sorted(store().glob("annotation_*.json"))
    ]


def latest():
    rows = records()
    superseded = {r["supersedes"] for r in rows if r.get("supersedes")}
    return [r for r in rows if r["annotation_id"] not in superseded]


def completed():
    return {r["sample_id"] for r in latest() if r["window_complete"]}


def find(sample_id):
    bars, ident, zones, bundle = foundation()
    for kind in ["blind", "near_miss", "review"]:
        for x in bundle[kind]:
            if x["sample_id"] == sample_id:
                return x
    raise ValueError("Unknown frozen sample")


def blind_done():
    b = foundation()[3]
    return {x["sample_id"] for k in ["blind", "near_miss"] for x in b[k]} <= completed()


def public_identity(ident, review=False):
    return {k: v for k, v in ident.items() if review or not k.startswith("provider")}


@router.get("/collection")
def collection():
    _, ident, _, b = foundation()
    return dict(
        identity=public_identity(ident),
        protocol_sha256=b["protocol"]["protocol_sha256"],
        acceptance=b["protocol"]["acceptance"],
        minimum=b["protocol"]["minimum"],
        matching=b["protocol"]["matching"],
        samples=[
            {
                k: v
                for k, v in x.items()
                if k in ("sample_id", "kind", "year", "ny_date", "confirmation")
            }
            for kind in (
                ["blind", "near_miss", "review"]
                if blind_done()
                else ["blind", "near_miss"]
            )
            for x in b[kind]
        ],
        completed=sorted(completed()),
        provider_review_unlocked=blind_done(),
    )


def view(sample_id):
    bars, ident, _, bundle = foundation()
    s = find(sample_id)
    review = s["kind"] == "PROVIDER_REVIEW"
    if review and not blind_done():
        raise ValueError(
            "Complete blind and near-miss windows before viewing provider proposals"
        )
    if review:
        exposure = store() / "provider_review_exposed.json"
        try:
            with exposure.open("x") as f:
                json.dump(
                    dict(
                        recorded_at=datetime.now(timezone.utc).isoformat(),
                        sample_id=sample_id,
                    ),
                    f,
                )
        except FileExistsError:
            pass
    end = s["candidate"]
    visible = bars.iloc[max(0, end - 14) : end + 1]
    visible = visible[
        visible.complete & visible.full & visible.schedule_resolved.astype(bool)
    ]
    candles = [
        dict(
            timestamp_utc=r.timestamp,
            open=r.open,
            high=r.high,
            low=r.low,
            close=r.close,
        )
        for r in visible.itertuples()
    ]
    choices = [
        dict(
            index=i,
            bar_id=r.bar_id,
            time=str(r.timestamp.tz_convert("America/New_York")),
        )
        for i, r in visible.iterrows()
        if i < end
    ]
    annotations = []
    proposal = s.get("proposal") if review else None
    if proposal:
        annotations = [
            dict(
                type="box",
                category="zone",
                start_time=proposal["base_timestamps"][0],
                end_time=proposal["availability_timestamp"],
                price_low=proposal["bottom"],
                price_high=proposal["top"],
                label="Provider proposal — provisional",
            )
        ]
    return clean(
        dict(
            sample_id=sample_id,
            kind=s["kind"],
            confirmation=s["confirmation"],
            candidate=end,
            choices=choices,
            identity=public_identity(ident, review),
            proposal=proposal,
            chart=dict(
                candles=candles,
                annotations=annotations,
                bar_seconds=14400,
                right_offset=1,
            ),
            annotations_saved=[
                dict(
                    annotation_id=r["annotation_id"],
                    label=r["label"],
                    window_complete=r["window_complete"],
                )
                for r in latest()
                if r["sample_id"] == sample_id
            ],
        )
    )


@router.get("/window/{sample_id}")
def window(sample_id: str):
    return view(sample_id)


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sample_id: str
    first: int
    last: int
    side: Literal["SUPPLY", "DEMAND"]


def calculate(s):
    bars, ident, _, _ = foundation()
    item = find(s.sample_id)
    view(s.sample_id)
    end = item["candidate"]
    if (
        not max(0, end - 14) <= s.first <= s.last < end
        or end - s.last not in (1, 2, 3)
        or not c.consecutive(bars, s.first, end)
    ):
        raise ValueError(
            "Select accepted adjacent base candles, excluding 1–3 departure candles"
        )
    base = bars.iloc[s.first : s.last + 1]
    dep = bars.iloc[s.last + 1 : end + 1]
    top = float(
        base.high.max() if s.side == "SUPPLY" else base[["open", "close"]].max().max()
    )
    bottom = float(
        base[["open", "close"]].min().min() if s.side == "SUPPLY" else base.low.min()
    )
    if top <= bottom:
        raise ValueError("Positive rectangle width required")
    human = clean(
        dict(
            side=s.side,
            base_ids=list(base.bar_id),
            base_timestamps=list(base.timestamp),
            first=s.first,
            last=s.last,
            top=top,
            bottom=bottom,
            proximal=bottom if s.side == "SUPPLY" else top,
            distal=top if s.side == "SUPPLY" else bottom,
            width=top - bottom,
            availability=item["confirmation"],
            base_count=len(base),
            base_body_ratios=[ratio(r) for r in base.to_dict("records")],
            departure_timestamps=list(dep.timestamp),
            departure_body_ratios=[ratio(r) for r in dep.to_dict("records")],
        )
    )
    human["preview_hash"] = digest([s.sample_id, human, ident])
    return human


@router.post("/preview")
def preview(body: Selection):
    return calculate(body)


class Annotation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sample_id: str
    label: Literal[
        "VALID_SUPPLY",
        "VALID_DEMAND",
        "NOT_A_ZONE",
        "ACCEPT_EXACT",
        "ACCEPT_ZONE_WRONG_BASE",
        "ACCEPT_ZONE_WRONG_BOUNDARIES",
        "REJECT_NOT_A_ZONE",
    ]
    selection: Selection | None = None
    preview_hash: str | None = None
    rectangle_approved: bool = False
    departure_excluded: bool = False
    window_complete: bool = True
    notes: str = Field(default="", max_length=5000)
    supersedes: str | None = None


def _annotate(body: Annotation):
    _, ident, _, bundle = foundation()
    s = find(body.sample_id)
    view(body.sample_id)
    review = s["kind"] == "PROVIDER_REVIEW"
    if review != body.label.startswith(("ACCEPT_", "REJECT_")):
        raise ValueError("Decision incompatible with mode")
    if not review and (store() / "provider_review_exposed.json").exists():
        raise ValueError(
            "Blind collection frozen after provider exposure; new independent collection required"
        )
    current = latest()
    prior = None
    if body.supersedes:
        prior = next(
            (
                r
                for r in current
                if r["annotation_id"] == body.supersedes
                and r["sample_id"] == body.sample_id
            ),
            None,
        )
        if not prior:
            raise ValueError(
                "Correction must reference a current annotation of this window"
            )
    elif body.sample_id in completed():
        raise ValueError("Window completed; use a correction version")
    positive = body.label not in ("NOT_A_ZONE", "REJECT_NOT_A_ZONE")
    human = None
    if positive:
        if not body.selection or body.selection.sample_id != body.sample_id:
            raise ValueError("Human base selection required")
        human = calculate(body.selection)
        if (
            human["preview_hash"] != body.preview_hash
            or not body.rectangle_approved
            or not body.departure_excluded
        ):
            raise ValueError("Approve fresh rectangle and departure exclusion")
        if not review and body.label != "VALID_" + human["side"]:
            raise ValueError("Decision/side mismatch")
        if review:
            z = s["proposal"]
            if human["side"] != z["zone_type"]:
                raise ValueError("Proposal direction must match accepted concept")
            exact = (
                list(map(str, pd.to_datetime(human["base_timestamps"])))
                == list(map(str, pd.to_datetime(z["base_timestamps"])))
                and human["top"] == z["top"]
                and human["bottom"] == z["bottom"]
            )
            if (body.label == "ACCEPT_EXACT") != exact:
                raise ValueError(
                    "Use the decision matching actual base/boundary agreement"
                )
    others = [
        r
        for r in current
        if r["sample_id"] == body.sample_id and r["annotation_id"] != body.supersedes
    ]
    if not positive and any(r["human"] for r in others):
        raise ValueError("Cannot mark no zone after recording zones")
    if positive and any(not r["human"] for r in others):
        raise ValueError("Correct the NOT_A_ZONE record before adding a zone")
    if positive and any(
        r["human"]
        and r["human"]["base_ids"] == human["base_ids"]
        and r["human"]["side"] == human["side"]
        for r in others
    ):
        raise ValueError("Duplicate human zone")
    if review and others:
        raise ValueError("One review per proposal; correct the existing record")
    value = clean(
        dict(
            annotation_id=uuid4().hex,
            mode="PROVIDER_REVIEW" if review else "BLIND",
            sample_kind=s["kind"],
            sample_id=body.sample_id,
            ny_date=s["ny_date"],
            confirmation=s["confirmation"],
            identity=ident,
            protocol_sha256=bundle["protocol"]["protocol_sha256"],
            unresolved_date_excluded=True,
            chart_bar_timestamps=[
                x["timestamp_utc"] for x in view(body.sample_id)["chart"]["candles"]
            ],
            rectangle_approved=body.rectangle_approved,
            departure_excluded=body.departure_excluded,
            label=body.label,
            human=human,
            provider=s.get("proposal") if review else None,
            disagreement_reason=body.label if review else None,
            notes=body.notes,
            window_complete=body.window_complete,
            supersedes=body.supersedes,
            version=prior["version"] + 1 if prior else 1,
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    # Exclusive creation plus per-parent correction claim prevents competing branches.
    claim = None
    if prior:
        claim = store() / ("correction_" + prior["annotation_id"])
        fd = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    path = store() / ("annotation_" + value["annotation_id"] + ".json")
    try:
        with path.open("x") as f:
            json.dump(value, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        if claim:
            claim.unlink(missing_ok=True)
        raise
    return dict(annotation_id=value["annotation_id"], version=value["version"])


@router.get("/annotations")
def annotations():
    # Full identity/provider snapshots are exportable only after blind collection.
    return [
        (
            {k: v for k, v in r.items() if k not in ("identity", "provider")}
            | {"identity": public_identity(r["identity"], blind_done())}
        )
        for r in records()
    ]


@router.post("/complete/{sample_id}")
def complete_window(sample_id: str):
    rows = [r for r in latest() if r["sample_id"] == sample_id]
    if not rows:
        raise ValueError("Record at least one zone or explicit NOT_A_ZONE first")
    r = sorted(rows, key=lambda r: r["recorded_at"])[-1]
    h = r["human"]
    return annotate(
        Annotation(
            sample_id=sample_id,
            label=r["label"],
            selection=(
                Selection(
                    sample_id=sample_id,
                    first=h["first"],
                    last=h["last"],
                    side=h["side"],
                )
                if h
                else None
            ),
            preview_hash=h["preview_hash"] if h else None,
            rectangle_approved=True,
            departure_excluded=True,
            window_complete=True,
            notes=r["notes"],
            supersedes=r["annotation_id"],
        )
    )


@router.get("/comparison")
def comparison():
    from engine.zone_ground_truth.comparison import measure

    _, _, zones, b = foundation()
    return clean(measure(b, latest(), zones))


@router.post("/export")
def export():
    # Export a new immutable snapshot; the original collection never gets overwritten.
    value = clean(
        dict(
            annotations=records(),
            comparison=comparison(),
            protocol=foundation()[3]["protocol"],
        )
    )
    if not blind_done():
        value["protocol"] = {
            k: v for k, v in value["protocol"].items() if k != "identity"
        }
        value["annotations"] = annotations()
    key = digest(value)
    path = store() / ("snapshot_" + key + ".json")
    if not path.exists():
        with path.open("x") as f:
            json.dump(value, f, indent=2, sort_keys=True)
    return dict(snapshot_id=key, **value)


@router.post("/annotations")
def annotate(body: Annotation):
    import fcntl

    with (store() / ".append.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _annotate(body)
