"""Offline forward labeler. Never imported or called by EventDetector."""

import numpy as np
import pandas as pd
from engine.canonical import clean

HORIZONS = [5, 10, 15, 30, 60, "session_close"]
THRESHOLDS = [10, 25, 50, 75, 100]


class PreparedMinutes:
    """Read-only per-day arrays, prepared once rather than once per event/horizon."""

    def __init__(self, frame):
        self.times = frame.index.as_unit("ns").asi8
        self.values = frame[["open", "high", "low", "close"]].to_numpy(dtype=float)
        self.times.setflags(write=False)
        self.values.setflags(write=False)


def label(observation, minutes):
    at = pd.Timestamp(observation["timestamp_utc"]).tz_convert("UTC")
    end = pd.Timestamp(observation["session_close"]).tz_convert("UTC")
    price = float(observation["price_at_event"])
    m = minutes if isinstance(minutes, PreparedMinutes) else PreparedMinutes(minutes)
    labels = {}
    minute_ns = 60_000_000_000
    left = np.searchsorted(m.times, at.value)
    for horizon in HORIZONS:
        stop = end if horizon == "session_close" else at + pd.Timedelta(minutes=horizon)
        base = {"horizon": str(horizon), "complete": False, "censor_reason": None}
        if stop > end or stop <= at:
            labels[str(horizon)] = {**base, "censor_reason": "OUTSIDE_SESSION"}
            continue
        right = np.searchsorted(m.times, stop.value)
        times = m.times[left:right]
        expected = int((stop - at).total_seconds() / 60)
        if (
            len(times) != expected
            or times[0] != at.value
            or not np.all(np.diff(times) == minute_ns)
        ):
            labels[str(horizon)] = {**base, "censor_reason": "MISSING_MINUTES"}
            continue
        values = m.values[left:right]
        op, high, low, close = values.T
        if (
            not np.isfinite(values).all()
            or not (
                (high >= np.maximum.reduce([op, close, low]))
                & (low <= np.minimum(op, close))
            ).all()
        ):
            labels[str(horizon)] = {**base, "censor_reason": "INVALID_OHLC"}
            continue
        up = max(0.0, float(high.max()) - price)
        down = max(0.0, price - float(low.min()))
        thresholds = {}
        for sign, series in [("up", high - price), ("down", price - low)]:
            for distance in THRESHOLDS:
                hits = np.flatnonzero(series >= distance)
                thresholds[f"{sign}_{distance}"] = {
                    "reached": bool(len(hits)),
                    "minutes": int(hits[0]) + 1 if len(hits) else None,
                }
        direction = observation.get("direction")
        labels[str(horizon)] = {
            **base,
            "complete": True,
            "forward_close_change": float(close[-1]) - price,
            "maximum_high_excursion": up,
            "maximum_low_excursion": down,
            "mfe": up if direction == "UP" else down if direction == "DOWN" else None,
            "mae": down if direction == "UP" else up if direction == "DOWN" else None,
            "thresholds": thresholds,
        }
    return clean(labels)


def directional(outcome, direction, interpretation="continuation"):
    if not outcome.get("complete") or direction == "UNKNOWN":
        return None, None
    up = (direction == "UP") == (interpretation == "continuation")
    return (
        (outcome["maximum_high_excursion"], outcome["maximum_low_excursion"])
        if up
        else (outcome["maximum_low_excursion"], outcome["maximum_high_excursion"])
    )
