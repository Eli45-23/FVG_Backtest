"""Saved descriptive range/bucket settings; no strategy thresholds are optimized."""

import math
from bisect import bisect_right

NUMERIC = (
    "atr14",
    "atr_percentile",
    "event_candle_range",
    "body_ratio",
    "break_distance_points",
    "break_distance_atr",
    "penetration_points",
    "penetration_atr",
    "room_points",
    "room_atr",
    "opening_range_size",
    "opening_range_atr",
    "premarket_range_size",
    "premarket_range_atr",
    "prior_day_range",
    "prior_day_range_atr",
    "overnight_gap",
    "overnight_gap_atr",
    "distance_open_to_level",
    "distance_open_to_level_atr",
    "distance_to_pdh",
    "distance_to_pdl",
    "distance_to_next_level",
    "ema_separation",
    "ema_absolute_separation",
    "ema_separation_atr",
    "ema9_slope",
    "ema20_slope",
    "vwap_distance",
    "vwap_distance_atr",
    "swing_displacement",
    "swing_displacement_atr",
    "zone_distance",
    "zone_distance_atr",
    "directional_efficiency",
    "rolling_range_atr",
    "retest_delay",
    "retest_penetration",
    "hold_body_ratio",
    "hold_candle_range",
    "minutes_since_rth_open",
    "ema9",
    "ema20",
    "vwap",
    "rth_open",
    "previous_rth_close",
    "opening_location",
    "vwap_cross_frequency",
)
CATEGORIES = (
    "level_type",
    "interaction_type",
    "compound_interaction",
    "direction",
    "approach_side",
    "touch_number",
    "year",
    "month",
    "weekday",
    "time_bucket",
    "volatility_bucket",
    "atr_regime",
    "structure_state",
    "ema_alignment",
    "vwap_alignment",
)


def validate(spec):
    for key, rule in spec.items():
        if key not in NUMERIC or set(rule) - {"min", "max", "edges"}:
            raise ValueError("Unknown numeric filter")
        for k in ("min", "max"):
            if rule.get(k) is not None and not math.isfinite(float(rule[k])):
                raise ValueError("Numeric filters must be finite")
        if (
            rule.get("min") is not None
            and rule.get("max") is not None
            and rule["min"] > rule["max"]
        ):
            raise ValueError("Reversed numeric interval")
        edges = rule.get("edges", [])
        if (
            len(edges) > 50
            or any(not math.isfinite(float(x)) for x in edges)
            or edges != sorted(set(edges))
        ):
            raise ValueError("Bucket edges must be finite, unique, increasing (max 50)")
    return spec


def accepts(event, spec):
    for key, r in spec.items():
        v = event.get(key)
        if r.get("min") is not None and (v is None or float(v) < r["min"]):
            return False
        if r.get("max") is not None and (v is None or float(v) > r["max"]):
            return False
    return True


def bucket(value, edges):
    if value is None:
        return "unavailable"
    i = bisect_right(edges, float(value))
    return f'[{edges[i-1] if i else "-inf"}, {edges[i] if i<len(edges) else "inf"})'
