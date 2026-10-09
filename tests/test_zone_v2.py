"""Frozen V2 geometry, causality, continuity and lifecycle contracts."""

from copy import deepcopy
import pandas as pd
import pytest
from engine.zone_v2.provider import (
    DisplacementBaseZoneProviderV2 as Provider,
    ProviderConfig,
)
from engine.zone_v2.lifecycle import ZoneLifecycleV2
from engine.zone_v2.frames import aggregate, with_atr, session_schedule
from engine.canonical import digest

T = pd.Timestamp("2020-01-06 23:00", tz="UTC")


def bar(i, o=100, h=105, l=95, c=101, atr=10, **kw):
    start = T + pd.Timedelta(hours=4 * i)
    return dict(
        timestamp=start,
        availability_timestamp=start + pd.Timedelta(hours=4),
        session_date=str(start.date()),
        open=o,
        high=h,
        low=l,
        close=c,
        volume=10,
        atr14=atr,
        complete=True,
        full=True,
        **kw,
    )


def formation(side="SUPPLY", count=1, incoming="RALLY"):
    p = Provider()
    prior = bar(
        0,
        o=90 if incoming == "RALLY" else 110,
        h=111,
        l=89,
        c=110 if incoming == "RALLY" else 90,
    )
    p.update(prior)
    for i in range(1, count + 1):
        p.update(bar(i))
    dep = (
        bar(count + 1, o=101, h=102, l=79, c=80)
        if side == "SUPPLY"
        else bar(count + 1, o=100, h=122, l=99, c=121)
    )
    out = p.update(dep)
    assert out
    return p, out[-1], dep


@pytest.mark.parametrize("side", ["SUPPLY", "DEMAND"])
@pytest.mark.parametrize("count", [1, 3])
def test_base_geometry_excludes_departure(side, count):
    p, z, dep = formation(side, count)
    assert z["base_count"] == count
    assert (z["top"], z["bottom"]) == ((105, 100) if side == "SUPPLY" else (101, 95))
    assert dep["timestamp"] not in z["base_timestamps"]
    assert z["availability_timestamp"] == dep["availability_timestamp"]
    assert p.available(dep["timestamp"]) == []


@pytest.mark.parametrize(
    "side,incoming,pattern",
    [
        ("SUPPLY", "RALLY", "RALLY_BASE_DROP"),
        ("SUPPLY", "DROP", "DROP_BASE_DROP"),
        ("DEMAND", "DROP", "DROP_BASE_RALLY"),
        ("DEMAND", "RALLY", "RALLY_BASE_RALLY"),
    ],
)
def test_patterns(side, incoming, pattern):
    assert formation(side, 1, incoming)[1]["pattern_type"] == pattern


@pytest.mark.parametrize(
    "base,dep",
    [
        (bar(0), bar(1, o=100, h=150, l=79, c=80)),  # weak body
        (bar(0, h=110, l=90), bar(1, o=100, h=101, l=70, c=71)),  # width
        (bar(0, o=96, c=104), bar(1, o=100, h=101, l=70, c=71)),  # body
        (bar(0, atr=None), bar(1, o=100, h=101, l=70, c=71)),  # no ATR
    ],
)
def test_disqualifications(base, dep):
    p = Provider()
    p.update(base)
    assert not p.update(dep)


def test_two_candle_confirmation():
    p = Provider()
    p.update(bar(0))
    assert not p.update(bar(1, o=101, h=102, l=94, c=95))
    z = p.update(bar(2, o=95, h=96, l=79, c=80))[-1]
    assert (
        z["departure_count"] == 2
        and z["availability_timestamp"] == bar(2)["availability_timestamp"]
    )


def test_too_late_departure_no_rescue():
    p = Provider()
    p.update(bar(0))
    p.update(bar(1, o=105, h=106, l=99, c=100))
    p.update(bar(2, o=105, h=106, l=99, c=100))
    assert p.update(bar(3, o=101, h=102, l=79, c=80)) == []


def test_maximal_immediate_base_stops_at_failure():
    p = Provider()
    p.update(bar(0, h=140, l=60))
    p.update(bar(1))
    p.update(bar(2))
    p.update(bar(3))
    z = p.update(bar(4, o=101, h=102, l=79, c=80))[-1]
    assert z["base_count"] == 3


