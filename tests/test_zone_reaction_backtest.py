"""Frozen voice-defined setups; synthetic Development candles only."""

from types import SimpleNamespace
from decimal import Decimal as D
import pandas as pd
import pytest
from scripts.zone_reaction_backtest.signals import Detector, bracket, selection_reason
from engine.zone_v2.acceptance import (
    assess_mechanical,
    require_mechanical_acceptance,
    REQUIRED,
)

T = pd.Timestamp("2020-02-03 14:30", tz="UTC")


def candle(i, o=98, h=102, l=97, c=99, complete=True):
    return SimpleNamespace(
        timestamp_utc=T + pd.Timedelta(minutes=5 * i),
        open=D(str(o)),
        high=D(str(h)),
        low=D(str(l)),
        close=D(str(c)),
        is_complete_5m=complete,
    )


def zone(side="SUPPLY"):
    return dict(
        zone_id="z", zone_type=side, bottom=100, top=110, availability_timestamp=T
    )


def detect(rows, side="SUPPLY", invalid=None):
    d = Detector()
    result = []
    for r in rows:
        result.extend(d.update(r, {"z": zone(side)}, invalid or {}, T))
    return result


@pytest.mark.parametrize("side", ["SUPPLY", "DEMAND"])
@pytest.mark.parametrize("tap", [False, True])
def test_rejection_and_exact_tap(side, tap):
    if side == "SUPPLY":
        rows = [candle(0, h=100 if tap else 102), candle(1, h=99, l=96, c=97)]
    else:
        rows = [
            candle(0, o=112, h=113, l=110 if tap else 108, c=112),
            candle(1, o=112, h=115, l=111, c=114),
        ]
    s = detect(rows, side)
    assert len(s) == 1 and s[0]["setup"] == ("B" if tap else "A")
    assert s[0]["direction"] == ("SHORT" if side == "SUPPLY" else "LONG")
    assert s[0]["entry_time_utc"] == T + pd.Timedelta(minutes=10)


@pytest.mark.parametrize("side", ["SUPPLY", "DEMAND"])
def test_break_and_adjacent_confirmation(side):
    if side == "SUPPLY":
        rows = [
            candle(0),
            candle(1, o=112, h=115, l=111, c=114),
            candle(2, o=114, h=116, l=111, c=112),
        ]
    else:
        rows = [
            candle(0, o=112, h=113, l=108, c=111),
            candle(1, o=98, h=99, l=96, c=97),
            candle(2, o=97, h=99, l=95, c=98),
        ]
    s = detect(rows, side)
    assert len(s) == 1 and s[0]["setup"] == "C"
    assert s[0]["direction"] == ("LONG" if side == "SUPPLY" else "SHORT")
    assert s[0]["entry_time_utc"] == T + pd.Timedelta(minutes=15)


def test_wick_inside_is_not_whole_candle_outside():
    assert not detect([candle(0), candle(1, h=100, c=97, l=96)])


def test_tap_followed_by_penetration_is_a_not_b():
    s = detect([candle(0, h=100), candle(1), candle(2, h=99, l=96, c=97)])
    assert [x["setup"] for x in s] == ["A"]


@pytest.mark.parametrize(
    "rows",
    [
        [candle(0), candle(2, h=99, l=96, c=97)],
        [candle(0), candle(1, complete=False), candle(2, h=99, l=96, c=97)],
        [
            candle(0),
            candle(1, o=112, h=115, l=111, c=114),
            candle(3, o=114, h=116, l=111, c=112),
        ],
    ],
)
def test_gaps_and_incomplete_cannot_bridge(rows):
    assert not detect(rows)


def test_no_future_zone():
    z = zone()
    z["availability_timestamp"] = T + pd.Timedelta(minutes=5)
    with pytest.raises(AssertionError):
        Detector().update(candle(0), {"z": z}, {}, T)


