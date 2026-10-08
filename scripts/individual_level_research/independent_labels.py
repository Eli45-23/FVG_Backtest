"""Independent pandas arithmetic, without calling engine outcome/statistics helpers."""

import json
import numpy as np, pandas as pd, pyarrow.parquet as pq, duckdb
from analyze import R, folder, LEVELS

path = "outputs/data/GLBX.MDP3_MNQ.v.0_ohlcv-1m_2020-01-01_2026-10-06.parquet"
a = pd.Timestamp("2020-01-01", tz="America/New_York").tz_convert("UTC")
b = pd.Timestamp("2024-01-01", tz="America/New_York").tz_convert("UTC")
m = pq.read_table(
    path,
    filters=[("ts_event", ">=", a), ("ts_event", "<", b)],
    columns=["ts_event", "open", "high", "low", "close"],
).to_pandas()
m = m[["open", "high", "low", "close"]].astype(float) / 1e9
charts = pd.read_csv(R / "chart_audit_index.csv")
n = 0
complete = 0
thresholds = 0
for level in LEVELS[:10]:
    e = pd.read_parquet(folder(level) / "events.parquet").set_index("event_id")
    id = json.loads((folder(level) / "configuration.json").read_text())["study_id"]
    con = duckdb.connect()
    for item in charts[charts.level == level].itertuples():
        p = json.loads(e.loc[item.event_id, "payload"])
        at = pd.Timestamp(p["timestamp_utc"])
        end = pd.Timestamp(p["session_close"])
        price = float(p["price_at_event"])
        saved = con.execute(
            "select * from read_parquet(?) where event_id=?",
            [f"storage/event_studies/{id}/v2_outcomes.parquet", item.event_id],
        ).df()
        for row in saved.itertuples():
            n += 1
            stop = (
                end
                if row.horizon == "session_close"
                else at + pd.Timedelta(minutes=int(row.horizon))
            )
            g = m[(m.index >= at) & (m.index < stop)]
            expected = (
                pd.date_range(at, stop, freq="min", inclusive="left")
                if stop > at
                else pd.DatetimeIndex([])
            )
            valid = bool(
                stop <= end
                and stop > at
                and g.index.as_unit("ns").equals(expected.as_unit("ns"))
                and np.isfinite(g.to_numpy()).all()
                and (g.high >= g[["open", "close", "low"]].max(axis=1)).all()
                and (g.low <= g[["open", "close"]].min(axis=1)).all()
            )
            assert valid == row.complete, (item.event_id, row.horizon)
            if not valid:
                continue
            complete += 1
            assert row.forward_close_change == float(g.close.iloc[-1]) - price
            assert row.maximum_high_excursion == max(0, float(g.high.max()) - price)
            assert row.maximum_low_excursion == max(0, price - float(g.low.min()))
            labels = json.loads(row.payload)
            for side, series in [("up", g.high - price), ("down", price - g.low)]:
                for t in [0.25, 0.5, 0.75, 1, 1.5, 2, 3]:
                    atr = p.get("atr14")
                    if not atr:
                        continue
                    hit = np.flatnonzero(series.to_numpy() >= float(atr) * t)
                    ref = labels["atr_thresholds"][f"{side}_{t:g}"]
                    assert ref["reached"] == bool(len(hit))
                    assert ref["minutes"] == (int(hit[0]) + 1 if len(hit) else None)
                    thresholds += 1
    con.close()
(R / "independent_label_verification.json").write_text(
    json.dumps(
        {
            "horizons_checked": n,
            "complete_horizons": complete,
            "atr_threshold_labels_checked": thresholds,
            "failures": 0,
            "method": "Direct Development-only pandas raw-minute slices; no outcome helper called",
        },
        indent=2,
    )
)
print(n, complete, thresholds)
