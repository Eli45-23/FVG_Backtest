"""Controlled change: causal full-hold selection and the ORIGINAL break stop."""

from decimal import Decimal as D
from types import SimpleNamespace
import pandas as pd
import pytest
from scripts.downward_break_full_hold.run import confirmation_status, prices

AT = pd.Timestamp("2020-02-03 15:00", tz="UTC")
END = AT + pd.Timedelta(hours=5)


@pytest.mark.parametrize(
    "high,expected",
    [
        (99.75, "FULL_HOLD"),
        (100, "NEXT_BAR_NOT_FULLY_BELOW"),
        (100.25, "NEXT_BAR_NOT_FULLY_BELOW"),
    ],
)
def test_entire_next_candle_must_be_strictly_below(high, expected):
    assert (
        confirmation_status(
            AT, END, 100, SimpleNamespace(high=high, is_complete_5m=True)
        )
        == expected
    )


@pytest.mark.parametrize("bar", [None, SimpleNamespace(high=99, is_complete_5m=False)])
def test_missing_or_incomplete_no_bridging(bar):
    assert confirmation_status(AT, END, 100, bar) == "MISSING_OR_INCOMPLETE_NEXT_BAR"


def test_session_boundary_confirmation_allowed_but_no_post_close_ownership():
    bar = SimpleNamespace(high=99, is_complete_5m=True)
    assert (
        confirmation_status(END - pd.Timedelta(minutes=5), END, 100, bar) == "FULL_HOLD"
    )
    assert confirmation_status(END, END, 100, bar) == "NO_ADJACENT_SESSION_BAR"


@pytest.mark.parametrize("ticks", [0, 1, 2])
@pytest.mark.parametrize("stop", ["LEVEL_RECLAIM", "BREAK_CANDLE_HIGH"])
def test_absolute_original_stop_frozen_risk_changes_with_entry(ticks, stop):
    original = prices(99, 100, 104, stop, ticks, 2)
    confirmed = prices(97, 100, 104, stop, ticks, 2)
    assert confirmed[1] == original[1]
    assert confirmed[2] == original[2] + 2
    assert confirmed[3] == confirmed[0] - 2 * confirmed[2]
    if stop == "BREAK_CANDLE_HIGH":
        assert confirmed[1] == D("104.25")
