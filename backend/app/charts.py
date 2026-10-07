"""Windowed read-only chart data. Annotation rendering is strategy-agnostic."""

from datetime import datetime
from typing import Literal, Any
from pydantic import BaseModel, ConfigDict
import pandas as pd
import pyarrow.parquet as pq
from engine.legacy import reference
from engine.canonical import clean


class Annotation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["box", "horizontal_line", "vertical_marker", "point_marker", "label"]
    start_time: datetime
    end_time: datetime | None = None
    price: float | None = None
    price_low: float | None = None
    price_high: float | None = None
    label: str = ""
    category: str = "strategy"
    metadata: dict[str, Any] = {}


def chart_payload(rows, trade_id, window="30", events=()):
    index = next((i for i, t in enumerate(rows) if t["trade_id"] == trade_id), None)
    if index is None:
        raise ValueError("Invalid trade ID")
    t = rows[index]
    entry = pd.Timestamp(t["entry_time_utc"])
    exit = pd.Timestamp(t["exit_time_utc"])
    day = entry.tz_convert("America/New_York").normalize()
    start = day.tz_convert("UTC")
    end = (day + pd.DateOffset(days=1)).tz_convert("UTC")
    if window not in ("30", "60", "session"):
        raise ValueError("Invalid chart window")
    a = (
        start
        if window == "session"
        else max(start, entry - pd.Timedelta(minutes=int(window)))
    )
    b = end if window == "session" else min(end, exit + pd.Timedelta(minutes=15))
    bars = pq.read_table(
        reference.INPUTS["bars"],
        filters=[("timestamp_utc", ">=", a), ("timestamp_utc", "<", b)],
    ).to_pandas()
    bars = bars.sort_values("timestamp_utc")
    if bars.empty:
        raise ValueError("No chart candles available for this window")
    annotations = []

    def add(**kw):
        annotations.append(Annotation(**kw).model_dump(mode="json"))

    for field, label, category in [
        ("entry_price", "Entry", "entry"),
        ("stop_price", "Original stop", "stop"),
        ("target_price", "Original target", "target"),
    ]:
        add(
            type="horizontal_line",
            start_time=entry,
            end_time=exit,
            price=float(t[field]),
            label=label,
            category=category,
        )
    add(
        type="point_marker",
        start_time=entry,
        price=float(t["entry_price"]),
        label=t["direction"] + " entry",
        category="entry",
    )
    add(
        type="point_marker",
        start_time=exit,
        price=float(t["exit_price"]),
        label=t["exit_reason"] + " exit",
        category="exit",
    )
    if float(t.get("fvg_top", 0)) > float(t.get("fvg_bottom", 0)):
        add(
            type="box",
            start_time=t["formation_time_utc"],
            end_time=exit,
            price_low=float(t["fvg_bottom"]),
            price_high=float(t["fvg_top"]),
            label="FVG",
            category="fvg",
        )
    for annotation in t.get("metadata", {}).get("annotations", []):
        add(**annotation)
    selected = [e for e in events if e["trade_id"] == trade_id]
    for i, e in enumerate(selected):
        add(
            type="horizontal_line",
            start_time=e["activation_timestamp"],
            end_time=(
                selected[i + 1]["activation_timestamp"]
                if i + 1 < len(selected)
                else exit
            ),
            price=float(e["effective_stop"]),
            label=e["reason"],
            category="management",
            metadata={"event_id": e["event_id"]},
        )
    return clean(
        {
            "trade": t,
            "candles": bars.to_dict("records"),
            "annotations": annotations,
            "management_events": selected,
            "session_bounds": {
                "start": start,
                "end": end,
                "definition": "New York calendar date; full available futures data",
            },
            "data_range": {
                "start": bars.timestamp_utc.min(),
                "end": bars.timestamp_utc.max(),
            },
            "previous_trade_id": rows[index - 1]["trade_id"] if index else None,
            "next_trade_id": (
                rows[index + 1]["trade_id"] if index + 1 < len(rows) else None
            ),
            "trade_number": index + 1,
            "trade_count": len(rows),
        }
    )
