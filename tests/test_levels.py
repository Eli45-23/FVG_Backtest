from types import SimpleNamespace as Row
from decimal import Decimal as D
import pandas as pd
import pytest
from engine.research.levels import (
    LevelEngine,
    Level,
    SessionConfig,
    Zone,
    FIVE,
    NY,
    schedule,
)
from engine.research.events import EventDetector
from engine.research.outcomes import label, directional
from engine.research.profiles import profile, validate_segment
from engine.research.analysis import describe


def bar(t, o=100, h=105, l=95, c=101, complete=True):
    at = pd.Timestamp(t, tz=NY).tz_convert("UTC") if isinstance(t, str) else t
    return Row(
        timestamp_utc=at,
        open=D(str(o)),
        high=D(str(h)),
        low=D(str(l)),
        close=D(str(c)),
        is_complete_5m=complete,
    )


def session(day, end="16:00"):
    return tuple(
        pd.Timestamp(f"{day} {t}", tz=NY).tz_convert("UTC") for t in ["09:30", end]
    )


def feed_day(e, day, end="16:00", omit=None, incomplete=None):
    op, cl = session(day, end)
    for i, t in enumerate(pd.date_range(op, cl, freq="5min", inclusive="left")):
        if i != omit:
            e.update(bar(t, h=110, l=90, complete=i != incomplete))


def test_prior_completed_no_lookahead():
    sessions = {d: session(d) for d in ["2024-01-02", "2024-01-03"]}
    e = LevelEngine(sessions=sessions)
    feed_day(e, "2024-01-02")
    e.update(bar("2024-01-03 09:30", h=1000, l=1))
    levels = {
        l.level_type: l for l in e.active(pd.Timestamp("2024-01-03 09:30", tz=NY))
    }
    assert levels["PDH"].price == 110 and levels["PDL"].price == 90
    assert levels["PDH"].source_date == "2024-01-02"
    assert "O5H" not in levels


@pytest.mark.parametrize("kind", ["missing", "incomplete"])
def test_prior_bad_session_not_used(kind):
    e = LevelEngine(sessions={d: session(d) for d in ["2024-01-02", "2024-01-03"]})
    feed_day(
        e,
        "2024-01-02",
        omit=5 if kind == "missing" else None,
        incomplete=5 if kind == "incomplete" else None,
    )
    e.update(bar("2024-01-03 09:30"))
    assert not any(l.level_type == "PDH" for l in e.levels)


def test_no_stale_previous_session():
    e = LevelEngine(
        sessions={d: session(d) for d in ["2024-01-02", "2024-01-03", "2024-01-04"]}
    )
    feed_day(e, "2024-01-02")
    e.update(bar("2024-01-04 09:30"))
    assert not any(l.level_type == "PDH" for l in e.levels)


def test_early_close_prior_valid():
    e = LevelEngine(
        sessions={
            "2024-07-03": session("2024-07-03", "13:00"),
            "2024-07-05": session("2024-07-05"),
        }
    )
    feed_day(e, "2024-07-03", "13:00")
    e.update(bar("2024-07-05 09:30"))
    assert next(l for l in e.levels if l.level_type == "PDH").price == 110


def test_actual_calendar_holiday_early_close_dst():
    s = schedule()
    assert "2024-07-04" not in s
    assert s["2024-07-03"][1].tz_convert(NY).hour == 13
    assert s["2024-03-08"][0].hour == 14 and s["2024-03-11"][0].hour == 13


def test_o5_timing():
    e = LevelEngine(sessions={"2024-01-02": session("2024-01-02")})
    e.update(bar("2024-01-02 09:30"))
    assert not e.active(pd.Timestamp("2024-01-02 09:34", tz=NY))
    assert len(e.active(pd.Timestamp("2024-01-02 09:35", tz=NY))) == 2


def test_o5_missing_source_not_synthesized():
    e = LevelEngine(sessions={"2024-01-02": session("2024-01-02")})
    e.update(bar("2024-01-02 09:35"))
    assert not e.levels


@pytest.mark.parametrize("missing", [True, False])
def test_premarket_confirmation(missing):
    e = LevelEngine(
        SessionConfig("09:00", "09:30"), sessions={"2024-01-02": session("2024-01-02")}
    )
    for i in range(6):
        if missing and i == 2:
            continue
        e.update(bar(f"2024-01-02 09:{i*5:02}"))
        if i < 5:
            assert not e.levels
    pm = [
        l
        for l in e.active(pd.Timestamp("2024-01-02 09:30", tz=NY))
        if l.level_type.startswith("PM")
    ]
    assert len(pm) == (0 if missing else 2)
    e.update(bar("2024-01-02 09:30", h=200))
    assert all(l.price == 105 for l in e.levels if l.level_type == "PMH")


@pytest.mark.parametrize(
    "args",
    [("09:30", "09:00"), ("04:01", "09:30"), ("04:00", None), ("04:00", "10:00")],
)
def test_pm_bad_configuration(args):
    with pytest.raises(ValueError):
        SessionConfig(*args)


def test_pm_disabled():
    assert SessionConfig().premarket_start is None


def level():
    return Level(
        "a",
        "PDH",
        D(100),
        "2024-01-02",
        "2024-01-01",
        pd.Timestamp("2024-01-02 09:30", tz=NY),
        True,
        (),
    )


def classify(sequence):
    d = EventDetector(SessionConfig())
    res = []
    for r in sequence:
        res += d.update(r, [level()], session("2024-01-02"))
    return res


