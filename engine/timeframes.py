"""Explicit clock/session anchored complete bars, never synthetic intervals."""

from dataclasses import dataclass
from decimal import Decimal as D
import pandas as pd
from engine.research.levels import schedule, NY

MINUTES = {"1m": 1, "5m": 5, "15m": 15, "4h": 240}


@dataclass(frozen=True)
class FrameConfig:
    anchor: str = "00:00"
    timezone: str = "UTC"
    session: str = "extended"

    def validate(self):
        from datetime import time

        time.fromisoformat(self.anchor)
        if self.timezone not in ("UTC", NY) or self.session not in ("extended", "rth"):
            raise ValueError("Explicit UTC/NY and extended/rth frame profile required")
        if self.session == "rth" and (self.anchor != "09:30" or self.timezone != NY):
            raise ValueError("RTH preset requires America/New_York 09:30 anchor")


def aggregate(raw, timeframe, config=FrameConfig()):
    config.validate()
    if timeframe not in MINUTES:
        raise ValueError("Unsupported timeframe")
    m = raw.reset_index() if "ts_event" not in raw else raw.copy()
    m = m.sort_values("ts_event")
    if m.ts_event.duplicated().any():
        raise ValueError("Duplicate source minute")
    if not m.ts_event.eq(m.ts_event.dt.floor("min")).all():
        raise ValueError("Off-clock minute")
    duration = MINUTES[timeframe]
    local = m.ts_event.dt.tz_convert(config.timezone)
    hh, mm = map(int, config.anchor.split(":"))
    wall = local.dt.tz_localize(None)
    anchors = wall.dt.normalize() + pd.Timedelta(hours=hh, minutes=mm)
    anchors = anchors.where(wall >= anchors, anchors - pd.Timedelta(days=1))
    # Localize the wall clock anchor, not an elapsed offset from midnight on DST days.
    # Ambiguous/nonexistent anchors fail explicitly; they are never silently shifted.
    anchors = anchors.dt.tz_localize(
        config.timezone, ambiguous="raise", nonexistent="raise"
    )
    start = anchors + (local - anchors).dt.floor(f"{duration}min")
    m["_bucket"] = start.dt.tz_convert("UTC")
    if config.session == "rth":
        sessions = schedule()
        ny = m.ts_event.dt.tz_convert(NY)
        mask = [
            str(t.date()) in sessions
            and sessions[str(t.date())][0] <= t < sessions[str(t.date())][1]
            for t in ny
        ]
        m = m.loc[mask]
    grouped = m.groupby("_bucket", sort=True)
    b = grouped.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        minute_count=("ts_event", "size"),
        first=("ts_event", "min"),
        last=("ts_event", "max"),
    )
    b["is_complete_5m"] = (
        (b.minute_count == duration)
        & (b["first"] == b.index)
        & (b["last"] == b.index + pd.Timedelta(minutes=duration - 1))
    )
    b["timestamp_utc"] = b.index
    b["timestamp_ny"] = b.index.tz_convert(NY)
    for k in ["open", "high", "low", "close"]:
        b[k] = b[k].map(lambda x: D(int(x)).scaleb(-9))
    b["availability_timestamp"] = b.index + pd.Timedelta(minutes=duration)
    return b.reset_index(drop=True).drop(columns=["first", "last"])
