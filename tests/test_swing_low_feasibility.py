"""Synthetic only: no database or historical/reserved data access."""

from pathlib import Path
import sys

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "scripts/swing_low_feasibility")
)
import numpy as np
import pytest
from core import path_measurements, independent_fill


def test_same_minute_stop_first():
    a = np.array([[100, 103, 97, 102]])
    r = path_measurements(a, 100, 98, 2, 2, 1)
    assert not r["r1_before_stop"] and r["r1_conflict"]
    assert independent_fill(a, 100, 98, 102, 1, 1) == (0, "STOP", 97.75, True)


def test_missing_after_target_does_not_cancel_completed_trade():
    a = np.array([[100, 103, 99, 102]])
    assert independent_fill(a, 100, 98, 102, 1, 30) == (0, "TARGET", 101.75, False)
    assert independent_fill(a, 100, 98, 104, 1, 30) is None
    r = path_measurements(a, 100, 98, 2, 2, 30, "missing")
    assert r["path_status"] == "EXECUTION_DATA_UNAVAILABLE" and r["r1_before_stop"]
    assert r["r2_before_stop"] is None


def test_atr_null_does_not_remove_r_results():
    r = path_measurements(np.array([[100, 103, 99, 102]]), 100, 98, 2, None, 1)
    assert r["r1_before_stop"] and r["atr1_before_stop"] is None
    assert r["mfe_atr"] is None and r["mfe_r"] == 1.5


def test_short_session_censors_horizon_but_exits_normally():
    a = np.array([[100, 101, 99, 100.5]])
    assert independent_fill(a, 100, 98, 102, 1, 1) == (
        0,
        "SESSION_CLOSE",
        100.25,
        False,
    )
    r = path_measurements(a, 100, 98, 2, 2, 1)
    assert r["path_complete"] and not r["complete_30m"] and r["stop_hit_30m"] is None


def test_mae_before_target_has_order_bounds():
    r = path_measurements(
        np.array([[100, 100.5, 99.75, 100], [100, 102, 99, 101]]), 100, 98, 2, 2, 2
    )
    assert r["r1_mae_before_hit_lower"] == 0.25
    assert r["r1_mae_before_hit_upper"] == 1
    assert r["r1_mae_order_ambiguous"]


def test_adverse_stop_gap_and_slippage():
    assert independent_fill(np.array([[97, 99, 96, 98]]), 100, 98, 102, 2, 1) == (
        0,
        "STOP",
        96.5,
        False,
    )


def test_stop_before_signal_is_not_in_owned_array():
    # Array begins at confirmed entry; prior signal-candle extremes are absent.
    r = path_measurements(np.array([[100, 103, 99, 102]]), 100, 98, 2, 2, 1)
    assert r["r1_before_stop"] and not r["stop_touched"]


def test_half_r_race_adverse_first():
    r = path_measurements(np.array([[100, 101, 99, 100]]), 100, 98, 2, 2, 1)
    assert r["half_r_race_conflict"] and not r["half_r_before_minus_half_r"]


def test_stop_in_final_minute_beats_session_close():
    assert independent_fill(np.array([[100, 101, 97, 100]]), 100, 98, 102, 0, 1) == (
        0,
        "STOP",
        98,
        False,
    )


def test_complete_horizon_denominator_independent_of_early_stop():
    a = np.array([[100, 101, 97, 98]] * 30)
    r = path_measurements(a, 100, 98, 2, 2, 30)
    assert r["complete_30m"] and r["stop_hit_30m"]
    assert not r["complete_60m"] and r["stop_hit_60m"] is None
    assert r["owned_prefix_minutes"] == 1


def test_stop_minute_extrema_are_only_upper_bounds():
    r = path_measurements(
        np.array([[100, 100.5, 99.75, 100], [100, 105, 97, 98]]), 100, 98, 2, 2, 2
    )
    assert r["exit_minute_extrema_order_unknown"]
    assert r["mfe_points_lower_bound"] == 0.5 and r["mfe_points"] == 5
    assert r["mae_points_lower_bound"] == 0.25 and r["mae_points"] == 3


def test_native_executor_rejects_required_missing_minute():
    from decimal import Decimal as D
    import pandas as pd

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from engine.partial_execution import execute
    from engine.strategy import Entry
    from engine.legacy import reference as ref

    at = pd.Timestamp("2020-01-02T15:00:00Z")
    s = {
        "direction": "LONG",
        "entry_price": D(100),
        "stop_price": D(98),
        "risk_points": D(2),
        "target_price": D(102),
        "entry_time_utc": at,
        "entry_time_ny": at.tz_convert("America/New_York"),
        "signal_id": "synthetic",
    }
    m = pd.DataFrame(
        [dict(ts_event=at, open=D(100), high=D(101), low=D(99), close=D(100), volume=1)]
    ).set_index("ts_event", drop=False)
    with pytest.raises(ValueError, match="Missing execution minute"):
        execute(
            s,
            m,
            ref.Config(D(".73"), 1),
            1,
            Entry("LONG", D(98), D(1)),
            None,
            {},
            {},
            at + pd.Timedelta(minutes=2),
        )
    m.loc[at, "high"] = D(103)
    t, _ = execute(
        s,
        m,
        ref.Config(D(".73"), 1),
        1,
        Entry("LONG", D(98), D(1)),
        None,
        {},
        {},
        at + pd.Timedelta(minutes=2),
    )
    assert t["exit_reason"] == "TARGET" and t["commission_usd"] == D("1.46")
