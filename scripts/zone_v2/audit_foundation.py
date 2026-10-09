"""Development-only V2 foundation audit. No forward outcomes are computed."""

from pathlib import Path
import sys, json, time, hashlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import pyarrow.parquet as pq
from engine.zone_v2.frames import session_schedule, aggregate, with_atr, identity
from engine.zone_v2.provider import DisplacementBaseZoneProviderV2, ProviderConfig
from engine.canonical import clean, dumps, digest
from engine.research.profiles import profile
from dataclasses import asdict

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work/supply-demand-provider-v2"


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    p = profile("research_2020_2026")
    lo = (
        pd.Timestamp("2019-12-01", tz="America/New_York")
        .tz_convert("UTC")
        .as_unit("ns")
    )
    hi = (
        pd.Timestamp("2024-01-01", tz="America/New_York")
        .tz_convert("UTC")
        .as_unit("ns")
    )
    raw = pq.read_table(
        p.minutes, filters=[("ts_event", ">=", lo), ("ts_event", "<", hi)]
    ).to_pandas()
    sessions = session_schedule("2020-01-02", "2023-12-29")
    fid = identity(sessions)
    config = dict(
        status="ENGINEERING_ACCEPTANCE_PENDING",
        provider=asdict(ProviderConfig()),
        frame=fid,
        dataset=p.identity(),
        segment="development",
        start="2020-01-01",
        end="2024-01-01",
        requested_warmup_start="2019-12-01",
        actual_first_source=str(raw.index.min()),
    )
    cp = OUT / "frozen_provider_config.json"
    if cp.exists() and json.loads(cp.read_text()) != clean(config):
        raise RuntimeError("Immutable configuration differs")
    cp.write_text(json.dumps(clean(config), indent=2, sort_keys=True) + "\n")
    bars, extra = aggregate(raw, sessions)
    bars = with_atr(bars)
    bars.to_parquet(OUT / "four_hour_bars.parquet", index=False)
    extra[["ts_event"]].to_csv(OUT / "out_of_schedule_minutes.csv", index=False)
    # Independent direct minute slicing and Python integer reducers.
    checks = []
    for b in bars.to_dict("records"):
        a = raw.loc[
            (raw.index >= b["timestamp"]) & (raw.index < b["availability_timestamp"])
        ]
        ok = True
        if len(a):
            expected = [
                int(a.open.iloc[0]),
                max(map(int, a.high)),
                min(map(int, a.low)),
                int(a.close.iloc[-1]),
            ]
            ok = all(
                round(b[k] * 1e9) == v
                for k, v in zip(["open", "high", "low", "close"], expected)
            ) and b["volume"] == sum(map(int, a.volume))
        checks.append(
            dict(
                timestamp=b["timestamp"],
                availability=b["availability_timestamp"],
                session_date=b["session_date"],
                full=b["full"],
                complete=b["complete"],
                minute_count=b["minute_count"],
                expected_minutes=b["expected_minutes"],
                missing_minutes=b["missing_minutes"],
                unexpected_minutes=b["unexpected_minutes"],
                ohlcv_reconciled=ok,
            )
        )
    pd.DataFrame(checks).to_csv(OUT / "four_hour_bar_reconciliation.csv", index=False)
    bars[
        [
            "timestamp",
            "session_date",
            "full",
            "complete",
            "atr14",
            "atr_count",
            "continuity_reset",
            "missing_minutes",
            "first_missing",
        ]
    ].to_csv(OUT / "atr_continuity_audit.csv", index=False)
    provider = DisplacementBaseZoneProviderV2(frame_identity=fid["schedule_sha256"])
    for b in bars.to_dict("records"):
        provider.update(b)
    for side in ["SUPPLY", "DEMAND"]:
        z = [
            dict(**clean(z), payload=dumps(z))
            for z in provider.zones
            if z["zone_type"] == side
        ]
        pd.DataFrame(
            [
                {
                    k: dumps(v) if isinstance(v, (dict, list)) else v
                    for k, v in row.items()
                }
                for row in z
            ]
        ).to_parquet(OUT / ("detected_" + side.lower() + "_zones.parquet"), index=False)
    again = DisplacementBaseZoneProviderV2(frame_identity=fid["schedule_sha256"])
    for b in bars.to_dict("records"):
        again.update(b)
    result = dict(
        source_rows=len(raw),
        bars=len(bars),
        complete_full_bars=int((bars.complete & bars.full).sum()),
        atr_available=int(bars.atr14.notna().sum()),
        missing_minutes=int(bars.missing_minutes.sum()),
        unexpected_minutes=int(bars.unexpected_minutes.sum()),
        out_of_schedule_minutes=len(extra),
        supply=sum(z["zone_type"] == "SUPPLY" for z in provider.zones),
        demand=sum(z["zone_type"] == "DEMAND" for z in provider.zones),
        first_atr=str(bars.loc[bars.atr14.notna(), "availability_timestamp"].min()),
        zones_sha256=digest(provider.zones),
        deterministic=digest(provider.zones) == digest(again.zones),
        ohlcv_all_reconciled=all(c["ohlcv_reconciled"] for c in checks),
        runtime_seconds=round(time.monotonic() - started, 3),
    )
    (OUT / "foundation_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
