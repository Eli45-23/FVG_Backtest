from dataclasses import FrozenInstanceError, replace
from decimal import Decimal as D
from types import SimpleNamespace
import sys
import pandas as pd
import pytest
from engine.legacy import ROOT, reference as ref
from engine.managed import execute
from engine.strategy import Bar, MoveStop, ManagementContext, StopChange
from engine.strategy.loading import load
from engine.canonical import digest

sys.path.insert(0, str(ROOT / "outputs/tests"))
from test_cont_a import signal, minutes


def setup(direction="LONG"):
    s = signal("bullish" if direction == "LONG" else "bearish")
    s.update(
        entry_price=D(200),
        stop_price=D(100) if direction == "LONG" else D(300),
        target_price=D(400) if direction == "LONG" else D(0),
        risk_points=D(100),
        risk_usd=D(200),
    )
    return s


def manager(fn):
    return SimpleNamespace(manage=fn)


def rstep():
    return load((ROOT / "strategies/builtins/cont_a_rstep.py").read_text())[0]


def run(s, px, m=None, bars=None):
    return execute(s, minutes(s, px), ref.Config(), m or rstep(), {}, bars or {})


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_touch_next_minute_activation(direction):
    s = setup(direction)
    px = (
        [[200, 251, 195, 245], [210, 220, 204, 210]]
        if direction == "LONG"
        else [[200, 205, 149, 155], [190, 196, 180, 190]]
    )
    t, ev = run(s, px)
    assert t["exit_price"] == D(205 if direction == "LONG" else 195)
    assert (
        t["duration_1m_bars"] == 2
    )  # trigger minute crossed new stop but did not own it yet
    assert ev[0]["activation_timestamp"] == s["entry_time_utc"] + ref.ONE
    assert ev[0]["timestamp"] == ev[0]["activation_timestamp"]
    assert ev[0]["effective_stop"] == t["final_stop_price"]
    assert ev[0]["trade_id"] == t["trade_id"]
    assert t["target_price"] == s["target_price"] and t["stop_price"] == s["stop_price"]
    assert t["management_exit"]


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_exit_wins_before_touch(direction):
    s = setup(direction)
    px = [[200, 260, 90, 220]] if direction == "LONG" else [[200, 310, 140, 180]]
    t, ev = run(s, px)
    assert ev == []
    assert t["exit_reason"] == "STOP"


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_same_minute_conflict_and_gap(direction):
    s = setup(direction)
    px = [[90, 410, 80, 210]] if direction == "LONG" else [[310, 320, -10, 200]]
    t, ev = run(s, px)
    assert t["same_minute_stop_target_conflict"]
    assert t["exit_price"] == D(90 if direction == "LONG" else 310)
    assert not ev


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_monotonic_and_tick_rounding(direction):
    s = setup(direction)
    price = D("205.12") if direction == "LONG" else D("194.88")
    px = (
        [[200, 251, 195, 245], [210, 220, 190, 210]]
        if direction == "LONG"
        else [[200, 205, 149, 155], [190, 200, 180, 190]]
    )
    t, ev = run(s, px, manager(lambda c, p: MoveStop(price)))
    assert ev[0]["effective_stop"] % D(".25") == 0
    assert ev[0]["effective_stop"] == D(205 if direction == "LONG" else 195)


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_loosen_rejected(direction):
    s = setup(direction)
    price = s["stop_price"] - D(1) if direction == "LONG" else s["stop_price"] + D(1)
    with pytest.raises(ValueError, match="loosen"):
        run(s, [[200, 210, 190, 200]], manager(lambda c, p: MoveStop(price)))


@pytest.mark.parametrize("price", [D("NaN"), D("Infinity"), D(400)])
def test_invalid_stop(price):
    with pytest.raises(ValueError, match="stop"):
        run(setup(), [[200, 210, 190, 200]], manager(lambda c, p: MoveStop(price)))


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_simultaneous_most_protective(direction):
    s = setup(direction)
    vals = [205, 225, 215] if direction == "LONG" else [195, 175, 185]
    px = (
        [[200, 250, 195, 245], [230, 240, 220, 230]]
        if direction == "LONG"
        else [[200, 205, 150, 155], [170, 180, 160, 170]]
    )
    t, ev = run(s, px, manager(lambda c, p: [MoveStop(D(v)) for v in vals]))
    assert len(ev) == 1
    assert ev[0]["effective_stop"] == D(225 if direction == "LONG" else 175)


