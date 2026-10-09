"""Development-only, append-only human annotations. No outcome queries."""

from pathlib import Path
from functools import lru_cache
from datetime import datetime, timezone
import json
import random
import hashlib
import os
from uuid import uuid4
import pandas as pd
from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from backend.app import db
from engine.canonical import clean, digest
from engine.zone_v2.provider import DisplacementBaseZoneProviderV2, ratio

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "work/supply-demand-provider-v2"
router = APIRouter(prefix="/api/zone-labels", tags=["Zone ground truth"])


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


@lru_cache(maxsize=1)
def foundation():
    """Reuse exact engineering bars, without querying reserved source rows."""
    manifest = json.loads((ARTIFACTS / "determinism_manifest.json").read_text())
    if (
        sha(ARTIFACTS / "frozen_provider_config.json")
        != manifest["artifact_hashes"]["frozen_provider_config.json"]
    ):
        raise ValueError("Foundation configuration identity changed")
    config = json.loads((ARTIFACTS / "frozen_provider_config.json").read_text())
    path = ARTIFACTS / "four_hour_bars.parquet"
    if sha(path) != manifest["artifact_hashes"]["four_hour_bars.parquet"]:
        raise ValueError(
            "Four-hour artifact identity changed; rebuild reviewed labeler foundation"
        )
    bars = pd.read_parquet(path)
    start = pd.Timestamp("2020-01-01", tz="America/New_York")
    end = pd.Timestamp("2024-01-01", tz="America/New_York")
    if not ((bars.timestamp >= start) & (bars.availability_timestamp < end)).all():
        raise ValueError("Only Development bars may enter the labeler")
    ident = dict(
        dataset=config["dataset"],
        construction=config["frame"],
        bars_sha256=sha(path),
        source_configuration_sha256=digest(config),
        provider_configuration=config["provider"],
        status="PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH",
    )
    return bars.reset_index(drop=True), ident


def candidates(bars):
    return [
        i
        for i in range(1, len(bars))
        if all(bool(bars.iloc[j].complete and bars.iloc[j].full) for j in (i - 1, i))
        and bars.iloc[i - 1].availability_timestamp == bars.iloc[i].timestamp
    ]


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate: int = Field(ge=0)
    first: int = Field(ge=0)
    last: int = Field(ge=0)
    zone_type: Literal["SUPPLY", "DEMAND"]
    seed: int = 2020


class Label(Selection):
    decision: Literal["VALID_SUPPLY", "VALID_DEMAND", "NOT_A_ZONE"]
    rectangle_approved: bool
    departure_excluded_confirmed: bool
    notes: str = Field(default="", max_length=5000)
    preview_hash: str


def preview(selection, bars, identity):
    a, b, c = selection.first, selection.last, selection.candidate
    if (
        c not in candidates(bars)
        or not max(0, c - 8) <= a <= b < c
        or c - b not in (1, 2)
    ):
        raise ValueError("Select an adjacent base before one or two departure candles")
    seq = bars.iloc[a : c + 1]
    if not (seq.complete & seq.full).all() or any(
        seq.iloc[i].availability_timestamp != seq.iloc[i + 1].timestamp
        for i in range(len(seq) - 1)
    ):
        raise ValueError(
            "Base/departure cannot cross incomplete, shortened or missing bars"
        )
    base = bars.iloc[a : b + 1].to_dict("records")
    deps = bars.iloc[b + 1 : c + 1].to_dict("records")
    supply = selection.zone_type == "SUPPLY"
    top = max(x["high"] if supply else max(x["open"], x["close"]) for x in base)
    bottom = min(min(x["open"], x["close"]) if supply else x["low"] for x in base)
    if top <= bottom:
        raise ValueError("Selected rectangle must have positive width")
    atr = base[-1]["atr14"]
    atr = float(atr) if pd.notna(atr) and atr > 0 else None
    displacement = bottom - deps[-1]["close"] if supply else deps[-1]["close"] - top
    tri = (base + deps)[-3:]
    fvg = (
        (tri[-1]["high"] < tri[0]["low"] if supply else tri[-1]["low"] > tri[0]["high"])
        if len(tri) == 3
        else None
    )
    visible = bars.iloc[max(0, a - 8) : c + 1]
    candles = [
        dict(
            timestamp_utc=x["timestamp"],
            **{k: x[k] for k in ("open", "high", "low", "close")},
        )
        for x in visible.to_dict("records")
        if x["complete"]
    ]
    result = clean(
        dict(
            selection=selection.model_dump(),
            identity=identity,
            base_count=len(base),
            base_timestamps=[x["timestamp"] for x in base],
            top=top,
            bottom=bottom,
            width=top - bottom,
            width_atr=(top - bottom) / atr if atr else None,
            atr14=atr,
            base_body_ratios=[ratio(x) for x in base],
            departure_timestamps=[x["timestamp"] for x in deps],
            departure_body_ratios=[ratio(x) for x in deps],
            departure_displacement=displacement,
            displacement_atr=displacement / atr if atr else None,
            bos=None,
            choch=None,
            fvg=fvg,
            availability=deps[-1]["availability_timestamp"],
            chart=dict(
                bar_seconds=14400,
                right_offset=2,
                candles=candles,
                annotations=[
                    dict(
                        type="box",
                        category="zone",
                        start_time=base[0]["timestamp"],
                        end_time=deps[-1]["availability_timestamp"],
                        price_low=bottom,
                        price_high=top,
                        label="Selected base origin — unavailable until confirmation",
                    ),
                    dict(
                        type="vertical_marker",
                        category="zone",
                        start_time=deps[0]["timestamp"],
                        label="Departure starts — excluded from base",
                    ),
                    dict(
                        type="vertical_marker",
                        category="zone",
                        start_time=deps[-1]["availability_timestamp"],
                        label="Proposed availability",
                    ),
                ],
            ),
            warning="Provisional calendar. Human decision only; no outcome candles shown. BOS/CHoCH unavailable.",
        )
    )
    result["preview_hash"] = digest(result)
    return result