def test_no_wrong_side_approach():
    assert not detect(
        [candle(0, o=111, h=112, l=99, c=100), candle(1, h=99, l=96, c=97)]
    )


def test_invalidated_zone_cannot_reject():
    d = Detector()
    d.update(candle(0), {"z": zone()}, {}, T)
    assert not d.update(
        candle(1, h=99, l=96, c=97),
        {"z": zone()},
        {"z": T + pd.Timedelta(minutes=10)},
        T,
    )


def test_same_break_invalidation_allows_only_pending_confirmation():
    d = Detector()
    d.update(candle(0), {"z": zone()}, {}, T)
    at = T + pd.Timedelta(minutes=10)
    assert not d.update(
        candle(1, o=112, h=115, l=111, c=114), {"z": zone()}, {"z": at}, T
    )
    s = d.update(candle(2, o=114, h=116, l=111, c=112), {"z": zone()}, {"z": at}, T)
    assert len(s) == 1 and s[0]["setup"] == "C"
    assert not d.update(
        candle(3, o=114, h=116, l=111, c=112), {"z": zone()}, {"z": at}, T
    )


def test_failed_confirmation_not_retried_without_new_contact():
    rows = [
        candle(0),
        candle(1, o=112, h=115, l=111, c=114),
        candle(2, o=112, h=113, l=109, c=111),
        candle(3, o=112, h=115, l=111, c=114),
        candle(4, o=112, h=115, l=111, c=114),
    ]
    assert not detect(rows)


@pytest.mark.parametrize(
    "direction,stop", [("LONG", D("99.75")), ("SHORT", D("110.25"))]
)
def test_boundary_stop_adverse_entry_fixed_2r(direction, stop):
    b = bracket(dict(direction=direction, close=105, zone_top=110, zone_bottom=100))
    assert b["stop_price"] == stop
    assert b["entry_price"] == (D("105.25") if direction == "LONG" else D("104.75"))
    assert abs(b["target_price"] - b["entry_price"]) == 2 * b["risk_points"]
    assert all(
        b[k] % D(".25") == 0 for k in ["stop_price", "entry_price", "target_price"]
    )


def test_position_lock_and_fresh_episode():
    s = dict(entry_time_utc=T + pd.Timedelta(minutes=15), episode_start=T)
    assert (
        selection_reason(
            s, T + pd.Timedelta(minutes=20), None, T + pd.Timedelta(hours=6)
        )
        == "POSITION_OPEN"
    )
    assert (
        selection_reason(
            s, None, T + pd.Timedelta(minutes=5), T + pd.Timedelta(hours=6)
        )
        == "EPISODE_BEGAN_BEFORE_PREVIOUS_EXIT"
    )
    s["episode_start"] = T + pd.Timedelta(minutes=10)
    assert (
        selection_reason(
            s, None, T + pd.Timedelta(minutes=5), T + pd.Timedelta(hours=6)
        )
        is None
    )
    assert selection_reason(s, None, None, s["entry_time_utc"]) == "AT_SESSION_CLOSE"


def test_deterministic_signal_identity():
    rows = [candle(0), candle(1, h=99, l=96, c=97)]
    assert detect(rows) == detect(rows)


def test_authorized_mechanical_gate_and_old_proof_isolation():
    c = {k: True for k in REQUIRED}
    r = assess_mechanical(c, {}, "hash")
    require_mechanical_acceptance(r, {}, "hash", "development")
    assert r["human_ground_truth_required"] is False
    for segment in ["validation", "oos"]:
        with pytest.raises(ValueError):
            require_mechanical_acceptance(r, {}, "hash", segment)
    with pytest.raises(ValueError):
        require_mechanical_acceptance(r, {}, "changed", "development")
    c["source_reconciled"] = False
    with pytest.raises(ValueError):
        require_mechanical_acceptance(
            assess_mechanical(c, {}, "hash"), {}, "hash", "development"
        )
