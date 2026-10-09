"""Frozen selection semantics, separate from the earlier 50-point strategy."""

from decimal import Decimal as D
from types import SimpleNamespace as S
import pandas as pd
import pytest
from scripts.level_combination.core import wait_entry
from scripts.opening15_breakout.core import selection_reason

T = pd.Timestamp("2020-03-09 15:00", tz="UTC")
END = T + pd.Timedelta(hours=1)


def signal():
    return dict(
        timestamp_utc=T,
        session_close=END,
        direction="UP",
        level_price=100,
        barrier_price=105,
    )


def bar(i, low=106, close=108):
    return S(
        timestamp_utc=T + pd.Timedelta(minutes=5 * i),
        open=107,
        high=110,
        low=low,
        close=close,
        is_complete_5m=True,
    )


def test_root_while_busy_can_confirm_after_exit():
    found, reason = wait_entry(signal(), [bar(0), bar(1)])
    assert reason == "CONFIRMED"
    assert (
        selection_reason(
            found["timestamp_utc"], END, T + pd.Timedelta(minutes=9), D(10)
        )
        is None
    )


def test_hold_confirmation_while_busy_is_discarded():
    found, _ = wait_entry(signal(), [bar(0), bar(1)])
    assert (
        selection_reason(
            found["timestamp_utc"], END, T + pd.Timedelta(minutes=11), D(10)
        )
        == "POSITION_OPEN"
    )


def test_exit_timestamp_equal_allows_new_position():
    assert selection_reason(T, END, T, D(10)) is None


def test_session_close_confirmation_remains_causal_but_cannot_enter():
    e = signal()
    e["session_close"] = T + pd.Timedelta(minutes=10)
    found, reason = wait_entry(e, [bar(0), bar(1)])
    assert reason == "CONFIRMED"
    assert (
        selection_reason(found["timestamp_utc"], e["session_close"], None, D(10))
        == "AT_SESSION_CLOSE"
    )


def test_hold_wick_equality_is_not_confirmation():
    e = signal()
    e["session_close"] = T + pd.Timedelta(minutes=10)
    assert wait_entry(e, [bar(0), bar(1, low=105)])[0] is None


def test_later_reaction_cannot_change_signal():
    assert wait_entry(signal(), [bar(0), bar(1)]) == wait_entry(
        signal(), [bar(0), bar(1), bar(2, low=0, close=1)]
    )


@pytest.mark.parametrize("risk", [D(0), D("-0.25")])
def test_nonpositive_risk_not_traded(risk):
    assert selection_reason(T, END, None, risk) == "NON_POSITIVE_RISK"