def store():
    p = db.STORE / "zone_ground_truth_v1"
    p.mkdir(parents=True, exist_ok=True)
    return p


def append(kind, value):
    value = clean(value)
    key = digest(value)
    p = store() / f"{kind}_{key}.json"
    temporary = store() / f".{uuid4().hex}.tmp"
    payload = dict(recorded_at=datetime.now(timezone.utc).isoformat(), **value)
    try:
        with temporary.open("x") as f:
            json.dump(payload, f, sort_keys=True, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        try:
            os.link(temporary, p)  # atomic create, never replace an existing record
        except FileExistsError:
            pass
    finally:
        temporary.unlink(missing_ok=True)
    return dict(id=key, **json.loads(p.read_text()))


def records(kind):
    return [
        dict(id=p.stem.split("_", 1)[1], **json.loads(p.read_text()))
        for p in sorted(store().glob(kind + "_*.json"))
    ]


@router.get("/candidate")
def candidate(
    index: int = 0,
    mode: Literal["index", "next", "previous", "random", "jump"] = "index",
    seed: int = 2020,
    jump: str = "",
):
    bars, ident = foundation()
    ids = candidates(bars)
    if mode == "random":
        # Seed is recorded in the eventual immutable selection.
        index = random.Random(seed).choice(ids)
    elif mode == "jump":
        t = pd.Timestamp(jump)
        if t.tz is None:
            t = t.tz_localize(
                "America/New_York", ambiguous="raise", nonexistent="raise"
            )
        if (
            not pd.Timestamp("2020-01-01", tz="America/New_York")
            <= t
            < pd.Timestamp("2024-01-01", tz="America/New_York")
        ):
            raise ValueError("Jump must be within Development")
        matches = [i for i in ids if bars.iloc[i].timestamp >= t]
        if not matches:
            raise ValueError("No remaining Development candidate")
        index = matches[0]
    elif mode == "next":
        index = next((i for i in ids if i > index), ids[-1])
    elif mode == "previous":
        index = next((i for i in reversed(ids) if i < index), ids[0])
    elif index == 0:
        index = ids[0]
    if index not in ids:
        raise ValueError("Invalid Development candidate")
    choices = []
    for i in range(max(0, index - 8), index + 1):
        row = bars.iloc[i]
        choices.append(
            dict(
                index=i,
                time=str(row.timestamp.tz_convert("America/New_York")),
                complete=bool(row.complete),
                full=bool(row.full),
            )
        )
    return dict(
        candidate=index,
        choices=choices,
        seed=seed,
        total=len(ids),
        **preview(
            Selection(
                candidate=index,
                first=index - 1,
                last=index - 1,
                zone_type="SUPPLY",
                seed=seed,
            ),
            bars,
            ident,
        ),
    )


@router.post("/preview")
def get_preview(body: Selection):
    return preview(body, *foundation())


@router.post("/annotations")
def annotate(body: Label):
    value = preview(
        Selection(**body.model_dump(include=set(Selection.model_fields))), *foundation()
    )
    if value["preview_hash"] != body.preview_hash:
        raise ValueError("Preview changed; review rectangle again")
    if not body.departure_excluded_confirmed:
        raise ValueError("Confirm departure excluded from base")
    if body.decision != "NOT_A_ZONE" and (
        body.decision != "VALID_" + body.zone_type or not body.rectangle_approved
    ):
        raise ValueError("Valid label must approve the matching rectangle")
    return append(
        "annotation",
        dict(
            preview=value,
            decision=body.decision,
            notes=body.notes,
            rectangle_approved=body.rectangle_approved,
            departure_excluded_confirmed=True,
        ),
    )


@router.get("/annotations")
def annotations():
    return records("annotation")


@router.post("/freeze")
def freeze():
    labels = records("annotation")
    if not labels:
        raise ValueError("No human annotations to freeze")
    # One reviewed decision per opportunity/type: conflicts require a new explicit review workflow.
    keys = [
        (x["preview"]["base_timestamps"][-1], x["preview"]["selection"]["zone_type"])
        for x in labels
    ]
    if len(keys) != len(set(keys)):
        raise ValueError(
            "Conflicting/repeated opportunity labels; freeze requires one decision per candidate/type"
        )
    return append("snapshot", dict(status="FROZEN_HUMAN_LABELS", annotations=labels))


def compare(labels, predictions):
    counts = dict(
        true_positives=0, false_positives=0, false_negatives=0, true_negatives=0
    )
    rows = []
    for item in labels:
        h = item["preview"]
        side = h["selection"]["zone_type"]
        pred = [
            p
            for p in predictions
            if p["zone_type"] == side
            and pd.Timestamp(p["base_timestamps"][-1])
            == pd.Timestamp(h["base_timestamps"][-1])
            and pd.Timestamp(p["availability_timestamp"])
            <= pd.Timestamp(h["availability"])
        ]
        positive = item["decision"] != "NOT_A_ZONE"
        # Opportunity is side + last base candle, observed through human confirmation.
        # Earlier provider confirmation can match; exact timing is scored separately.
        match = (
            min(
                pred,
                key=lambda p: (
                    p["base_timestamps"]
                    != [pd.Timestamp(t) for t in h["base_timestamps"]],
                    p["zone_id"],
                ),
            )
            if pred
            else None
        )
        outcome = (
            "true_positives"
            if positive and match
            else (
                "false_negatives"
                if positive
                else "false_positives" if pred else "true_negatives"
            )
        )
        counts[outcome] += 1
        rows.append(
            dict(
                label_id=item["id"],
                zone_type=side,
                base_count=h["base_count"],
                outcome=outcome,
                provider_count=len(pred),
                base_agreement=bool(
                    positive
                    and match
                    and [str(pd.Timestamp(t)) for t in match["base_timestamps"]]
                    == [str(pd.Timestamp(t)) for t in h["base_timestamps"]]
                ),
                boundary_agreement=bool(
                    positive
                    and match
                    and match["top"] == h["top"]
                    and match["bottom"] == h["bottom"]
                ),
                availability_agreement=bool(
                    positive
                    and match
                    and pd.Timestamp(match["availability_timestamp"])
                    == pd.Timestamp(h["availability"])
                ),
                availability_difference_minutes=(
                    (
                        pd.Timestamp(match["availability_timestamp"])
                        - pd.Timestamp(h["availability"])
                    ).total_seconds()
                    / 60
                    if match
                    else None
                ),
            )
        )
    tp = counts["true_positives"]
    fp = counts["false_positives"]
    fn = counts["false_negatives"]
    return dict(
        **counts,
        precision=tp / (tp + fp) if tp + fp else None,
        recall=tp / (tp + fn) if tp + fn else None,
        rows=rows,
        base_candle_agreement=(
            sum(r["base_agreement"] for r in rows) / tp if tp else None
        ),
        exact_boundary_agreement=(
            sum(r["boundary_agreement"] for r in rows) / tp if tp else None
        ),
        availability_time_agreement=(
            sum(r["availability_agreement"] for r in rows) / tp if tp else None
        ),
        scope="Reviewed side/last-base-candle opportunities only, observed through human confirmation. Predictions match by last base candle and side; full base, boundaries and availability are scored separately. Later predictions are misses at this cutoff. Unreviewed predictions are not false positives. Not population precision/recall.",
    )


@router.post("/compare/{snapshot_id}")
def comparison(snapshot_id: str):
    if len(snapshot_id) != 64 or any(c not in "0123456789abcdef" for c in snapshot_id):
        raise ValueError("Invalid snapshot")
    snap = json.loads((store() / f"snapshot_{snapshot_id}.json").read_text())
    bars, ident = foundation()
    labels = snap["annotations"]
    if any(x["preview"]["identity"] != clean(ident) for x in labels):
        raise ValueError("Dataset/construction identity mismatch")
    provider = DisplacementBaseZoneProviderV2(
        frame_identity=ident["construction"]["schedule_sha256"]
    )
    last = max(pd.Timestamp(x["preview"]["availability"]) for x in labels)
    for b in bars[bars.availability_timestamp <= last].to_dict("records"):
        provider.update(b)
    report = compare(labels, provider.zones)
    report["by_direction"] = {
        s: compare(
            [x for x in labels if x["preview"]["selection"]["zone_type"] == s],
            provider.zones,
        )
        for s in ("SUPPLY", "DEMAND")
    }
    report["by_base_count"] = {
        str(n): compare(
            [x for x in labels if x["preview"]["base_count"] == n], provider.zones
        )
        for n in sorted({1, 2, 3} | set(x["preview"]["base_count"] for x in labels))
    }
    return append(
        "comparison",
        dict(
            snapshot_id=snapshot_id,
            provider_source_hash=sha(ROOT / "engine/zone_v2/provider.py"),
            report=report,
            status="PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH",
        ),
    )
