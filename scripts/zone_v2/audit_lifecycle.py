"""Detection-only Development audit; intentionally no outcome loader."""

from pathlib import Path
import sys, json, time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import pyarrow.parquet as pq
from engine.zone_v2.lifecycle import ZoneLifecycleV2
from engine.canonical import dumps, clean, digest
from engine.research.profiles import profile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work/supply-demand-provider-v2"


def main():
    started = time.monotonic()
    zones = []
    for side in ["supply", "demand"]:
        for payload in pd.read_parquet(OUT / f"detected_{side}_zones.parquet").payload:
            z = json.loads(payload)
            for key in ["availability_timestamp", "formation_timestamp"]:
                z[key] = pd.Timestamp(z[key])
            for key in ["base_timestamps", "departure_timestamps"]:
                z[key] = list(map(pd.Timestamp, z[key]))
            zones.append(z)
    zones.sort(key=lambda z: (z["availability_timestamp"], z["zone_id"]))
    end = (
        pd.Timestamp("2024-01-01", tz="America/New_York")
        .tz_convert("UTC")
        .as_unit("ns")
    )
    bars = pq.read_table(
        profile("research_2020_2026").bars, filters=[("timestamp_utc", "<", end)]
    ).to_pandas()
    frames = pd.read_parquet(OUT / "four_hour_bars.parquet").to_dict("records")
    config = json.loads((OUT / "frozen_provider_config.json").read_text())
    expected = []
    for session in config["frame"]["sessions"]:
        idx = pd.date_range(
            session["open"], session["close"], freq="min", inclusive="left"
        )
        if session["pause_start"] is not None:
            idx = idx[
                (idx < pd.Timestamp(session["pause_start"]))
                | (idx >= pd.Timestamp(session["pause_end"]))
            ]
        expected.extend(idx)
    engine = ZoneLifecycleV2(pd.DatetimeIndex(expected))
    zi = fi = 0
    rows = []
    for b in bars.to_dict("records"):
        b["timestamp"] = b["timestamp_utc"]
        start = b["timestamp"]
        at = start + pd.Timedelta(minutes=5)
        while fi < len(frames) and frames[fi]["availability_timestamp"] <= start:
            engine.four_hour(frames[fi])
            fi += 1
        while zi < len(zones) and zones[zi]["availability_timestamp"] <= start:
            engine.add(zones[zi])
            zi += 1
        engine.five_minute(b)
        if len(engine.events) >= 2000:
            rows.extend(engine.events)
            engine.events = []
    while fi < len(frames):
        engine.four_hour(frames[fi])
        fi += 1
    rows.extend(engine.events)
    flat = []
    for e in rows:
        flat.append(
            {
                k: dumps(v) if isinstance(v, (dict, list)) else v
                for k, v in clean(e).items()
            }
        )
    df = pd.DataFrame(flat)
    df.to_parquet(OUT / "zone_events.parquet", index=False)
    # State audit contains observations only, not forward outcome labels.
    states = []
    for zid, s in engine.states.items():
        states.append(
            dict(
                zone_id=zid,
                zone_type=s["zone"]["zone_type"],
                touch_number=s["touch_number"],
                first_touch_timestamp=s["first_touch_timestamp"],
                fresh=s["fresh"],
                touched=s["touched"],
                entered=s["entered"],
                mitigated=s["mitigated"],
                active=s["active"],
                invalidated=s["invalidated"],
                invalidated_at=s.get("invalidated_at"),
                deepest_penetration=s["deepest_penetration"],
                coverage_uncertain=s["coverage_uncertain"],
            )
        )
    pd.DataFrame(states).to_csv(OUT / "zone_lifecycle_audit.csv", index=False)
    audit = df[
        [
            "event_id",
            "zone_id",
            "provider_version",
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
    audit.to_csv(OUT / "causal_availability_audit.csv", index=False)
    (OUT / "lifecycle_summary.json").write_text(
        json.dumps(
            dict(
                events=len(df),
                zones=len(states),
                causal=bool(audit.causal.all()),
                unique=bool(audit.unique_event.all()),
                events_sha256=digest(flat),
                runtime_seconds=round(time.monotonic() - started, 3),
            ),
            indent=2,
        )
        + "\n"
    )
    print((OUT / "lifecycle_summary.json").read_text())


if __name__ == "__main__":
    main()
