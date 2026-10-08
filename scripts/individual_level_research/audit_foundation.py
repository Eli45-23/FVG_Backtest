import sys, json, hashlib, time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import pandas as pd, numpy as np
from engine.research.study2 import source
from engine.research.study import read_bars
from engine.timeframes import aggregate, FrameConfig
from engine.features import FeatureHub
from engine.research.levels import SessionConfig, NY

R = (
    Path(__file__).resolve().parents[2]
    / "work"
    / "mnq-individual-level-master-research"
)
C = json.loads(
    Path(
        "storage/event_studies/5cb7fab0d4e7414792a3fbe59ded4999/config.json"
    ).read_text()
)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


manifest = {}
for f in Path("storage/event_studies/5cb7fab0d4e7414792a3fbe59ded4999").iterdir():
    if f.is_file():
        manifest[str(f)] = {"sha256": sha(f), "bytes": f.stat().st_size}
for v in C["dataset_identity"]["files"].values():
    p = Path("outputs/data") / v["name"]
    assert sha(p) == v["sha256"]
    manifest[str(p)] = {"sha256": v["sha256"], "bytes": p.stat().st_size}
(R / "preserved_source_manifest.json").write_text(json.dumps(manifest, indent=2))
(R / "registration_clarification.json").write_text(
    json.dumps(
        {
            "BREAK_FAILED_HOLD": "Exact existing engine enum BREAK_FAILED_NEXT_CANDLE_HOLD; semantic alias correction before aggregate outcome analysis. No family or hypothesis change."
        },
        indent=2,
    )
)
print("identities verified", flush=True)
start = time.monotonic()
raw = source(C, True)
bars = read_bars(C)
assert raw.index.max() < pd.Timestamp("2024-01-01", tz=NY)
frames = {
    "5m": bars,
    **{
        t: aggregate(raw, t, FrameConfig(**C["research_settings"]["frame"]))
        for t in ["15m", "4h"]
    },
}
coverage = []
ny = bars.timestamp_utc.dt.tz_convert(NY)
bar_days = {str(d): g for d, g in bars.groupby(ny.dt.date)}
for day in C["calendar"]["sessions"]:
    if not "2020-01-01" <= day < "2024-01-01":
        continue
    g = bar_days.get(day, pd.DataFrame(columns=bars.columns))
    t = g.timestamp_utc.dt.tz_convert(NY)
    pm = g[(t.dt.strftime("%H:%M") < "09:30")]
    expected = pd.date_range(day + " 00:00", day + " 09:25", freq="5min", tz=NY)
    actual = pd.DatetimeIndex(pm.loc[pm.is_complete_5m, "timestamp_utc"]).tz_convert(NY)
    missing = expected.difference(actual)
    coverage.append(
        dict(
            date=day,
            expected=114,
            actual_complete=len(actual),
            available=len(missing) == 0,
            missing_or_incomplete_starts=";".join(map(str, missing)),
        )
    )
pd.DataFrame(coverage).to_csv(R / "premarket_coverage.csv", index=False)
# Replay only frozen causal provider; no changes to indicator gap behavior or candle anchoring.
hub = FeatureHub(
    frames,
    SessionConfig(**C["session"]),
    C["research_settings"],
    {
        d: tuple(pd.Timestamp(t) for t in ts)
        for d, ts in C["calendar"]["sessions"].items()
    },
)
counts = {
    t: dict(bars=len(f), complete=int(f.is_complete_5m.sum()), atr_available=0, zones=0)
    for t, f in frames.items()
}
catalog = {}
seen = {}
context = []
for row in bars.itertuples(index=False):
    at = row.timestamp_utc + pd.Timedelta(minutes=5)
    hub.advance(at)
    for tf, v in hub.values.items():
        latest = hub.latest.get(tf)
        if latest is None or seen.get(tf) == latest.timestamp:
            continue
        seen[tf] = latest.timestamp
        if v.get("atr14") is not None:
            counts[tf]["atr_available"] += 1
        for swing in v.get("confirmed_swings", []):
            old = catalog.get(swing["id"], {})
            first = old.get("first_broken_at")
            if first is None and swing.get("broken"):
                first = at
            catalog[swing["id"]] = {
                **swing,
                "observed_timeframe": tf,
                "first_broken_at": first,
            }
for tf, z in hub.zones.items():
    counts[tf]["zones"] = len(z.zones)
pd.DataFrame(catalog.values()).to_parquet(R / "swing_catalog.parquet", index=False)
(R / "foundation_audit.json").write_text(
    json.dumps(
        {
            "frames": counts,
            "zone_config": C["research_settings"]["zones"],
            "frame_config": C["research_settings"]["frame"],
            "runtime_seconds": time.monotonic() - start,
            "pm_complete_dates": sum(x["available"] for x in coverage),
            "pm_unavailable_dates": sum(not x["available"] for x in coverage),
        },
        indent=2,
    )
)
print(counts, flush=True)
