"""Synthetic-only tests: no database, historical files, or reserved-period access."""

import numpy as np
import pandas as pd
from decimal import Decimal as D
from types import SimpleNamespace
from scripts.pml_feasibility.core import short_path, short_fill
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref
from engine.research.sequences import Sequences


def test_short_stop_first_conflict():
    a = np.array([[100, 103, 97, 100]])
    p = short_path(a, 100, 102, 2, 2, 1)
    assert not p["r1_before_stop"] and p["r1_conflict"]
    assert short_fill(a, 100, 102, 98, 1, 1) == (0, "STOP", 102.25, True)


def test_short_gap_adverse_fill():
    assert short_fill(np.array([[104, 105, 99, 101]]), 100, 102, 98, 2, 1) == (
        0,
        "STOP",
        104.5,
        False,
    )


def test_short_target_slippage():
    assert short_fill(np.array([[100, 101, 97, 98]]), 100, 102, 98, 1, 1) == (
        0,
        "TARGET",
        98.25,
        False,
    )


def test_horizons_are_not_session_races():
    a = np.tile([100, 100.5, 99.5, 100.0], (60, 1))
    a[20] = [100, 101, 97, 98]
    p = short_path(a, 100, 102, 2, 2, 60)
    assert (
        not p["15m_r1_before_stop"]
        and p["30m_r1_before_stop"]
        and p["60m_r1_before_stop"]
    )


def test_censored_horizon_stays_null_even_when_target_hit():
    p = short_path(np.array([[100, 101, 97, 98]]), 100, 102, 2, 2, 1)
    assert p["r1_before_stop"] and p["30m_r1_before_stop"] is None
    assert not p["complete_30m"]


def test_missing_does_not_discard_earlier_fill():
    a = np.array([[100, 101, 97, 98]])
    assert short_fill(a, 100, 102, 98, 1, 30) is not None
    assert short_fill(a, 100, 102, 96, 1, 30) is None
    p = short_path(a, 100, 102, 2, 2, 30, "gap")
    assert p["r1_before_stop"] and p["r2_before_stop"] is None
    assert p["30m_r1_before_stop"] is None


def test_atr_missing_keeps_r_analysis():
    p = short_path(np.array([[100, 101, 97, 98]]), 100, 102, 2, None, 1)
    assert p["r1_before_stop"] and p["atr1_before_stop"] is None


def test_short_excursions_and_mae_bounds():
    p = short_path(
        np.array([[100, 100.5, 99.5, 100], [100, 101, 97, 98]]), 100, 102, 2, 2, 2
    )
    assert p["mfe_points"] == 3 and p["mae_points"] == 1
    assert p["r1_mae_before_hit_lower"] == 0.5 and p["r1_mae_before_hit_upper"] == 1
    assert p["r1_mae_order_ambiguous"]


def test_session_final_minute_stop_precedes_close():
    assert short_fill(np.array([[100, 103, 99, 101]]), 100, 102, 98, 0, 1)[1] == "STOP"


def test_session_close_exit():
    assert short_fill(np.array([[100, 101, 99, 100.5]]), 100, 102, 98, 1, 1) == (
        0,
        "SESSION_CLOSE",
        100.75,
        False,
    )


def test_native_execution_excludes_failure_bar_and_charges_actual_fees():
    at = pd.Timestamp("2021-01-04 15:00Z")
    end = at + pd.Timedelta(minutes=1)
    data = pd.DataFrame(
        [[D(100), D(110), D(90), D(100)], [D(100), D(101), D(97), D(98)]],
        columns=["open", "high", "low", "close"],
        index=[at - pd.Timedelta(minutes=1), at],
    )
    s = dict(
        direction="SHORT",
        entry_price=D(100),
        stop_price=D(102),
        target_price=D(98),
        risk_points=D(2),
        entry_time_utc=at,
        entry_time_ny=at.tz_convert("America/New_York"),
        signal_id="test",
    )
    t, _ = execute(
        s,
        data,
        ref.Config(D(".73"), 1),
        1,
        Entry("SHORT", D(102), D(1)),
        None,
        {},
        {},
        end,
    )
    assert t["exit_reason"] == "TARGET" and t["exit_price"] == D("98.25")
    assert t["net_pnl_usd"] == D("2.04") and t["commission_usd"] == D("1.46")


def row(at, close, complete=True):
    return SimpleNamespace(
        timestamp_utc=pd.Timestamp(at),
        open=D(99),
        high=D(102),
        low=D(97),
        close=D(close),
        is_complete_5m=complete,
    )


def root():
    return dict(
        event_id="root",
        close="99",
        level_id="pml",
        level_price="100",
        direction="DOWN",
        interaction_type="BREAK_ACCEPTANCE",
        timestamp_utc="2021-01-04T15:00:00+00:00",
        touch_number=2,
        date="2021-01-04",
    )


def test_failure_is_adjacent_close_above_not_touch():
    seq = Sequences()
    seq.update(row("2021-01-04 14:55Z", 99), [root()])
    e = seq.update(row("2021-01-04 15:00Z", 101), [])
    assert len(e) == 1 and e[0]["interaction_type"] == "BREAK_FAILED_NEXT_CANDLE_HOLD"
    assert e[0]["direction"] == "DOWN" and e[0]["touch_number"] == 2
    assert pd.Timestamp(e[0]["timestamp_utc"]) == pd.Timestamp("2021-01-04 15:05Z")


def test_missing_adjacent_candle_prevents_failure():
    seq = Sequences()
    seq.update(row("2021-01-04 14:55Z", 99), [root()])
    assert not seq.update(row("2021-01-04 15:05Z", 101), [])


def test_incomplete_adjacent_candle_prevents_failure():
    seq = Sequences()
    seq.update(row("2021-01-04 14:55Z", 99), [root()])
    assert not seq.update(row("2021-01-04 15:00Z", 101, False), [])


def test_exact_level_close_is_not_failed_hold():
    seq = Sequences()
    seq.update(row("2021-01-04 14:55Z", 99), [root()])
    assert not seq.update(row("2021-01-04 15:00Z", 100), [])
