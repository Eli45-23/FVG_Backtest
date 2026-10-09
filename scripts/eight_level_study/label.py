"""Offline forward measurements, physically separate from the causal detector."""

import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from engine.research.outcomes import PreparedMinutes, label as reference_label
from scripts.eight_level_study.detect import P, PM, NY

HORIZONS = ["5", "10", "15", "30", "60", "session_close"]
POINTS = [10, 25, 50, 75, 100, 150, 200]
ATR = [0.5, 1, 1.5, 2]


def measures(obs, frame):
    at = pd.Timestamp(obs["timestamp_utc"])
    end = pd.Timestamp(obs["session_close"])
    price = float(obs["price_at_event"])
    atr = obs.get("atr14")
    left = np.searchsorted(frame.times, at.value)
    out = []
    for h in HORIZONS:
        stop = end if h == "session_close" else at + pd.Timedelta(minutes=int(h))
        r = dict(
            event_id=obs["event_id"], horizon=h, complete=False, censor_reason=None
        )
        if stop <= at or stop > end:
            r["censor_reason"] = "OUTSIDE_SESSION"
            out.append(r)
            continue
        right = np.searchsorted(frame.times, stop.value)
        times = frame.times[left:right]
        v = frame.values[left:right]
        n = int((stop - at).total_seconds() / 60)
        if (
            len(times) != n
            or times[0] != at.value
            or not np.all(np.diff(times) == 60_000_000_000)
        ):
            r["censor_reason"] = "MISSING_MINUTES"
            out.append(r)
            continue
        op, hi, lo, cl = v.T
        if (
            not np.isfinite(v).all()
            or not (
                (hi >= np.maximum.reduce([op, lo, cl])) & (lo <= np.minimum(op, cl))
            ).all()
        ):
            r["censor_reason"] = "INVALID_OHLC"
            out.append(r)
            continue
        r.update(
            complete=True,
            forward_change=float(cl[-1] - price),
            up_excursion=max(0, float(hi.max() - price)),
            down_excursion=max(0, float(price - lo.min())),
        )
        for side, fav, adv in [
            ("up", hi - price, price - lo),
            ("down", price - lo, hi - price),
        ]:
            for t in POINTS:
                ix = np.flatnonzero(fav >= t)
                hit = len(ix) > 0
                r[f"{side}_hit_{t}"] = float(hit)
                r[f"{side}_time_{t}"] = float(ix[0] + 1) if hit else None
                r[f"{side}_mae_before_{t}"] = (
                    max(0, float(adv[: ix[0] + 1].max())) if hit else None
                )
            for t in ATR:
                r[f"{side}_atr_{t:g}"] = (
                    float(np.any(fav >= t * atr))
                    if atr is not None and np.isfinite(atr) and atr > 0
                    else None
                )
        out.append(r)
    return out


NUM = (
    ["forward_change", "up_excursion", "down_excursion"]
    + [
        f"{s}_{m}_{t}"
        for s in ["up", "down"]
        for t in POINTS
        for m in ["hit", "time", "mae_before"]
    ]
    + [f"{s}_atr_{t:g}" for s in ["up", "down"] for t in ATR]
)
SCHEMA = pa.schema(
    [
        ("event_id", pa.string()),
        ("horizon", pa.string()),
        ("complete", pa.bool_()),
        ("censor_reason", pa.string()),
    ]
    + [(k, pa.float64()) for k in NUM]
)


def main():
    cfg = json.loads((ROOT / "storage/event_studies" / PM / "config.json").read_text())
    assert cfg["segment"] == "development" and cfg["end"] == "2024-01-01"
    start = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC")
    end = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC")
    raw = pq.read_table(
        ROOT / "outputs/data" / cfg["dataset_identity"]["files"]["minutes"]["name"],
        filters=[("ts_event", ">=", start), ("ts_event", "<", end)],
    ).to_pandas()
    if "ts_event" in raw:
        raw = raw.set_index("ts_event")
    raw = raw.sort_index()
    assert raw.index.is_unique and raw.index.min() >= start and raw.index.max() < end
    for k in ["open", "high", "low", "close"]:
        raw[k] = raw[k].astype(float) / 1e9
    days = {
        str(d): PreparedMinutes(g)
        for d, g in raw.groupby(raw.index.tz_convert(NY).date)
    }
    obs = pd.read_parquet(P / "baseline_observations.parquet").sort_values(
        "timestamp_utc"
    )
    writer = pq.ParquetWriter(
        P / "baseline_outcomes.parquet", SCHEMA, compression="zstd"
    )
    buffer = []
    checked = 0
    try:
        for i, o in enumerate(obs.to_dict("records")):
            result = measures(o, days[o["date"]])
            buffer.extend(result)
            if i % 257 == 0:
                ref = reference_label(o, days[o["date"]])
                for r in result:
                    v = ref[r["horizon"]]
                    assert (
                        v["complete"] == r["complete"]
                        and v["censor_reason"] == r["censor_reason"]
                    )
                    if r["complete"]:
                        assert (
                            v["maximum_high_excursion"] == r["up_excursion"]
                            and v["maximum_low_excursion"] == r["down_excursion"]
                        )
                        for s in ["up", "down"]:
                            for t in [10, 25, 50, 75, 100]:
                                a = v["thresholds"][f"{s}_{t}"]
                                assert (
                                    bool(r[f"{s}_hit_{t}"]) == a["reached"]
                                    and r[f"{s}_time_{t}"] == a["minutes"]
                                )
                    checked += 1
            if len(buffer) >= 6144:
                writer.write_table(pa.Table.from_pylist(buffer, schema=SCHEMA))
                buffer = []
        if buffer:
            writer.write_table(pa.Table.from_pylist(buffer, schema=SCHEMA))
    finally:
        writer.close()
    (P / "label_verification.json").write_text(
        json.dumps(
            dict(
                source_minutes=len(raw),
                ordinary_observations=len(obs),
                outcome_rows=len(obs) * 6,
                independent_native_horizon_checks=checked,
                start=str(start),
                end_exclusive=str(end),
            ),
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    print(
        "Forward labels complete:", len(obs) * 6, "native checks", checked, flush=True
    )


if __name__ == "__main__":
    main()