def ctx(direction="LONG", low=301, high=310):
    s = setup(direction)
    at = s["entry_time_utc"] + ref.FIVE * 2
    bar = Bar(at - ref.FIVE, D(low), D(high), D(low), D(high))
    history = (
        StopChange(
            s["entry_time_utc"] + ref.ONE,
            s["entry_time_utc"] + ref.ONE,
            s["stop_price"],
            D(205 if direction == "LONG" else 195),
            "touch",
        ),
    )
    return ManagementContext(
        at,
        "bar_5m_close",
        s["entry_time_utc"],
        s["entry_price"],
        s["stop_price"],
        history[0].effective_stop,
        s["target_price"],
        direction,
        s["risk_points"],
        D(199),
        D(5),
        bar,
        bar,
        history,
    )


@pytest.mark.parametrize(
    "direction,low,high,holds",
    [
        ("LONG", 301, 310, True),
        ("LONG", 300, 310, False),
        ("LONG", 299, 310, False),
        ("SHORT", 90, 99, True),
        ("SHORT", 90, 100, False),
        ("SHORT", 90, 101, False),
    ],
)
def test_strict_whole_hold(direction, low, high, holds):
    c = ctx(direction, low, high)
    assert c.completed_bar_holds_beyond_r(1) == holds
    assert not replace(c, completed_bar=None).completed_bar_holds_beyond_r(1)


@pytest.mark.parametrize(
    "direction,threshold,locked",
    [
        ("LONG", "1", "1"),
        ("LONG", "1.5", "1.25"),
        ("LONG", "1.75", "1.5"),
        ("SHORT", "1", "1"),
        ("SHORT", "1.5", "1.25"),
        ("SHORT", "1.75", "1.5"),
    ],
)
def test_rstep_levels(direction, threshold, locked):
    c = ctx(direction)
    level = c.price_at_r(threshold)
    c = replace(
        c,
        completed_bar=(
            replace(c.completed_bar, low=level + D(".25"), high=level + D(1))
            if direction == "LONG"
            else replace(c.completed_bar, low=level - D(1), high=level - D(".25"))
        ),
    )
    requests = rstep().manage(c, {})
    assert max(
        requests, key=lambda x: x.price * c.direction_sign
    ).price == c.price_at_r(locked)


def test_later_full_bar_required():
    c = ctx()
    c = replace(c, completed_bar=replace(c.completed_bar, timestamp=c.entry_time))
    assert rstep().manage(c, {}) is None


def test_confirmed_bar_cannot_retroact():
    s = setup()
    at = s["entry_time_utc"]
    b = Bar(at, D(200), D(250), D(195), D(245))
    seen = []

    def manage(c, p):
        seen.append((c.timestamp, c.event))
        return MoveStop(D(225)) if c.completed_bar else None

    t, ev = run(
        s, [[200, 250, 195, 245]] * 5 + [[230, 240, 220, 230]], manager(manage), {at: b}
    )
    assert len(ev) == 1 and ev[0]["activation_timestamp"] == at + ref.FIVE
    assert t["duration_1m_bars"] == 6
    assert [time for time, event in seen if event == "bar_5m_close"] == [at + ref.FIVE]


def test_no_complete_bar_no_callback():
    s = setup()
    seen = []

    def manage(c, p):
        seen.append(c.event)

    t, ev = run(s, [[200, 250, 195, 245]] * 5 + [[200, 210, 90, 100]], manager(manage))
    assert "bar_5m_close" not in seen and ev == []


def test_session_close_unchanged():
    s = setup()
    s["entry_time_utc"] = pd.Timestamp("2024-02-05T20:59Z")
    s["entry_time_ny"] = s["entry_time_utc"].tz_convert("America/New_York")
    t, ev = run(s, [[200, 251, 195, 245]])
    assert t["exit_reason"] == "SESSION_CLOSE" and t["exit_price"] == 245 and not ev


def test_context_immutable():
    c = ctx()
    with pytest.raises(FrozenInstanceError):
        c.current_stop = D(999)
    with pytest.raises(FrozenInstanceError):
        c.completed_bar.low = D(999)
    assert not hasattr(c, "data")
    assert c.price_at_r("1.25") == 325
    assert c.reached_r("1.5")
    assert c.minutes_since_entry == 10


def test_noop_matches_legacy_and_repeat():
    s = setup()
    px = [[200, 220, 195, 210], [210, 410, 200, 400]]
    a, e = run(s, px, manager(lambda c, p: None))
    b = ref.execute(s, minutes(s, px), ref.Config())
    assert all(a[k] == v for k, v in b.items())
    assert not e
    assert digest(run(s, px)) == digest(run(s, px))


def test_callback_failure():
    def fail(c, p):
        raise RuntimeError("bad policy")

    with pytest.raises(ValueError, match="Management callback failed"):
        run(setup(), [[200, 210, 190, 200]], manager(fail))
