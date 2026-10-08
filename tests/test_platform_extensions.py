from decimal import Decimal as D
from types import SimpleNamespace as Row
import pandas as pd
import pytest
from engine.strategy import Bar, Entry, MoveStop
from engine.position import PositionPlan, TargetLeg
from engine.partial_execution import execute
from engine.research.structure import Structure, StructureConfig
from engine.research.indicators import Indicators, IndicatorConfig
from engine.research.zones import DisplacementBaseZoneDetectorV1, ZoneConfig
from engine.research.statistics import clustered, StatisticsConfig, benjamini_hochberg
from engine.timeframes import aggregate, FrameConfig
from engine.legacy import reference as ref

BASE = pd.Timestamp("2020-01-06 14:30", tz="UTC")


def bar(i, o=100, h=102, l=98, c=101):
    return Bar(BASE + pd.Timedelta(minutes=5 * i), D(o), D(h), D(l), D(c), 10)


def minute_frame(rows):
    return pd.DataFrame(
        [
            dict(
                ts_event=BASE + pd.Timedelta(minutes=i),
                open=D(o),
                high=D(h),
                low=D(l),
                close=D(c),
                volume=1,
            )
            for i, (o, h, l, c) in enumerate(rows)
        ]
    ).set_index("ts_event", drop=False)


def signal(direction="LONG"):
    ny = BASE.tz_convert("America/New_York")
    stop = D(90) if direction == "LONG" else D(110)
    return dict(
        signal_id="synthetic",
        direction=direction,
        entry_price=D(100),
        stop_price=stop,
        target_price=D(120) if direction == "LONG" else D(80),
        risk_points=D(10),
        entry_time_utc=BASE,
        entry_time_ny=ny,
    )


def sim(rows, plan=None, quantity=2, commission="0", manager=None):
    return execute(
        signal(),
        minute_frame(rows),
        ref.Config(D(commission), 0),
        quantity,
        plan
        or PositionPlan(
            "LONG",
            D(90),
            legs=(TargetLeg(1, D(1), "tp1"), TargetLeg(1, D(2), "tp2")),
            break_even_after_tp1=True,
        ),
        manager,
        {},
        {},
        BASE + pd.Timedelta(minutes=len(rows)),
    )


def test_tp1_then_be_next_minute():
    t, e = sim([(100, 111, 95, 109), (109, 110, 99, 101)])
    assert [f["exit_price"] for f in t["partial_execution_history"]] == [D(110), D(100)]
    assert (
        t["net_pnl_usd"] == 20
        and t["remaining_quantity"] == 0
        and e[0]["activation_timestamp"] == BASE + ref.ONE
    )


def test_stop_wins_all_same_minute_targets():
    t, e = sim([(100, 125, 89, 101)])
    assert (
        len(t["partial_execution_history"]) == 1
        and t["net_pnl_usd"] == -40
        and t["same_minute_stop_target_conflict"]
    )


def test_same_minute_targets_before_new_be():
    t, e = sim([(100, 125, 95, 120)])
    assert t["net_pnl_usd"] == 60 and not e


def test_runner_session_close_costs():
    p = PositionPlan(
        "LONG", D(90), legs=(TargetLeg(1, D(1)), TargetLeg(1, None, "runner"))
    )
    t, e = sim([(100, 111, 95, 108), (108, 109, 105, 106)], p, commission="1")
    assert (
        t["exit_reason"] == "SESSION_CLOSE"
        and t["net_pnl_usd"] == 28
        and t["commission_usd"] == 4
    )


def test_quantity_mismatch():
    with pytest.raises(ValueError):
        sim([(100, 101, 99, 100)], quantity=3)


def test_missing_minute_fails():
    frame = minute_frame([(100, 101, 99, 100), (100, 101, 99, 100)]).iloc[1:]
    with pytest.raises(ValueError, match="Missing"):
        execute(
            signal(),
            frame,
            ref.Config(),
            1,
            Entry("LONG", D(90)),
            None,
            {},
            {},
            BASE + pd.Timedelta(minutes=2),
        )


