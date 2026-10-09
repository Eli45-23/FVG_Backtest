"""Deterministic candle/bracket audits of predeclared chart samples."""

import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.o15l_clear_hold.run import P, write


def main():
    trades = pd.read_csv(P / "trades_1tick.csv").sort_values(
        ["entry_time_utc", "signal_id"]
    )
    bars = pd.read_parquet(P / "chart_bars.parquet").set_index("timestamp_utc")
    chosen = pd.concat(
        [trades.groupby("year").head(1), trades.nlargest(1, "risk_points")]
    ).drop_duplicates("signal_id")
    rows = []
    for t in chosen.to_dict("records"):
        at = pd.Timestamp(t["entry_time_utc"])
        root = pd.Timestamp(t["root_confirmation"])
        r = bars.loc[root - pd.Timedelta(minutes=5)]
        clearance = bars.loc[at - pd.Timedelta(minutes=10)]
        hold = bars.loc[at - pd.Timedelta(minutes=5)]
        assert r.is_complete_5m and clearance.is_complete_5m and hold.is_complete_5m
        assert float(r.close) > t["opening_low"]
        assert (
            float(clearance.close) > t["barrier_price"]
            and float(hold.low) > t["barrier_price"]
        )
        assert t["stop_price"] == float(r.low) - 0.25
        assert t["entry_price"] == float(hold.close) + 0.25
        assert (
            t["target_price"] - t["entry_price"]
            == t["risk_points"]
            == t["entry_price"] - t["stop_price"]
        )
        assert (
            pd.Timestamp(t["level_available_at"])
            <= root
            < at
            <= pd.Timestamp(t["exit_time_utc"])
        )
        rows.append(
            dict(
                signal_id=t["signal_id"],
                year=t["year"],
                date=t["date"],
                root_confirmation=root,
                clearance_confirmation=t["clearance_confirmation"],
                hold_confirmation=at,
                opening_low=t["opening_low"],
                barrier=t["barrier_price"],
                stop=t["stop_price"],
                entry=t["entry_price"],
                target=t["target_price"],
                checks="PASS",
                selection=(
                    "FIRST_OF_YEAR"
                    if t["signal_id"] in set(trades.groupby("year").head(1).signal_id)
                    else "MAXIMUM_RISK"
                ),
            )
        )
    write("chart_audit.csv", rows)
    print("PASS deterministic candle/bracket chart audit", len(rows))


if __name__ == "__main__":
    main()