def test_nonoverlap_not_bridged():
    p = Provider()
    p.update(bar(0, o=110, h=114, l=109, c=111))
    p.update(bar(1))
    assert p.update(bar(2, o=101, h=102, l=79, c=80))[-1]["base_count"] == 1


def test_duplicate_guard_and_determinism():
    a = formation()[0]
    b = formation()[0]
    assert digest(a.zones) == digest(b.zones)
    assert len({z["zone_id"] for z in a.zones}) == len(a.zones)
    with pytest.raises(ValueError):
        a.update(bar(2))


@pytest.mark.parametrize("field", ["complete", "full"])
def test_invalid_or_shortened_clears_sequence(field):
    p = Provider()
    p.update(bar(0))
    b = bar(1)
    b[field] = False
    p.update(b)
    assert not p.update(bar(2, o=101, h=102, l=79, c=80))


def lifecycle():
    _, z, _ = formation()
    l = ZoneLifecycleV2()
    l.add(z)
    return l, z


def minute(z, i, o=99, h=103.75, l=98, c=99):
    return dict(
        timestamp=z["availability_timestamp"] + pd.Timedelta(minutes=5 * i),
        open=o,
        high=h,
        low=l,
        close=c,
        complete=True,
    )


def test_preavailability_excluded():
    l, z = lifecycle()
    assert l.five_minute(minute(z, -1)) == []


def test_touch_penetration_rejection_confirmation():
    l, z = lifecycle()
    a = l.five_minute(minute(z, 0))
    assert {e["event_type"] for e in a} == {
        "ZONE_FIRST_TOUCH",
        "ZONE_ENTRY",
        "ZONE_25_PERCENT_PENETRATION",
        "ZONE_50_PERCENT_PENETRATION",
        "ZONE_75_PERCENT_PENETRATION",
        "ZONE_REJECTION",
    }
    a = l.five_minute(minute(z, 1, h=99, l=96, c=97))
    assert [e["event_type"] for e in a] == ["ZONE_REJECTION_CONFIRMATION"]
    assert [e["event_type"] for e in l.five_minute(minute(z, 2))][
        0
    ] == "ZONE_SECOND_TOUCH"
    l.five_minute(minute(z, 3, h=99))
    assert l.five_minute(minute(z, 4))[0]["event_type"] == "ZONE_THIRD_PLUS_TOUCH"


def test_distal_wick_does_not_invalidate():
    l, z = lifecycle()
    a = l.five_minute(minute(z, 0, h=106))
    assert {"ZONE_DISTAL_TOUCH", "ZONE_FULL_TRAVERSAL"} <= {e["event_type"] for e in a}
    assert l.states[z["zone_id"]]["active"]


def test_four_hour_invalidation_reclaim_retest():
    l, z = lifecycle()
    b = bar(3, o=101, h=108, l=99, c=107)
    assert l.four_hour(b)[0]["event_type"] == "ZONE_INVALIDATION"
    l.five_minute(minute(z, 49, o=107, h=108, l=106, c=107))
    a = l.five_minute(minute(z, 50, o=107, h=108, l=103, c=104))
    assert {"ZONE_INVALIDATION_RECLAIM", "ZONE_RETEST_AFTER_INVALIDATION"} == {
        e["event_type"] for e in a
    }


def test_boundary_equality_no_invalidation():
    l, z = lifecycle()
    assert l.four_hour(bar(3, c=105)) == []


def test_gap_flags_uncertain_lifecycle():
    l, z = lifecycle()
    l.five_minute(minute(z, 0))
    l.five_minute(minute(z, 2))
    assert l.states[z["zone_id"]]["coverage_uncertain"]


def raw_session(s):
    idx = pd.date_range(s["open"], s["close"], freq="min", inclusive="left")
    if s.get("pause_start") is not None:
        idx = idx[(idx < s["pause_start"]) | (idx >= s["pause_end"])]
    return pd.DataFrame(
        dict(
            open=100_000_000_000,
            high=105_000_000_000,
            low=95_000_000_000,
            close=101_000_000_000,
            volume=1,
        ),
        index=idx.rename("ts_event"),
    )