def test_indicator_prefix():
    a = Indicators()
    b = Indicators()
    prefix = [bar(i, c=100 + i, h=102 + i, l=98 + i, o=100 + i) for i in range(20)]
    av = [a.update(r, r.timestamp) for r in prefix]
    bv = [b.update(r, r.timestamp) for r in prefix + [bar(20, h=10000, c=9000)]]
    assert av == bv[:20] and av[0]["vwap"] is not None and av[-1]["atr14"] is not None


def test_pivot_delayed_and_strict():
    s = Structure(StructureConfig(1, 1))
    a = bar(0, h=101)
    p = bar(1, h=110)
    c = bar(2, h=102)
    assert not s.update(a, a.timestamp + ref.FIVE)
    assert not s.update(p, p.timestamp + ref.FIVE)
    events = s.update(c, c.timestamp + ref.FIVE)
    high = next(e for e in events if e["event_type"] == "SWING_HIGH")
    assert (
        high["formation_timestamp"] == p.timestamp
        and high["availability_timestamp"] == c.timestamp + ref.FIVE
    )


def test_structure_bos_choch():
    s = Structure()
    s.high = {"id": "h", "price": 105}
    s.low = {"id": "l", "price": 95}
    s.state = "BULLISH"
    assert (
        s.update(bar(0, h=107, c=106), BASE + ref.FIVE)[0]["event_type"]
        == "BULLISH_BOS"
    )
    assert (
        s.update(bar(1, l=90, c=94), BASE + 2 * ref.FIVE)[0]["event_type"]
        == "BEARISH_CHOCH"
    )


def test_zone_departure_availability_and_invalidation():
    z = DisplacementBaseZoneDetectorV1(ZoneConfig(base_max=1, min_displacement_atr=1))
    assert not z.update(bar(0, o=100, c=100, h=101, l=99), BASE + ref.FIVE, 3)
    new = z.update(bar(1, o=101, h=110, l=100, c=108), BASE + 2 * ref.FIVE, 3)
    assert new and new[0]["availability_timestamp"] == BASE + 2 * ref.FIVE
    z.update(bar(2, o=100, h=102, l=95, c=96), BASE + 3 * ref.FIVE, 3)
    assert z.zones[0]["status"] == "invalidated" and z.zones[0]["touch_count"] == 1


def test_cluster_repetition_and_determinism():
    dates = ["a", "a", "b", "b"]
    y = [1, 1, 0, 0]
    base = [0.5] * 4
    cfg = StatisticsConfig(iterations=100)
    a = clustered(dates, y, base, cfg)
    b = clustered(dates * 2, y * 2, base * 2, cfg)
    assert (
        a["effect"] == b["effect"] and a["ci95"] == b["ci95"] and a["unique_dates"] == 2
    )
    assert a == clustered(dates, y, base, cfg)


def test_bh():
    assert benjamini_hochberg([0.01, 0.04, 0.03, None]) == [0.03, 0.04, 0.04, None]


@pytest.mark.parametrize("tf,count", [("1m", 1), ("5m", 5), ("15m", 15), ("4h", 240)])
def test_timeframe_confirmation(tf, count):
    at = pd.Timestamp("2020-01-06", tz="UTC")
    raw = pd.DataFrame(
        dict(
            ts_event=pd.date_range(at, periods=count, freq="min"),
            open=100_000_000_000,
            high=102_000_000_000,
            low=99_000_000_000,
            close=101_000_000_000,
            volume=1,
        )
    )
    r = aggregate(raw, tf).iloc[0]
    assert r.is_complete_5m and r.availability_timestamp == at + pd.Timedelta(
        minutes=count
    )
    if count > 1:
        assert not aggregate(raw.iloc[1:], tf).iloc[0].is_complete_5m


