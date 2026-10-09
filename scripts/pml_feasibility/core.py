"""Research-only SHORT measurements; production engine still performs all fills."""

from scripts.swing_low_feasibility.core import path_measurements, independent_fill


def mirror(ohlc):
    return -ohlc[:, [0, 2, 1, 3]]


def short_path(ohlc, entry, stop, risk, atr, expected, gap=None):
    arr = mirror(ohlc)
    out = path_measurements(arr, -entry, -stop, risk, atr, expected, gap)
    for horizon in (15, 30, 60):
        # A horizon denominator requires the entire observation, irrespective of exit.
        complete = expected >= horizon and len(arr) >= horizon
        prefix = arr[:horizon]
        m = path_measurements(
            prefix, -entry, -stop, risk, atr, horizon, None if complete else "CENSORED"
        )
        for key, value in m.items():
            if key.endswith(("_before_stop", "_conflict")) and key.startswith(
                ("r", "atr")
            ):
                out[f"{horizon}m_{key}"] = value if complete else None
    return out


def short_fill(ohlc, entry, stop, target, ticks, expected):
    result = independent_fill(mirror(ohlc), -entry, -stop, -target, ticks, expected)
    if result is None:
        return None
    i, reason, price, conflict = result
    return i, reason, -price, conflict
