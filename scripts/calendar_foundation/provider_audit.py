"""Engineering only. Requires reviewed bar readiness; never computes outcomes."""

import json, time
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from engine.zone_v2.provider import DisplacementBaseZoneProviderV2
from engine.zone_v2.lifecycle import ZoneLifecycleV2
from engine.canonical import clean, dumps, digest
from engine.research.profiles import profile as dataset
from engine.session_calendar.mnq_v1 import schedule, profile, NY
from scripts.calendar_foundation.audit import OUT, ROOT, write


def main():
    started = time.monotonic()
    gate = json.loads((OUT / "human_ground_truth_readiness.json").read_text())
    bars = pd.read_parquet(OUT / "four_hour_bar_inventory.parquet")
    if (
        gate["status"] != "READY_FOR_HUMAN_GROUND_TRUTH"
        or digest(bars.to_dict("records")) != gate["bars_sha256"]
        or profile()["profile_sha256"] != gate["profile_sha256"]
    ):
        raise ValueError("Reviewed matching foundation required")
    frames = bars.to_dict("records")
    provider = DisplacementBaseZoneProviderV2(
        frame_identity=profile()["profile_sha256"]
    )
    for b in frames:
        provider.update(b)
    repeat = DisplacementBaseZoneProviderV2(frame_identity=profile()["profile_sha256"])
    for b in frames:
        repeat.update(b)
    assert digest(provider.zones) == digest(repeat.zones)
    zones = sorted(
        provider.zones, key=lambda z: (z["availability_timestamp"], z["zone_id"])
    )
    for side in ("SUPPLY", "DEMAND"):
        pd.DataFrame(
            [
                dict(zone_id=z["zone_id"], payload=dumps(z))
                for z in zones
                if z["zone_type"] == side
            ]
        ).to_parquet(OUT / f"detected_{side.lower()}_zones.parquet", index=False)
    lo = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC").as_unit("ns")
    hi = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC").as_unit("ns")
    five = pq.read_table(
        dataset("research_2020_2026").bars,
        filters=[("timestamp_utc", ">=", lo), ("timestamp_utc", "<", hi)],
    ).to_pandas()
    # Lifecycle keeps the existing complete-5m rule inside resolved official hours.
    # Incomplete 4h bars still cannot form or invalidate zones.
    expected = []
    accepted_minutes = []
    for s in schedule():
        x = pd.date_range(s["open"], s["close"], freq="min", inclusive="left")
        if s["pause_start"] is not None:
            x = x[(x < s["pause_start"]) | (x >= s["pause_end"])]
        # Include nominal unknown windows only in gap detection so unknown data is never a scheduled closure.
        expected.extend(x)
        if s["resolved"]:
            accepted_minutes.extend(x)
    allowed = pd.DatetimeIndex(accepted_minutes)
    engine = ZoneLifecycleV2(pd.DatetimeIndex(expected))
    zi = fi = 0
    events = []
    for b in five.to_dict("records"):
        start = b["timestamp_utc"]
        b["timestamp"] = start
        b["complete"] = bool(
            b["is_complete_5m"]
            and all(start + pd.Timedelta(minutes=k) in allowed for k in range(5))
        )
        while fi < len(frames) and frames[fi]["availability_timestamp"] <= start:
            engine.four_hour(frames[fi])
            fi += 1
        while zi < len(zones) and zones[zi]["availability_timestamp"] <= start:
            engine.add(zones[zi])
            zi += 1
        engine.five_minute(b)
        if len(engine.events) > 2000:
            events.extend(engine.events)
            engine.events = []
    while fi < len(frames):
        engine.four_hour(frames[fi])
        fi += 1
    events.extend(engine.events)
    flat = [
        {k: dumps(v) if isinstance(v, (dict, list)) else v for k, v in clean(e).items()}
        for e in events
    ]
    df = pd.DataFrame(flat)
    df.to_parquet(OUT / "zone_events.parquet", index=False)
    audit = df[
        [
            "event_id",
            "zone_id",
            "event_type",
            "bar_start",
            "timestamp",
            "availability_timestamp",
        ]
    ].copy()
    audit["causal"] = pd.to_datetime(audit.bar_start) >= pd.to_datetime(
        audit.availability_timestamp
    )
    audit["unique_event"] = ~audit.event_id.duplicated(keep=False)
    assert audit.causal.all() and audit.unique_event.all()
    audit.to_csv(OUT / "causal_availability_audit.csv", index=False)
    pd.DataFrame(
        [
            dict(
                zone_id=k,
                **{
                    f: clean(s.get(f))
                    for f in [
                        "touch_number",
                        "first_touch_timestamp",
                        "active",
                        "invalidated",
                        "mitigated",
                        "coverage_uncertain",
                        "invalidated_at",
                    ]
                },
            )
            for k, s in engine.states.items()
        ]
    ).to_csv(OUT / "zone_lifecycle_audit.csv", index=False)
    old = []
    for side in ("supply", "demand"):
        old.extend(
            json.loads(x)
            for x in pd.read_parquet(
                ROOT / f"work/supply-demand-provider-v2/detected_{side}_zones.parquet"
            ).payload
        )

    def key(z):
        return (
            z["zone_type"],
            str(pd.Timestamp(z["formation_timestamp"])),
            tuple(str(pd.Timestamp(t)) for t in z["base_timestamps"]),
        )

    prior = {key(z): z for z in old}
    now = {key(z): z for z in zones}
    rows = []
    for k in sorted(set(prior) | set(now)):
        a, b = prior.get(k), now.get(k)
        rows.append(
            dict(
                zone_type=k[0],
                formation_timestamp=k[1],
                old_zone_id=a["zone_id"] if a else None,
                new_zone_id=b["zone_id"] if b else None,
                status=(
                    "RETAINED_REIDENTIFIED" if a and b else "REMOVED" if a else "ADDED"
                ),
                boundaries_unchanged=bool(
                    a and b and (a["top"], a["bottom"]) == (b["top"], b["bottom"])
                ),
                availability_unchanged=bool(
                    a
                    and b
                    and pd.Timestamp(a["availability_timestamp"])
                    == pd.Timestamp(b["availability_timestamp"])
                ),
                old_top=a["top"] if a else None,
                new_top=b["top"] if b else None,
                old_bottom=a["bottom"] if a else None,
                new_bottom=b["bottom"] if b else None,
                old_availability=a["availability_timestamp"] if a else None,
                new_availability=b["availability_timestamp"] if b else None,
            )
        )
    pd.DataFrame(rows).to_csv(OUT / "provider_before_after_comparison.csv", index=False)
    summary = dict(
        provider_status="PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH",
        supply=sum(z["zone_type"] == "SUPPLY" for z in zones),
        demand=sum(z["zone_type"] == "DEMAND" for z in zones),
        zones_sha256=digest(zones),
        events=len(events),
        events_sha256=digest(flat),
        causal=True,
        unique=True,
        formation_deterministic=True,
        first_zone_availability=min(z["availability_timestamp"] for z in zones),
        comparison_counts=pd.Series([r["status"] for r in rows])
        .value_counts()
        .to_dict(),
        scope="Engineering only; lifecycle requires complete 5m bars in resolved official hours; 4h formation/invalidation requires complete full bars",
        runtime_seconds=round(time.monotonic() - started, 3),
    )
    write("provider_summary.json", summary)
    print(json.dumps(clean(summary), indent=2))


if __name__ == "__main__":
    main()