@pytest.mark.parametrize("day", ["2020-03-09", "2020-11-02"])
def test_ny_anchor_dst(day):
    at = pd.Timestamp(day + " 09:30", tz="America/New_York").tz_convert("UTC")
    raw = pd.DataFrame(
        dict(
            ts_event=pd.date_range(at, periods=240, freq="min"),
            open=100_000_000_000,
            high=102_000_000_000,
            low=99_000_000_000,
            close=101_000_000_000,
            volume=1,
        )
    )
    r = aggregate(raw, "4h", FrameConfig("09:30", "America/New_York", "rth")).iloc[0]
    assert r.is_complete_5m and r.timestamp_ny.strftime("%H:%M") == "09:30"
    assert (
        r.availability_timestamp.tz_convert("America/New_York").strftime("%H:%M")
        == "13:30"
    )


def test_halfday_4h_is_incomplete():
    at = pd.Timestamp("2020-11-27 09:30", tz="America/New_York").tz_convert("UTC")
    raw = pd.DataFrame(
        dict(
            ts_event=pd.date_range(at, periods=390, freq="min"),
            open=100_000_000_000,
            high=102_000_000_000,
            low=99_000_000_000,
            close=101_000_000_000,
            volume=1,
        )
    )
    result = aggregate(raw, "4h", FrameConfig("09:30", "America/New_York", "rth"))
    assert (
        len(result) == 1
        and result.iloc[0].minute_count == 210
        and not result.iloc[0].is_complete_5m
    )


@pytest.mark.parametrize(
    "state,direction,high,low,close,expected",
    [
        ("BEARISH", "UP", 110, 99, 106, "BULLISH_CHOCH"),
        ("BEARISH", "DOWN", 101, 90, 94, "BEARISH_BOS"),
    ],
)
def test_opposite_structure_states(state, direction, high, low, close, expected):
    s = Structure()
    s.high = {"id": "h", "price": 105}
    s.low = {"id": "l", "price": 95}
    s.state = state
    assert (
        s.update(bar(0, h=high, l=low, c=close), BASE + ref.FIVE)[0]["event_type"]
        == expected
    )


@pytest.mark.parametrize(
    "kind,prices,progression",
    [
        ("HIGH", [105, 110], "HH"),
        ("HIGH", [110, 105], "LH"),
        ("LOW", [95, 96], "HL"),
        ("LOW", [96, 95], "LL"),
    ],
)
def test_swing_progression(kind, prices, progression):
    s = Structure(StructureConfig(1, 1))
    idx = 0
    for price in prices:
        for value in [None, price, None]:
            b = bar(
                idx,
                h=value if kind == "HIGH" and value else 102,
                l=value if kind == "LOW" and value else 98,
            )
            s.update(b, b.timestamp + ref.FIVE)
            idx += 1
    assert s.progression[kind] == progression


def test_runner_management_only_activates_after_confirmation():
    class Manager:
        def manage(self, ctx, params):
            assert ctx.initial_quantity == 2
            if ctx.remaining_quantity == 1 and ctx.current_stop < D(103):
                assert len(ctx.partial_fills) == 1
                return MoveStop(D(103), "Runner structural request")

    plan = PositionPlan(
        "LONG", D(90), legs=(TargetLeg(1, D(1), "TP1"), TargetLeg(1, None, "runner"))
    )
    trade, events = sim(
        [(100, 111, 95, 109), (109, 110, 102, 104)], plan, manager=Manager()
    )
    assert (
        trade["net_pnl_usd"] == 26
        and events[0]["activation_timestamp"] == BASE + ref.ONE
    )


def test_vwap_missing_contribution_is_unavailable():
    indicator = Indicators()
    assert indicator.update(bar(0), BASE)["vwap"] is not None
    indicator.update(bar(1), BASE + ref.FIVE, complete=False)
    result = indicator.update(bar(2), BASE + 2 * ref.FIVE)
    assert result["vwap"] is None and not result["vwap_complete"]
