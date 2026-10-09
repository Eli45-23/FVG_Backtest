"""Causal opening range breakout rules. No outcome data or position state."""

from decimal import Decimal as D
import hashlib
import pandas as pd
from engine.legacy import reference as ref

NY = "America/New_York"
BINS = [
    "09:45–09:59",
    "10:00–10:29",
    "10:30–10:59",
    "11:00–11:59",
    "12:00–13:59",
    "14:00–15:59",
]


def bucket(at):
    minute = at.tz_convert(NY).hour * 60 + at.tz_convert(NY).minute
    for end, label in zip([600, 630, 660, 720, 840, 960], BINS):
        if minute < end:
            return label
    return "SESSION_CLOSE"


class Detector:
    def __init__(self, high, low, available):
        self.high, self.low, self.available = high, low, available
        self.long_arm = self.short_arm = True
        self.previous = None
        self.number = 0

    def update(self, b):
        at = b.timestamp_utc
        if not b.is_complete_5m:
            self.previous = None
            self.long_arm = self.short_arm = False
            return None
        prev = self.previous
        contiguous = prev is not None and at - prev.timestamp_utc == pd.Timedelta(
            minutes=5
        )
        if prev is not None and not contiguous:
            self.long_arm = self.short_arm = False
        side = None
        if at >= self.available and contiguous:
            if self.long_arm and b.close > self.high:
                side = "LONG"
            elif self.short_arm and b.close < self.low:
                side = "SHORT"
        if side == "LONG":
            self.long_arm = False
        if side == "SHORT":
            self.short_arm = False
        if b.close < self.high:
            self.long_arm = True
        if b.close > self.low:
            self.short_arm = True
        self.previous = b
        if side is None:
            return None
        self.number += 1
        confirmed = at + pd.Timedelta(minutes=5)
        date = str(confirmed.tz_convert(NY).date())
        sid = hashlib.sha256(
            f"opening15-50pt-v1|{date}|{confirmed.isoformat()}|{side}".encode()
        ).hexdigest()
        return dict(
            signal_id=sid,
            event_id=sid,
            date=date,
            year=int(date[:4]),
            direction=side,
            entry_time_utc=confirmed,
            entry_time_ny=confirmed.tz_convert(NY),
            trigger_bar_start=at,
            previous_bar_start=prev.timestamp_utc,
            close=b.close,
            signal_open=b.open,
            signal_high=b.high,
            signal_low=b.low,
            previous_high=prev.high,
            previous_low=prev.low,
            opening_high=self.high,
            opening_low=self.low,
            level_available_at=self.available,
            breakout_number=self.number,
            time_bucket=bucket(confirmed),
        )


def bracket(s, ticks):
    sign = D(1) if s["direction"] == "LONG" else D(-1)
    entry = ref.tick(D(str(s["close"]))) + sign * D(".25") * ticks
    stop = D(str(s["previous_low"] if sign == 1 else s["previous_high"]))
    assert stop % D(".25") == 0
    risk = (entry - stop) * sign
    return dict(
        entry_price=entry,
        stop_price=stop,
        risk_points=risk,
        risk_usd=risk * 2,
        target_price=entry + sign * D(50),
        target_r=D(50) / risk if risk > 0 else None,
    )


def selection_reason(at, end, busy, risk):
    if at >= end:
        return "AT_SESSION_CLOSE"
    if busy is not None and at < busy:
        return "POSITION_OPEN"
    if risk <= 0:
        return "NON_POSITIVE_RISK"
    return None


def independent_signals(frame, high, low, available):
    """Separate vector crossing check, with equality carried within continuity groups."""
    import numpy as np

    g = frame[frame.is_complete_5m].copy().sort_values("timestamp_utc")
    if g.empty:
        return []
    gap = g.timestamp_utc.diff().ne(pd.Timedelta(minutes=5))
    groups = gap.cumsum()
    out = []
    for direction, level, wanted in [("LONG", high, 1), ("SHORT", low, -1)]:
        side = np.sign(g.close.astype(float) - float(level)).replace(0, np.nan)
        history = side.groupby(groups).ffill()
        previous = history.groupby(groups).shift()
        # Opening-range closes cannot have crossed a wick extreme. Seed only the
        # contiguous opening group; after a gap there is no inferred inside state.
        initial = groups.eq(groups.iloc[0]) & g.timestamp_utc.iloc[0].__eq__(
            available - pd.Timedelta(minutes=15)
        )
        previous = previous.mask(initial & previous.isna(), -wanted)
        eligible = (
            (side == wanted)
            & (previous == -wanted)
            & ~gap
            & (g.timestamp_utc >= available)
        )
        out.extend(
            (a + pd.Timedelta(minutes=5), direction)
            for a in g.loc[eligible, "timestamp_utc"]
        )
    return sorted(out)
