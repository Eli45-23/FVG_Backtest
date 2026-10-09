from decimal import Decimal as D
from types import SimpleNamespace
import pandas as pd
import pytest
from scripts.zone_rejection_v2.core import ActiveZones, milestones
from scripts.zone_reaction_backtest.signals import Detector

T = pd.Timestamp("2020-02-03 08:00", tz="America/New_York").tz_convert("UTC")


def z(id="one", side="SUPPLY", at=T):
    return dict(
        zone_id=id, zone_type=side, bottom=100, top=110, availability_timestamp=at
    )


def b(at=T, o=112, h=114, l=111, c=113, complete=True):
    return SimpleNamespace(
        timestamp_utc=at,
        open=D(str(o)),
        high=D(str(h)),
        low=D(str(l)),
        close=D(str(c)),
        is_complete_5m=complete,
    )


@pytest.mark.parametrize("side", ["SUPPLY", "DEMAND"])
def test_premarket_full_break_permanent(side):
    a = ActiveZones()
    a.add(z(side=side))
    a.observe(b() if side == "SUPPLY" else b(o=98, h=99, l=96, c=97))
    assert not a.known() and a.ended["one"] == T + pd.Timedelta(minutes=5)
    a.observe(b(at=T + pd.Timedelta(minutes=5), o=105, h=109, l=101, c=105))
    assert not a.known()


@pytest.mark.parametrize("row", [b(l=110), b(l=109), b(complete=False)])
def test_equality_wick_and_incomplete_not_break(row):
    a = ActiveZones()
    a.add(z())
    a.observe(row)
    assert "one" in a.known()


def test_replace_same_side_only_never_fallback():
    a = ActiveZones()
    a.add(z())
    a.add(z("d", "DEMAND"))
    a.add(z("new", at=T + pd.Timedelta(minutes=5)))
    assert set(a.known()) == {"new", "d"}
    a.observe(b(at=T + pd.Timedelta(minutes=5)))
    assert set(a.known()) == {"d"} and "one" in a.ended


def test_not_available_during_previous_bar():
    a = ActiveZones()
    a.add(z(at=T + pd.Timedelta(minutes=5)))
    a.observe(b())
    assert a.known()


def test_replacement_at_signal_close_suppresses_old_entry():
    a = ActiveZones()
    a.add(z())
    d = Detector()
    d.update(b(o=98, h=102, l=97, c=99), a.known(), a.ended, T)
    known = a.known()
    a.add(z("new", at=T + pd.Timedelta(minutes=10)))
    assert not d.update(
        b(at=T + pd.Timedelta(minutes=5), o=98, h=99, l=96, c=97), known, a.ended, T
    )


def trade(side="LONG"):
    return dict(
        direction=side,
        entry_price=D(100),
        risk_points=D(10),
        stop_price=D(90 if side == "LONG" else 110),
        entry_time_utc=T,
        exit_time_utc=T + pd.Timedelta(minutes=2),
    )


def minutes(rows):
    return pd.DataFrame(
        rows,
        columns=["open", "high", "low", "close"],
        index=pd.date_range(T, periods=len(rows), freq="min"),
    ).map(lambda x: D(str(x)))


def test_1r_before_later_stop_counts_but_not_same_minute_2r():
    x = milestones(trade(), minutes([[100, 111, 99, 109], [109, 121, 89, 95]]))
    assert (
        x["reached_1r"] and not x["reached_2r"] and x["2r_stop_same_minute_ambiguity"]
    )


def test_conflict_at_first_minute_not_mfe_shortcut():
    x = milestones(trade(), minutes([[100, 121, 89, 95], [95, 125, 94, 123]]))
    assert (
        not x["reached_1r"]
        and not x["reached_2r"]
        and x["1r_stop_same_minute_ambiguity"]
    )


def test_short_milestones_and_no_signal_candle_use():
    m = minutes([[100, 101, 89, 90], [90, 95, 79, 80]])
    m.loc[T - pd.Timedelta(minutes=1)] = [100, 200, 0, 100]
    x = milestones(trade("SHORT"), m.sort_index())
    assert x["reached_1r"] and x["reached_2r"]
    assert x["first_1r_observed_at"] == T + pd.Timedelta(minutes=1)


def test_no_milestone_after_actual_exit():
    t = trade()
    t["exit_time_utc"] = T + pd.Timedelta(minutes=1)
    assert not milestones(t, minutes([[100, 105, 99, 103], [103, 125, 100, 120]]))[
        "reached_1r"
    ]
