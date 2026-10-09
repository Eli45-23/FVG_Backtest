"""Full Development-only reconciliation; does not run zone/outcome research."""

from pathlib import Path
import json, time
import pandas as pd
import pyarrow.parquet as pq
from engine.canonical import clean, dumps, digest
from engine.research.profiles import profile as dataset
from engine.session_calendar.mnq_v1 import profile, schedule, NY, SOURCES
from engine.session_calendar.bars_v2 import build

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work/zone-v2-calendar-foundation"


def write(name, data):
    text = json.dumps(clean(data), indent=2, sort_keys=True) + "\n"
    p = OUT / name
    if name == "frozen_calendar_profile.json" and p.exists() and p.read_text() != text:
        raise ValueError("Frozen profile differs")
    p.write_text(text)


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    sessions = schedule()
    prof = profile()
    ds = dataset("research_2020_2026")
    write("frozen_calendar_profile.json", dict(**prof, dataset=ds.identity()))
    pd.DataFrame(
        [
            dict(
                **clean(s),
                source_title=SOURCES[s["schedule_source"]]["title"],
                source_url=SOURCES[s["schedule_source"]]["url"],
                access_date=SOURCES[s["schedule_source"]]["access_date"],
                regular_maintenance_start_ny="17:00",
                regular_maintenance_end_ny="18:00",
                maintenance_note="Standing rule only; unresolved rows do not assert official holiday hours; Friday also begins weekend closure",
            )
            for s in sessions
            if not s["resolved"] or s["schedule_source"] != "regular"
        ]
    ).to_csv(OUT / "official_session_exceptions.csv", index=False)
    lo = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC").as_unit("ns")
    hi = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC").as_unit("ns")
    raw = (
        pq.read_table(
            ds.minutes, filters=[("ts_event", ">=", lo), ("ts_event", "<", hi)]
        )
        .to_pandas()
        .sort_index()
    )
    bars, extra = build(raw, sessions)
    bars.to_parquet(OUT / "four_hour_bar_inventory.parquet", index=False)
    bars[
        [
            "bar_id",
            "timestamp",
            "availability_timestamp",
            "complete",
            "full",
            "atr14",
            "atr_count",
            "continuity_reset",
            "exclusion_reason",
        ]
    ].to_csv(OUT / "atr_continuity_audit.csv", index=False)
    mismatch = []
    checks = []
    expected_total = observed_expected = 0
    for b in bars.to_dict("records"):
        s = next(s for s in sessions if s["session_date"] == b["session_date"])
        p = raw.loc[
            (raw.index >= b["timestamp"]) & (raw.index < b["availability_timestamp"])
        ]
        expected = pd.date_range(
            b["timestamp"], b["availability_timestamp"], freq="min", inclusive="left"
        )
        if s["pause_start"] is not None:
            expected = expected[
                (expected < s["pause_start"]) | (expected >= s["pause_end"])
            ]
        if s["resolved"]:
            expected_total += len(expected)
            observed_expected += len(expected.intersection(p.index))
            for t in expected.difference(p.index):
                mismatch.append(
                    dict(
                        timestamp=t,
                        session_date=s["session_date"],
                        classification="vendor/source missingness",
                        context="Absent expected minute; no-trade/halt/vendor cause not established",
                        observed=False,
                        bar_id=b["bar_id"],
                    )
                )
            for t in p.index.difference(expected):
                mismatch.append(
                    dict(
                        timestamp=t,
                        session_date=s["session_date"],
                        classification="source observation outside the expected boundary",
                        context="expected maintenance interval / documented historical pause",
                        observed=True,
                        bar_id=b["bar_id"],
                    )
                )
        else:
            for t in p.index:
                mismatch.append(
                    dict(
                        timestamp=t,
                        session_date=s["session_date"],
                        classification="unresolved",
                        context="Official holiday/adjacent hours unavailable; entire session excluded",
                        observed=True,
                        bar_id=b["bar_id"],
                    )
                )
        arithmetic = True
        if len(p):
            values = [
                int(p.open.iloc[0]),
                int(p.high.max()),
                int(p.low.min()),
                int(p.close.iloc[-1]),
                sum(map(int, p.volume)),
            ]
            arithmetic = values == [
                round(b[k] * 1e9) for k in ["open", "high", "low", "close"]
            ] + [b["volume"]]
        complete = bool(
            len(p) > 0
            and len(expected) == len(p)
            and not len(expected.difference(p.index))
            and s["resolved"]
        )
        checks.append(
            dict(
                bar_id=b["bar_id"],
                accepted=bool(b["complete"]),
                ohlcv_exact=arithmetic,
                minute_count_exact=len(p) == b["minute_count"],
                completeness_exact=complete == b["complete"],
                start_exact=(b["timestamp"] - s["open"]).total_seconds() % 14400 == 0,
                end_exact=b["availability_timestamp"]
                == min(b["timestamp"] + pd.Timedelta(hours=4), s["close"]),
                expected_count_exact=len(expected) == b["expected_minutes"],
            )
        )
    # Outside every scheduled diagnostic interval: preserve all observations.
    for t in extra.ts_event:
        local = t.tz_convert(NY)
        label = (
            str((local + pd.Timedelta(days=1)).date())
            if local.hour >= 18
            else str(local.date())
        )
        s = next((s for s in sessions if s["session_date"] == label), None)
        mismatch.append(
            dict(
                timestamp=t,
                session_date=label,
                classification=(
                    "unresolved"
                    if s and not s["resolved"]
                    else "source observation outside the expected boundary"
                ),
                context=(
                    "official abbreviated session"
                    if s and s["abbreviated"]
                    else "expected maintenance interval or weekend boundary"
                ),
                observed=True,
                bar_id=None,
            )
        )
    m = pd.DataFrame(mismatch)
    m.to_csv(OUT / "source_coverage_mismatches.csv", index=False)
    m.groupby(["classification", "context", "observed"]).size().rename(
        "minutes"
    ).reset_index().to_csv(OUT / "mismatch_classification.csv", index=False)
    pd.DataFrame(checks).to_csv(OUT / "four_hour_ohlcv_reconciliation.csv", index=False)
    pd.DataFrame(
        [clean(s) for s in sessions if s["schedule_source"] != "regular"]
    ).to_csv(OUT / "holiday_abbreviated_session_audit.csv", index=False)
    dst = []
    for y in range(2020, 2024):
        from engine.session_calendar.mnq_v1 import nth

        for day in [nth(y, 3, 6, 2), nth(y, 11, 6, 1)]:
            for s in sessions:
                if abs((pd.Timestamp(s["session_date"]).date() - day).days) <= 3:
                    dst.append(
                        dict(
                            transition=str(day),
                            session_date=s["session_date"],
                            open_utc=s["open"],
                            open_ny=s["open"].tz_convert(NY),
                            close_utc=s["close"],
                            anchor_correct=s["open"].tz_convert(NY).hour == 18,
                        )
                    )
    pd.DataFrame(dst).to_csv(OUT / "dst_audit.csv", index=False)
    # Repeat complete reduction independently through the same deterministic pipeline.
    again, _ = build(raw, sessions)
    repeat = digest(bars.to_dict("records")) == digest(again.to_dict("records"))
    summary = dict(
        source_minutes=len(raw),
        official_expected_trading_minutes_resolved_sessions=expected_total,
        total_official_expected_minutes=None,
        observed_expected_minutes=observed_expected,
        observed_out_of_schedule_resolved=int(
            (
                (m.classification == "source observation outside the expected boundary")
                & m.observed
            ).sum()
        ),
        absent_expected_minutes=int((~m.observed).sum()),
        unresolved_observed_minutes=int((m.classification == "unresolved").sum()),
        unresolved_session_dates=[
            s["session_date"] for s in sessions if not s["resolved"]
        ],
        complete_full_bars=int((bars.complete & bars.full).sum()),
        accepted_bars=int(bars.complete.sum()),
        shortened_bars=int((~bars.full).sum()),
        incomplete_or_unresolved_bars=int((~bars.complete).sum()),
        excluded_formation_bars=int((~bars.formation_eligible).sum()),
        earliest_eligible_full_bar=bars.loc[
            bars.complete & bars.full, "availability_timestamp"
        ].min(),
        first_atr=bars.loc[bars.atr14.notna(), "availability_timestamp"].min(),
        atr_unavailable_sessions_including_resets=sorted(
            bars.loc[bars.atr14.isna(), "session_date"].unique()
        ),
        initial_warmup_sessions=sorted(
            bars.loc[
                bars.availability_timestamp
                < bars.loc[bars.atr14.notna(), "availability_timestamp"].min(),
                "session_date",
            ].unique()
        ),
        reconciliation_all=all(
            all(v for k, v in r.items() if k.endswith("exact")) for r in checks
        ),
        deterministic=repeat,
        bars_sha256=digest(bars.to_dict("records")),
        runtime_seconds=round(time.monotonic() - started, 3),
    )
    write("foundation_summary.json", summary)
    print(json.dumps(clean(summary), indent=2))


if __name__ == "__main__":
    main()
