from types import SimpleNamespace
from decimal import Decimal as D
import pandas as pd
import pytest
from scripts.eight_level_study.core import Opening15, Entries
from scripts.eight_level_study.label import measures
from engine.research.outcomes import PreparedMinutes

T = pd.Timestamp("2020-03-09 09:30", tz="America/New_York").tz_convert("UTC")
SESSION = (T, T + pd.Timedelta(hours=6, minutes=30))


def b(i=0, o=99, h=102, l=98, c=101, complete=True):
    return SimpleNamespace(
        timestamp_utc=T + pd.Timedelta(minutes=5 * i),
        open=D(o),
        high=D(h),
        low=D(l),
        close=D(c),
        is_complete_5m=complete,
    )


def ev(kind="BREAK_ACCEPTANCE", i=0, **kw):
    return dict(
        event_id=f"{kind}{i}",
        root_event_id=None,
        interaction_type=kind,
        level_id="level",
        level_type="PDH",
        level_price="100",
        level_available_at=T,
        approach_side="BELOW",
        touch_number=1,
        direction="UP",
        timestamp_utc=T + pd.Timedelta(minutes=5 * (i + 1)),
        high="102",
        low="98",
        **kw,
    )


def test_opening15_exact_wicks_and_availability():
    x = Opening15({"2020-03-09": SESSION})
    for i in range(3):
        x.update(b(i, h=102 + i, l=98 - i))
        assert not x.active(T + pd.Timedelta(minutes=14))
    assert {
        l.level_type: float(l.price) for l in x.active(T + pd.Timedelta(minutes=15))
    } == {"O15H": 104, "O15L": 96}
    x.update(b(3, h=150, l=50))
    assert float(x.levels[0].price) == 104


@pytest.mark.parametrize("rows", [[b(0), b(2)], [b(0), b(1, complete=False), b(2)]])
def test_incomplete_opening15_unavailable(rows):
    x = Opening15({"2020-03-09": SESSION})
    for r in rows:
        x.update(r)
    assert not x.levels


def test_break_close_kept_without_future_success():
    x = Entries()
    r = x.update(b(), [ev()], {}, SESSION)
    assert [e["entry_kind"] for e in r] == ["BREAK_CLOSE"]
    assert not x.update(b(1, o=101, h=102, l=97, c=98), [], {}, SESSION)


def test_first_full_without_retest():
    x = Entries()
    x.update(b(), [ev()], {}, SESSION)
    r = x.update(b(1, o=102, h=105, l=101, c=104), [], {}, SESSION)
    assert [e["entry_kind"] for e in r] == ["BREAK_FIRST_FULL"]
    assert not x.update(b(2, o=102, h=105, l=101, c=104), [], {}, SESSION)


def test_touch_cancels_direct_departure():
    x = Entries()
    x.update(b(), [ev()], {}, SESSION)
    x.update(b(1, o=102, h=105, l=100, c=104), [], {}, SESSION)
    assert not x.update(b(2, o=102, h=105, l=101, c=104), [], {}, SESSION)


def test_failure_direction_is_reversed_and_adjacent_confirm():
    x = Entries()
    e = ev("BREAK_FAILED_NEXT_CANDLE_HOLD")
    e["root_event_id"] = "root"
    e["low"] = "97"
    r = x.update(b(c=98), [e], {}, SESSION)
    assert r[0]["direction"] == "DOWN"
    r = x.update(b(1, o=98, h=99, l=95, c=96), [], {}, SESSION)
    assert (
        r[0]["entry_kind"] == "FAILED_BREAK_CONFIRMATION" and r[0]["root_id"] == "root"
    )


def test_missing_bar_cancels_pending_confirmation():
    x = Entries()
    x.update(b(), [ev("BREAK_FAILED_NEXT_CANDLE_HOLD")], {}, SESSION)
    assert not x.update(b(2, o=98, h=99, l=95, c=96), [], {}, SESSION)


def test_retest_range_excludes_escape_candle():
    x = Entries()
    e = ev("BREAK_RETEST_HOLD")
    e["root_event_id"] = "break"
    x.update(b(), [e], {}, SESSION)
    x.update(b(1, o=101, h=104, l=100, c=103), [], {}, SESSION)
    r = x.update(b(2, o=103, h=106, l=102, c=105), [], {}, SESSION)
    assert r[0]["entry_kind"] == "RETEST_RANGE_ESCAPE" and r[0]["root_id"] == "break"


def test_rejection_uses_approach_side():
    x = Entries()
    r = x.update(b(), [ev("REJECTION")], {}, SESSION)
    assert r[0]["direction"] == "DOWN"


def test_forward_does_not_include_signal_and_censors_close():
    at = T + pd.Timedelta(minutes=5)
    raw = pd.DataFrame(
        dict(
            open=[100] * 11,
            high=[200] + [125] * 10,
            low=[0] + [95] * 10,
            close=[100] * 11,
        ),
        index=pd.date_range(at - pd.Timedelta(minutes=1), periods=11, freq="min"),
    )
    o = dict(
        event_id="x",
        timestamp_utc=at,
        session_close=at + pd.Timedelta(minutes=10),
        price_at_event=100,
        atr14=None,
    )
    m = {x["horizon"]: x for x in measures(o, PreparedMinutes(raw))}
    assert (
        m["5"]["up_excursion"] == 25
        and m["5"]["up_hit_25"] == 1
        and m["5"]["up_atr_1"] is None
    )
    assert not m["30"]["complete"] and m["30"]["censor_reason"] == "OUTSIDE_SESSION"
    assert m["session_close"]["complete"]


def test_missing_owned_minute_censors_only_affected_horizons():
    raw = pd.DataFrame(
        dict(open=100, high=101, low=99, close=100),
        index=pd.date_range(T, periods=60, freq="min"),
    ).drop(T + pd.Timedelta(minutes=8))
    o = dict(
        event_id="x",
        timestamp_utc=T,
        session_close=T + pd.Timedelta(minutes=60),
        price_at_event=100,
        atr14=1,
    )
    m = {x["horizon"]: x for x in measures(o, PreparedMinutes(raw))}
    assert m["5"]["complete"] and m["10"]["censor_reason"] == "MISSING_MINUTES"
