from types import SimpleNamespace
from decimal import Decimal as D
import pandas as pd
import pytest
from scripts.opening15_breakout.core import Detector, bracket, selection_reason, bucket
from engine.partial_execution import execute
from engine.legacy import reference as ref
from engine.strategy import Entry

T = pd.Timestamp("2020-03-09 09:30", tz="America/New_York").tz_convert("UTC")


def bar(i, c, h=None, l=None, complete=True):
    return SimpleNamespace(
        timestamp_utc=T + pd.Timedelta(minutes=5 * i),
        open=D(str(c)),
        high=D(str(h if h is not None else c + 1)),
        low=D(str(l if l is not None else c - 1)),
        close=D(str(c)),
        is_complete_5m=complete,
    )


def ready():
    d = Detector(D(100), D(90), T + pd.Timedelta(minutes=15))
    for i in range(3):
        assert d.update(bar(i, 95)) is None
    return d


@pytest.mark.parametrize(
    "c,direction,stop", [(101, "LONG", D(94)), (89, "SHORT", D(96))]
)
def test_first_post_opening_break(c, direction, stop):
    d = ready()
    s = d.update(bar(3, c))
    assert s["direction"] == direction
    assert s["entry_time_utc"] == T + pd.Timedelta(minutes=20)
    v = bracket(s, 1)
    assert v["stop_price"] == stop
    assert abs(v["target_price"] - v["entry_price"]) == 50


def test_wick_and_equal_close_do_not_break():
    d = ready()
    assert d.update(bar(3, 100, 105, 94)) is None
    assert d.update(bar(4, 101))["direction"] == "LONG"


def test_repeat_requires_strict_return_inside_not_equal():
    d = ready()
    assert d.update(bar(3, 101))
    assert d.update(bar(4, 102)) is None
    assert d.update(bar(5, 100)) is None
    assert d.update(bar(6, 101)) is None
    assert d.update(bar(7, 99)) is None
    assert d.update(bar(8, 101))["breakout_number"] == 2


def test_missing_bar_break_cannot_bridge():
    d = ready()
    assert d.update(bar(4, 101)) is None
    assert d.update(bar(5, 99)) is None
    assert d.update(bar(6, 101))


def test_incomplete_clears_arms_and_previous():
    d = ready()
    assert d.update(bar(3, 99, complete=False)) is None
    assert d.update(bar(4, 101)) is None
    assert d.update(bar(5, 99)) is None
    assert d.update(bar(6, 101))


def test_confirmation_and_busy_boundary():
    end = T + pd.Timedelta(hours=6, minutes=30)
    assert (
        selection_reason(T, end, T + pd.Timedelta(minutes=1), D(10)) == "POSITION_OPEN"
    )
    assert selection_reason(T, end, T, D(10)) is None
    assert selection_reason(end, end, None, D(10)) == "AT_SESSION_CLOSE"
    assert selection_reason(T, end, None, D(0)) == "NON_POSITIVE_RISK"


def test_skipped_signal_not_deferred():
    d = ready()
    s = d.update(bar(3, 101))
    assert s
    assert d.update(bar(4, 102)) is None


def test_time_buckets_use_actual_confirmation():
    assert (
        bucket(pd.Timestamp("2020-03-09 10:00", tz="America/New_York")) == "10:00–10:29"
    )


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
@pytest.mark.parametrize("ticks", [0, 1, 2])
def test_native_fixed_fifty_point_target_and_costs(direction, ticks):
    sign = D(1) if direction == "LONG" else D(-1)
    s = dict(
        direction=direction, close=D(100), previous_low=D(97), previous_high=D(107)
    )
    b = bracket(s, ticks)
    at = T + pd.Timedelta(minutes=20)
    target = b["target_price"]
    frame = pd.DataFrame(
        [
            dict(open=D(100), high=D(1000), low=D(0), close=D(100), volume=1),
            dict(
                open=b["entry_price"],
                high=target if sign == 1 else b["entry_price"],
                low=target if sign == -1 else b["entry_price"],
                close=target,
                volume=1,
            ),
        ],
        index=[at - pd.Timedelta(minutes=1), at],
    )
    record = dict(
        **s,
        **b,
        entry_time_utc=at,
        entry_time_ny=at.tz_convert("America/New_York"),
        signal_id="test"
    )
    trade, _ = execute(
        record,
        frame,
        ref.Config(D(".73"), ticks),
        1,
        Entry(direction, b["stop_price"], b["target_r"]),
        None,
        {},
        {},
        at + pd.Timedelta(minutes=1),
    )
    assert trade["exit_reason"] == "TARGET"
    assert trade["net_pnl_usd"] == D(100) - D(".5") * ticks - D("1.46")
    assert (
        trade["final_stop_price"] == b["stop_price"]
        and trade["management_event_count"] == 0
    )


@pytest.mark.parametrize("mirror", [False, True])
def test_independent_vector_reconciliation_includes_equal_and_missing(mirror):
    from scripts.opening15_breakout.core import independent_signals

    prices = [
        95,
        95,
        95,
        101,
        100,
        101,
        99,
        100,
        101,
        95,
        89,
        90,
        89,
        91,
        89,
        95,
        101,
        99,
        101,
    ]
    if mirror:
        prices = [190 - v for v in prices]
    rows = [bar(i, c, complete=i != 9) for i, c in enumerate(prices) if i != 16]
    d = Detector(D(100), D(90), T + pd.Timedelta(minutes=15))
    observed = []
    for r in rows:
        s = d.update(r)
        if s:
            observed.append((s["entry_time_utc"], s["direction"]))
    frame = pd.DataFrame([vars(r) for r in rows])
    assert sorted(observed) == independent_signals(
        frame, D(100), D(90), T + pd.Timedelta(minutes=15)
    )


def test_date_cluster_bootstrap_is_deterministic():
    from scripts.opening15_breakout.report import cluster_intervals

    g = pd.DataFrame(
        dict(
            date=["2020-01-02", "2020-01-02", "2020-01-03"],
            signal_id=["a", "b", "c"],
            result_r=[1.0, 1.0, -1.0],
            net_pnl_usd=[5.0, 5.0, -8.0],
        )
    )
    assert cluster_intervals(g) == cluster_intervals(g)
    assert cluster_intervals(g)["mean_r_ci_low"] == -1