@pytest.mark.parametrize(
    "start,end",
    [
        ("2020-03-06", "2020-03-11"),
        ("2020-10-30", "2020-11-04"),
        ("2020-11-25", "2020-11-30"),
    ],
)
def test_weekend_dst_holiday_maintenance_atr(start, end):
    s = session_schedule(start, end)
    raw = pd.concat([raw_session(x) for x in s])
    b, extra = aggregate(raw, s)
    a = with_atr(b)
    assert b.complete.all() and extra.empty
    assert a.atr14.notna().any()
    assert not a.continuity_reset.any()
    assert all(
        t.tz_convert("America/New_York").hour == 18 for t in [x["open"] for x in s]
    )
    assert not b.loc[~b.full, "full"].any()


def test_unexpected_missing_resets_atr():
    s = session_schedule("2020-02-03", "2020-02-07")
    raw = pd.concat([raw_session(x) for x in s])
    raw = raw.drop(raw.index[-60])
    b, _ = aggregate(raw, s)
    a = with_atr(b)
    assert a.iloc[-1].continuity_reset and pd.isna(a.iloc[-1].atr14)


def test_atr_fourteen_only_and_shortened_excluded():
    a = pd.DataFrame([bar(i, atr=None) for i in range(14)])
    x = with_atr(a)
    assert x.atr14.iloc[:13].isna().all() and x.atr14.iloc[13] == 10


def test_pause_policy_changes_june_2021():
    a = session_schedule("2021-06-25", "2021-06-28")
    assert a[0]["pause_start"] is not None and a[1]["pause_start"] is None


def test_config_not_optimization_surface():
    with pytest.raises(ValueError):
        ProviderConfig(max_base_body_ratio=0.6)


def test_decimal_source_prices():
    from decimal import Decimal

    l, z = lifecycle()
    b = minute(z, 0)
    for k in ("open", "high", "low", "close"):
        b[k] = Decimal(str(b[k]))
    assert l.five_minute(b)[0]["event_type"] == "ZONE_FIRST_TOUCH"


def test_scheduled_gap_does_not_flag_missing():
    _, z, _ = formation()
    a = z["availability_timestamp"]
    expected = pd.date_range(
        a, a + pd.Timedelta(minutes=5), freq="min", inclusive="left"
    ).append(pd.date_range(a + pd.Timedelta(minutes=60), periods=5, freq="min"))
    l = ZoneLifecycleV2(expected)
    l.add(z)
    l.five_minute(minute(z, 0))
    l.five_minute(minute(z, 12))
    assert not l.states[z["zone_id"]]["coverage_uncertain"]


def test_demand_penetration_and_rejection_mirrors_supply():
    _, z, _ = formation("DEMAND")
    l = ZoneLifecycleV2()
    l.add(z)
    b = minute(z, 0, o=102, h=104, l=96.5, c=102)
    events = l.five_minute(b)
    assert "ZONE_75_PERCENT_PENETRATION" in {e["event_type"] for e in events}
    assert "ZONE_REJECTION" in {e["event_type"] for e in events}
    assert all(e["direction"] == "UP" for e in events)


def test_incomplete_bar_no_lifecycle_event():
    l, z = lifecycle()
    b = minute(z, 0)
    b["complete"] = False
    assert not l.five_minute(b)


def test_lifecycle_duplicate_bar_rejected():
    l, z = lifecycle()
    l.five_minute(minute(z, 0))
    with pytest.raises(ValueError):
        l.five_minute(minute(z, 0))


def test_omitted_expected_bar_does_not_bridge_formation():
    p = Provider()
    p.update(bar(0))
    assert not p.update(bar(2, o=101, h=102, l=79, c=80))


def test_research_gate_rejects_incomplete_and_stale_proof():
    from engine.zone_v2.acceptance import assess, require_acceptance, REQUIRED

    report = assess({}, {}, "a")
    with pytest.raises(ValueError):
        require_acceptance(report, {}, "a")
    approved = assess({k: True for k in REQUIRED}, {}, "a")
    require_acceptance(approved, {}, "a")
    with pytest.raises(ValueError):
        require_acceptance(approved, {}, "b")
    with pytest.raises(ValueError):
        require_acceptance(approved, {"different": True}, "a")
