"""Independent vectorized audit of every waiting opportunity, without fill outcomes."""

import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scripts.level_combination.run import P, SOURCE, NY


def main():
    identity = json.loads((SOURCE / "source_identity.json").read_text())
    start = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC")
    end = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC")
    b = (
        pq.read_table(
            ROOT / "outputs/data" / identity["dataset"]["files"]["bars"]["name"],
            filters=[("timestamp_utc", ">=", start), ("timestamp_utc", "<", end)],
        )
        .to_pandas()
        .sort_values("timestamp_utc")
    )
    b["date"] = b.timestamp_utc.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    days = {d: g for d, g in b.groupby("date")}
    signals = pd.read_csv(P / "causal_signals.csv", low_memory=False)
    original = signals[signals.policy == "IMMEDIATE"].set_index("opportunity_id")
    a = pd.read_csv(P / "waiting_opportunities.csv")
    for r in a.itertuples():
        e = original.loc[r.opportunity_id]
        at = pd.Timestamp(e.timestamp_utc)
        close = pd.Timestamp(e.session_close)
        g = days[r.date]
        g = g[(g.timestamp_utc >= at) & (g.timestamp_utc < close)]
        expected = pd.date_range(
            at, periods=max(0, int((close - at).total_seconds() / 300)), freq="5min"
        )
        aligned = g.set_index("timestamp_utc").reindex(expected)
        direction = 1 if e.direction == "UP" else -1
        complete = aligned.is_complete_5m.fillna(False).to_numpy(bool)
        values = aligned[["open", "high", "low", "close"]].to_numpy(float)
        valid = (
            complete
            & np.isfinite(values).all(axis=1)
            & (values[:, 1] >= values[:, [0, 2, 3]].max(axis=1))
            & (values[:, 2] <= values[:, [0, 3]].min(axis=1))
        )
        closes = values[:, 3]
        reclaimed = (closes - float(e.level_price)) * direction <= 0
        gap = np.flatnonzero(~valid)
        cancel = np.flatnonzero(reclaimed)
        boundary = min(
            int(gap[0]) if len(gap) else len(values),
            int(cancel[0]) if len(cancel) else len(values),
        )
        full = (
            values[:, 2] > e.barrier_price
            if direction == 1
            else values[:, 1] < e.barrier_price
        )
        clear = (closes - e.barrier_price) * direction > 0
        matches = (
            np.flatnonzero(full[1:boundary] & clear[: max(0, boundary - 1)]) + 1
            if boundary > 1
            else []
        )
        if len(matches):
            confirmation = expected[int(matches[0])] + pd.Timedelta(minutes=5)
            assert r.reason == "CONFIRMED" and confirmation == pd.Timestamp(
                r.wait_timestamp
            )
        else:
            reason = (
                "MISSING_OR_INCOMPLETE_ADJACENCY"
                if boundary < len(values) and not valid[boundary]
                else "ROOT_RECLAIMED" if boundary < len(values) else "SESSION_ENDED"
            )
            assert r.reason == reason, (r.opportunity_id, r.reason, reason)
    print(
        json.dumps(
            {
                "status": "PASS",
                "independently_reconciled_waiting_opportunities": len(a),
                "confirmation_signals": int(a.wait_entered.sum()),
                "development_only": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
