"""Research-only path measurements; fills remain delegated to the production executor."""

import numpy as np


def first(mask):
    ix = np.flatnonzero(mask)
    return int(ix[0]) if len(ix) else None


def path_measurements(ohlc, entry, stop, risk, atr, expected_minutes, first_gap=None):
    """Known continuous minute prefix only. Inclusive exit-bar extrema are upper bounds."""
    n = len(ohlc)
    high = ohlc[:, 1] if n else np.array([])
    low = ohlc[:, 2] if n else np.array([])
    si = first(low <= stop)
    resolved = si is not None or (n == expected_minutes and first_gap is None)
    used = n if si is None else si + 1
    out = {
        "path_status": (
            "STOP"
            if si is not None
            else "SESSION_CLOSE" if resolved else "EXECUTION_DATA_UNAVAILABLE"
        ),
        "owned_prefix_minutes": used,
        "minutes_to_stop": si + 1 if si is not None else None,
        "mfe_points": max(0, float(high[:used].max()) - entry) if used else None,
        "mae_points": max(0, entry - float(low[:used].min())) if used else None,
        "path_complete": resolved,
        "stop_touched": si is not None,
    }
    out["exit_minute_extrema_order_unknown"] = si is not None
    before = used - 1 if si is not None else used
    out["mfe_points_lower_bound"] = (
        max(0, float(high[:before].max()) - entry) if before else 0 if used else None
    )
    out["mae_points_lower_bound"] = (
        max(0, entry - float(low[:before].min())) if before else 0 if used else None
    )
    for name in ["mfe", "mae"]:
        points = out[name + "_points"]
        out[name + "_r"] = points / risk if points is not None else None
        out[name + "_atr"] = (
            points / atr if points is not None and atr is not None else None
        )
    for horizon in [15, 30, 60]:
        complete = expected_minutes >= horizon and n >= horizon
        out[f"complete_{horizon}m"] = complete
        out[f"stop_hit_{horizon}m"] = (
            bool(si is not None and si < horizon) if complete else None
        )
        out[f"censor_{horizon}m"] = (
            None
            if complete
            else (
                "SESSION_BOUNDARY"
                if expected_minutes < horizon and n >= expected_minutes
                else "MISSING_MINUTES"
            )
        )
    for unit, levels in [("r", [0.5, 1, 1.25, 1.5, 2]), ("atr", [0.5, 1, 1.5])]:
        for target in levels:
            tag = unit + str(target).replace(".", "p")
            if unit == "atr" and atr is None:
                out.update(
                    {
                        tag + "_before_stop": None,
                        tag + "_minutes": None,
                        tag + "_conflict": None,
                    }
                )
                continue
            threshold = entry + target * (risk if unit == "r" else atr)
            ti = first(high >= threshold)
            hit = ti is not None and (si is None or ti < si)
            out[tag + "_before_stop"] = hit if hit or resolved else None
            out[tag + "_minutes"] = ti + 1 if hit else None
            out[tag + "_conflict"] = ti is not None and si is not None and ti == si
            if unit == "r" and target in [0.5, 1]:
                lo = (
                    max(0, entry - float(low[:ti].min()))
                    if hit and ti
                    else 0 if hit else None
                )
                hi = max(lo, entry - float(low[ti])) if hit else None
                out[tag + "_mae_before_hit_lower"] = lo
                out[tag + "_mae_before_hit_upper"] = hi
                out[tag + "_mae_order_ambiguous"] = hi > lo if hit else None
    pos = first(high >= entry + 0.5 * risk)
    neg = first(low <= entry - 0.5 * risk)
    out["half_r_before_minus_half_r"] = (
        bool(pos is not None and (neg is None or pos < neg))
        if pos is not None or neg is not None or resolved
        else None
    )
    out["half_r_race_conflict"] = pos is not None and neg is not None and pos == neg
    out["stop_before_half_r"] = (
        bool(si is not None and (pos is None or si <= pos)) if resolved else None
    )
    return out


def independent_fill(ohlc, entry, stop, target, ticks, expected_minutes):
    """Simple independent numerical check against every native fixed-bracket fill."""
    for i, (op, hi, lo, cl) in enumerate(ohlc):
        if lo <= stop:
            return i, "STOP", min(stop, op) - ticks * 0.25, bool(hi >= target)
        if hi >= target:
            return i, "TARGET", target - ticks * 0.25, False
        if i + 1 == expected_minutes:
            return i, "SESSION_CLOSE", cl - ticks * 0.25, False
    return None
