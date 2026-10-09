import pandas as pd
import pytest
from engine.session_calendar.mnq_v1 import schedule, profile, NY, nth
from engine.session_calendar.bars_v2 import build
from engine.zone_v2.frames import session_schedule
from engine.canonical import digest


def minutes(sessions):
    times = []
    for s in sessions:
        x = pd.date_range(s["open"], s["close"], freq="min", inclusive="left")
        if s["pause_start"] is not None:
            x = x[(x < s["pause_start"]) | (x >= s["pause_end"])]
        times.extend(x)
    return pd.DataFrame(
        dict(
            open=100_000_000_000,
            high=101_000_000_000,
            low=99_000_000_000,
            close=100_250_000_000,
            volume=2,
        ),
        index=pd.DatetimeIndex(times, name="ts_event"),
    )


def test_regular_and_pause_change():
    before = schedule("2021-06-25", "2021-06-25")[0]
    after = schedule("2021-06-28", "2021-06-28")[0]
    assert (
        before["open"].tz_convert(NY).hour == 18
        and before["close"].tz_convert(NY).hour == 17
    )
    assert before["pause_start"].tz_convert(NY).strftime("%H:%M") == "16:15"
    assert after["pause_start"] is None
    b, _ = build(minutes([before, after]), [before, after])
    assert b.complete.all()
    assert b.iloc[5].expected_minutes == 165 and b.iloc[-1].expected_minutes == 180


@pytest.mark.parametrize("year", [2020, 2021, 2022, 2023])
@pytest.mark.parametrize("month,n,offset", [(3, 2, -4), (11, 1, -5)])
def test_every_dst_transition(year, month, n, offset):
    sunday = pd.Timestamp(nth(year, month, 6, n))
    monday = str((sunday + pd.Timedelta(days=1)).date())
    s = schedule(monday, monday)[0]
    ny = s["open"].tz_convert(NY)
    assert ny.hour == 18 and ny.utcoffset().total_seconds() / 3600 == offset
    bars, _ = build(minutes([s]), [s])
    assert bars.complete.all()
    assert list(bars.timestamp.dt.tz_convert(NY).dt.hour) == [18, 22, 2, 6, 10, 14]


@pytest.mark.parametrize(
    "d,close",
    [
        ("2023-04-07", "09:15"),
        ("2023-07-03", "13:15"),
        ("2023-07-04", "13:00"),
        ("2023-06-19", "13:00"),
        ("2023-11-24", "13:15"),
    ],
)
def test_verified_abbreviated(d, close):
    s = schedule(d, d)[0]
    assert s["resolved"] and s["close"].tz_convert(NY).strftime("%H:%M") == close
    b, _ = build(minutes([s]), [s])
    assert b.complete.all() and not b.iloc[-1].full
    assert not b.iloc[-1].formation_eligible


@pytest.mark.parametrize("d", ["2020-04-10", "2021-04-02", "2022-04-15", "2022-06-20"])
def test_unverified_holidays_fail_closed(d):
    s = schedule(d, d)[0]
    assert not s["resolved"] and s["official_close"] is None
    b, _ = build(minutes([s]), [s])
    assert not b.complete.any() and b.atr14.isna().all()
    assert b.official_expected_minutes.isna().all()


def test_atr_weekend_dst_reset_recovery_and_exact_reduction():
    ss = schedule("2023-03-06", "2023-03-17")
    raw = minutes(ss)
    b, _ = build(raw, ss)
    assert b.atr14.notna().any()
    assert b.loc[b.full, "open"].eq(100).all() and b.loc[b.full, "volume"].eq(480).all()
    assert not b.continuity_reset.any()
    missing = ss[5]["open"] + pd.Timedelta(minutes=7)
    c, _ = build(raw.drop(missing), ss)
    bad = c[c.timestamp == ss[5]["open"]].iloc[0]
    assert not bad.complete and bad.continuity_reset and pd.isna(bad.atr14)
    later = c[c.timestamp > ss[5]["open"]]
    eligible = later[later.full]
    assert eligible.iloc[:13].atr14.isna().all() and pd.notna(eligible.iloc[13].atr14)


def test_shortened_holiday_preserves_atr_but_unresolved_resets():
    ss = schedule("2023-06-12", "2023-06-21")
    b, _ = build(minutes(ss), ss)
    # Jun16 is deliberately unresolved adjacent-day context; then confirmed Jun19 resumes.
    assert not b[b.session_date == "2023-06-16"].complete.any()
    short = b[(b.session_date == "2023-06-19") & ~b.full].iloc[0]
    assert short.complete and not short.continuity_reset


def test_deterministic_ids_and_source_outside():
    ss = schedule("2023-03-06", "2023-03-06")
    raw = minutes(ss)
    a, _ = build(raw, ss)
    b, _ = build(raw, ss)
    assert digest(a.to_dict("records")) == digest(b.to_dict("records"))
    raw.loc[ss[0]["close"]] = raw.iloc[0]
    _, extra = build(raw.sort_index(), ss)
    assert len(extra) == 1
    assert profile()["profile_sha256"] == profile()["profile_sha256"]


def test_legacy_candidate_preserved_and_development_guard():
    assert not any(
        x["session_date"] == "2023-04-07"
        for x in session_schedule("2023-04-06", "2023-04-10")
    )
    assert schedule("2023-04-07", "2023-04-07")[0]["resolved"]
    with pytest.raises(ValueError):
        schedule("2024-01-01", "2024-02-01")


def test_initialized_atr_survives_verified_abbreviation_and_weekend():
    # November 22/23/24 are all explicitly documented, so no unknown reset.
    ss = schedule("2023-11-13", "2023-11-27")
    b, _ = build(minutes(ss), ss)
    short = b[(b.session_date == "2023-11-23") & ~b.full].iloc[0]
    assert short.complete and short.atr_count == 14 and short.atr14 == 2
    following = b[b.session_date == "2023-11-24"].iloc[0]
    assert following.atr_count == 14 and following.atr14 == 2
    assert not b.continuity_reset.any()


def test_unexpected_pause_observation_disables_bucket_and_resets():
    ss = schedule("2021-06-21", "2021-06-25")
    raw = minutes(ss)
    at = ss[-1]["pause_start"]
    raw.loc[at] = raw.iloc[0]
    b, _ = build(raw.sort_index(), ss)
    last = b.iloc[-1]
    assert last.unexpected_minutes == 1 and not last.complete
    assert last.continuity_reset and pd.isna(last.atr14)


def test_future_source_does_not_change_prior_bars():
    ss = schedule("2023-03-06", "2023-03-10")
    raw = minutes(ss)
    full, _ = build(raw, ss)
    prefix, _ = build(raw.loc[raw.index < ss[3]["open"]], ss[:3])
    assert digest(prefix.to_dict("records")) == digest(
        full.iloc[: len(prefix)].to_dict("records")
    )


def test_unsorted_source_has_same_identity_and_last_minute():
    ss = schedule("2023-03-06", "2023-03-06")
    raw = minutes(ss)
    a, _ = build(raw, ss)
    b, _ = build(raw.iloc[::-1], ss)
    assert digest(a.to_dict("records")) == digest(b.to_dict("records"))