def test_touch_episode_numbers():
    rows = [
        bar("2024-01-02 09:30", h=99, l=95, c=98),
        bar("2024-01-02 09:35"),
        bar("2024-01-02 09:40"),
        bar("2024-01-02 09:45", h=99, l=95, c=98),
        bar("2024-01-02 09:50"),
        bar("2024-01-02 09:55", h=99, l=95, c=98),
        bar("2024-01-02 10:00"),
    ]
    assert [
        e["touch_number"] for e in classify(rows) if e["interaction_type"] == "TOUCH"
    ] == [1, 2, 3]


@pytest.mark.parametrize("side", [1, -1])
def test_sweep_mirror(side):
    r = bar("2024-01-02 09:30", o=100 + side * 2, h=104, l=96, c=100 + side)
    es = classify([r])
    assert any(e["interaction_type"] == "SWEEP_RECLAIM" for e in es)
    assert es[0]["direction"] == ("DOWN" if side == 1 else "UP")


def test_break_retest():
    es = classify(
        [
            bar("2024-01-02 09:30", o=98, h=104, l=97, c=103),
            bar("2024-01-02 09:35", o=103, h=105, l=102, c=104),
            bar("2024-01-02 09:40", o=104, h=105, l=99, c=103),
        ]
    )
    assert len([e for e in es if e["interaction_type"] == "BREAK_ACCEPTANCE"]) == 1
    assert len([e for e in es if e["interaction_type"] == "RETEST"]) == 1


def test_missing_bar_cannot_bridge_retest():
    es = classify(
        [
            bar("2024-01-02 09:30", o=98, h=104, l=97, c=103),
            bar("2024-01-02 09:45", o=104, h=105, l=99, c=103),
        ]
    )
    assert not any(e["interaction_type"] == "RETEST" for e in es)


def test_rejection_config():
    d = EventDetector(SessionConfig(rejection_clearance=10))
    es = d.update(
        bar("2024-01-02 09:30", o=103, c=103), [level()], session("2024-01-02")
    )
    assert not any(e["interaction_type"] == "REJECTION" for e in es)


def test_unavailable_level_not_detected():
    from dataclasses import replace

    d = EventDetector(SessionConfig())
    l = replace(level(), availability_timestamp=pd.Timestamp("2024-01-02 09:35", tz=NY))
    assert not d.update(bar("2024-01-02 09:30"), [l], session("2024-01-02"))


def test_causal_prefix_equivalence():
    a = [bar("2024-01-02 09:30"), bar("2024-01-02 09:35")]
    prefix = classify(a)
    extended = classify(a + [bar("2024-01-02 09:40", h=10000, l=1)])
    assert extended[: len(prefix)] == prefix


def minutes():
    index = pd.date_range(
        "2024-01-02 15:00", periods=60, freq="1min", tz=NY
    ).tz_convert("UTC")
    return pd.DataFrame(
        {"open": 100.0, "high": 130.0, "low": 80.0, "close": 110.0}, index=index
    )


def observation():
    return {
        "timestamp_utc": str(minutes().index[0]),
        "price_at_event": 100,
        "session_close": str(pd.Timestamp("2024-01-02 16:00", tz=NY)),
        "direction": "UP",
    }


def test_forward_exact_calculation():
    labels = label(observation(), minutes())
    for v in labels.values():
        assert (
            v["complete"]
            and v["mfe"] == 30
            and v["mae"] == 20
            and v["forward_close_change"] == 10
        )
        assert v["thresholds"]["up_25"] == {"reached": True, "minutes": 1}
        assert not v["thresholds"]["up_50"]["reached"]
        assert directional(v, "UP", "rejection") == (20, 30)


def test_no_pre_event_candle_excursion():
    m = minutes()
    m.loc[m.index[0] - pd.Timedelta(minutes=1)] = [100, 99999, 1, 100]
    m = m.sort_index()
    assert label(observation(), m)["5"]["mfe"] == 30


def test_missing_forward_censors():
    labels = label(observation(), minutes().drop(minutes().index[9]))
    assert labels["5"]["complete"] and not labels["10"]["complete"]


def test_forward_session_boundary():
    o = {**observation(), "timestamp_utc": str(minutes().index[-5])}
    r = label(o, minutes())
    assert (
        r["5"]["complete"]
        and not r["10"]["complete"]
        and r["session_close"]["complete"]
    )


def test_bad_forward_ohlc():
    m = minutes()
    m.iloc[1, m.columns.get_loc("high")] = 1
    assert label(observation(), m)["5"]["censor_reason"] == "INVALID_OHLC"


def test_profiles_do_not_extend_legacy():
    with pytest.raises(ValueError):
        profile("legacy_2024_2026").validate("2020-01-01", "2021-01-01")
    profile("research_2020_2026").validate("2020-01-01", "2021-01-01")


@pytest.mark.parametrize(
    "seg,start,end",
    [
        ("development", "2023-12-31", "2024-01-02"),
        ("validation", "2025-01-01", "2025-01-02"),
        ("development", "2025-01-01", "2025-01-02"),
    ],
)
def test_segment_cannot_mislabel_oos(seg, start, end):
    with pytest.raises(ValueError):
        validate_segment("research_2020_2026", seg, start, end)


def test_zone_is_structure_only():
    t = pd.Timestamp("2024-01-02", tz="UTC")
    z = Zone("a", "supply", D(110), D(100), t, t, "4h")
    assert z.status == "active"
    with pytest.raises(ValueError):
        Zone("a", "supply", D(90), D(100), t, t, "4h")


def test_baseline_matching_not_global():
    e = {"event_id": "e", "direction": "UP", "year": 2024, "time_bucket": "10:00"}
    b = {**e, "event_id": "b"}
    x = {**e, "event_id": "x", "year": 2025}
    lab = label(observation(), minutes())
    result = describe([e], {"e": lab}, [b, x], {"b": lab, "x": lab})
    assert result["unique_matched_baseline_observations"] == 1
    assert all(p["difference"] == 0 for p in result["probabilities"])
