from decimal import Decimal as D
import numpy as np
import pandas as pd
import pytest
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref
from scripts.downward_break_feasibility.run import prices
from scripts.pml_feasibility.core import short_fill, short_path


@pytest.mark.parametrize(
    "stop_name,expected",
    [("LEVEL_RECLAIM", D("100.25")), ("BREAK_CANDLE_HIGH", D("103.25"))],
)
def test_stops_and_executed_risk(stop_name, expected):
    entry, stop, risk, target = prices(99, 100, 103, stop_name, 1, 2)
    assert entry == D("98.75") and stop == expected and risk == stop - entry
    assert target == entry - 2 * risk


@pytest.mark.parametrize("ticks", [0, 1, 2])
@pytest.mark.parametrize("target_r", [1, 2])
def test_native_fee_and_independent_short_fill(ticks, target_r):
    at = pd.Timestamp("2020-02-03 15:00", tz="UTC")
    entry, stop, risk, target = prices(
        99, 100, 103, "BREAK_CANDLE_HIGH", ticks, target_r
    )
    # The completed signal candle has a huge range but is not owned.
    frame = pd.DataFrame(
        dict(
            open=[99, 99, 90],
            high=[200, 100, 92],
            low=[0, 80, 85],
            close=[99, 90, 89],
            volume=[1, 1, 1],
        ),
        index=pd.date_range(at - pd.Timedelta(minutes=1), periods=3, freq="min"),
    )
    for k in ["open", "high", "low", "close"]:
        frame[k] = frame[k].map(lambda v: D(str(v)))
    s = dict(
        direction="SHORT",
        entry_price=entry,
        stop_price=stop,
        risk_points=risk,
        target_price=target,
        entry_time_utc=at,
        entry_time_ny=at.tz_convert("America/New_York"),
        signal_id="synthetic",
    )
    result, _ = execute(
        s,
        frame,
        ref.Config(D(".73"), ticks),
        1,
        Entry("SHORT", stop, D(target_r)),
        None,
        {},
        {},
        at + pd.Timedelta(minutes=2),
    )
    assert result["exit_reason"] == "TARGET"
    assert result["commission_usd"] == D("1.46")
    assert result["net_pnl_usd"] == (entry - target - D(".25") * ticks) * 2 - D("1.46")
    assert result["management_event_count"] == 0 and result["final_stop_price"] == stop
    arr = frame.iloc[1:][["open", "high", "low", "close"]].to_numpy(dtype=float)
    independent = short_fill(arr, float(entry), float(stop), float(target), ticks, 2)
    assert independent[1] == "TARGET" and independent[2] == float(result["exit_price"])


def test_conflict_and_adverse_stop_gap():
    arr = np.array([[105, 107, 90, 96]], dtype=float)
    assert short_fill(arr, 99, 103, 95, 1, 1) == (0, "STOP", 105.25, True)


def test_stop_before_missing_minute_resolves():
    arr = np.array([[99, 104, 98, 100]], dtype=float)
    assert short_fill(arr, 99, 103, 95, 1, 10) == (0, "STOP", 103.25, False)
    m = short_path(arr, 99, 103, 4, None, 10, "missing")
    assert m["path_complete"] and m["path_status"] == "STOP"
    assert not m["complete_15m"] and m["atr1_before_stop"] is None


def test_unresolved_missing_and_session_boundary():
    arr = np.array([[99, 100, 98, 99]], dtype=float)
    assert short_fill(arr, 99, 103, 95, 1, 10) is None
    assert short_fill(arr, 99, 103, 95, 1, 1) == (0, "SESSION_CLOSE", 99.25, False)


def test_signal_high_does_not_replace_level_stop():
    _, level_stop, _, _ = prices(99, 100, 120, "LEVEL_RECLAIM", 1, 1)
    assert level_stop == D("100.25")
