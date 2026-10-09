"""Causal context and waiting policy. No forward outcomes enter these functions."""

import json
import math
import pandas as pd
from engine.research.levels import valid_bar

FIVE = pd.Timedelta(minutes=5)


def context(event, levels):
    at = pd.Timestamp(event["timestamp_utc"])
    known = [
        l for l in levels if l["available"] and pd.Timestamp(l["availability"]) <= at
    ]
    others = [l for l in known if l["level"] != event["level_type"]]
    direction = 1 if event["direction"] == "UP" else -1
    price = float(event["price_at_event"])
    root = float(event["level_price"])
    atr = event.get("atr14")
    usable = atr is not None and math.isfinite(float(atr)) and float(atr) > 0
    forward = sorted(
        [
            (direction * (float(l["price"]) - price), l)
            for l in others
            if direction * (float(l["price"]) - price) > 0
        ],
        key=lambda x: (x[0], x[1]["level"]),
    )
    obstacles = [l for d, l in forward if usable and d <= float(atr)]
    cluster = [
        l for l in others if usable and abs(float(l["price"]) - root) <= float(atr)
    ]
    barrier = max((float(l["price"]) * direction for l in obstacles), default=None)
    return dict(
        known_level_count=len(known),
        full_level_coverage=len(known) == 8,
        known_levels=json.dumps(
            [{k: l[k] for k in ["level", "price", "availability"]} for l in known],
            sort_keys=True,
            default=str,
        ),
        context_status="KNOWN" if usable else "ATR_UNAVAILABLE",
        obstacle_count=len(obstacles),
        obstacle_levels="|".join(l["level"] for l in obstacles),
        barrier_price=barrier * direction if barrier is not None else None,
        nearest_level=forward[0][1]["level"] if forward else None,
        room_points=forward[0][0] if forward else None,
        room_atr=forward[0][0] / float(atr) if forward and usable else None,
        cluster_group=("CLUSTERED" if cluster else "ISOLATED") if usable else "UNKNOWN",
        cluster_count=len(cluster),
        cluster_levels="|".join(l["level"] for l in cluster),
        cluster_candle_contacts=sum(
            float(event["low"]) <= float(l["price"]) <= float(event["high"])
            for l in cluster
        ),
        coincident_levels=sum(float(l["price"]) == root for l in others),
    )


def wait_entry(event, bars):
    """Bars are processed in order and truncated by the caller to the same session."""
    s = 1 if event["direction"] == "UP" else -1
    root, barrier = float(event["level_price"]), float(event["barrier_price"])
    expected = pd.Timestamp(event["timestamp_utc"])
    end = pd.Timestamp(event["session_close"])
    cleared = False
    for row in bars:
        if row.timestamp_utc < expected:
            continue
        if row.timestamp_utc >= end:
            break
        if row.timestamp_utc != expected or not valid_bar(row):
            return None, "MISSING_OR_INCOMPLETE_ADJACENCY"
        expected += FIVE
        if (float(row.close) - root) * s <= 0:
            return None, "ROOT_RECLAIMED"
        full = float(row.low) > barrier if s == 1 else float(row.high) < barrier
        if cleared and full:
            return (
                dict(
                    timestamp_utc=expected,
                    price_at_event=float(row.close),
                    confirmation_high=float(row.high),
                    confirmation_low=float(row.low),
                ),
                "CONFIRMED",
            )
        cleared = (float(row.close) - barrier) * s > 0
    if expected < end:
        return None, "MISSING_OR_INCOMPLETE_ADJACENCY"
    return None, "SESSION_ENDED"
