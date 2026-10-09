"""Development only, sequential selection, unchanged native minute executor."""

import sys, json, hashlib
from pathlib import Path
from decimal import Decimal as D
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.opening15_breakout.core import (
    Detector,
    bracket,
    selection_reason,
    NY,
    independent_signals,
)
from scripts.swing_low_feasibility.core import independent_fill
from scripts.pml_feasibility.core import short_fill
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref

P = ROOT / "work/opening15-breakout-50pt-v1"
SOURCE = ROOT / "work/eight-level-reaction-entry-study-v1"


def sha(p):
    with open(p, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(name, value):
    (P / name).write_text(
        json.dumps(value, sort_keys=True, indent=2, default=str, allow_nan=False) + "\n"
    )


def write(name, rows):
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).to_csv(
        P / name, index=False, float_format="%.12g", lineterminator="\n"
    )


def main():
    protocol = json.loads((P / "protocol.json").read_text())
    assert protocol["specification_sha256"] == sha(
        ROOT / "docs/OPENING15_BREAKOUT_50PT_V1.md"
    )
    manifest = json.loads((SOURCE / "reproducibility_manifest.json").read_text())
    assert manifest["status"] == "PASS" and manifest["segment"] == "development"
    f = SOURCE / "source_identity.json"
    assert sha(f) == manifest["artifacts"]["source_identity.json"]["sha256"]
    identity = json.loads(f.read_text())
    hashes = {
        str(f.relative_to(ROOT)): sha(f),
        str((P / "protocol.json").relative_to(ROOT)): sha(P / "protocol.json"),
    }
    for name, h in identity["source_hashes"].items():
        assert sha(ROOT / name) == h
        hashes[name] = h
    start = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC")
    end = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC")
    frames = {}
    for kind, key in [("bars", "timestamp_utc"), ("minutes", "ts_event")]:
        f = ROOT / "outputs/data" / identity["dataset"]["files"][kind]["name"]
        frame = pq.read_table(
            f, filters=[(key, ">=", start), (key, "<", end)]
        ).to_pandas()
        if key not in frame:
            frame = frame.reset_index()
        assert (
            frame[key].is_unique
            and frame[key].between(start, end, inclusive="left").all()
        )
        if kind == "minutes":
            for c in ["open", "high", "low", "close"]:
                frame[c] = frame[c].map(lambda v: D(int(v)).scaleb(-9))
        frame["date"] = frame[key].dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
        frames[kind] = frame.sort_values(key)
    days = {}
    for date, g in frames["minutes"].groupby("date"):
        g = g.set_index("ts_event")
        g.index = g.index.as_unit("ns")
        days[date] = g
    bar_days = {date: g for date, g in frames["bars"].groupby("date")}
    sessions = {
        d: tuple(map(pd.Timestamp, v))
        for d, v in identity["calendar"]["sessions"].items()
        if "2020-01-01" <= d < "2024-01-01"
    }
    signals = []
    coverage = []
    chartbars = []
    for date, (op, cl) in sorted(sessions.items()):
        reason = "FULL_SESSION"
        if cl - op != pd.Timedelta(hours=6, minutes=30):
            reason = "HALF_DAY"
        g = bar_days.get(date, pd.DataFrame(columns=frames["bars"].columns))
        opening = g[g.timestamp_utc.isin(pd.date_range(op, periods=3, freq="5min"))]
        valid = len(opening) == 3 and opening.is_complete_5m.all()
        if reason == "FULL_SESSION" and not valid:
            reason = "OPENING_RANGE_UNAVAILABLE"
        high = opening.high.max() if valid else None
        low = opening.low.min() if valid else None
        quality = dict(
            date=date,
            session_open=op,
            session_close=cl,
            status=reason,
            opening_bars=len(opening),
            missing_opening_starts=";".join(
                str(a)
                for a in pd.date_range(op, periods=3, freq="5min")
                if a not in set(opening.timestamp_utc)
            ),
            incomplete_opening_starts=";".join(
                str(a) for a in opening.loc[~opening.is_complete_5m, "timestamp_utc"]
            ),
            opening_high=high,
            opening_low=low,
            available=op + pd.Timedelta(minutes=15),
            minute_reconciliation=False,
        )
        if valid:
            mins = days.get(date, pd.DataFrame()).reindex(
                pd.date_range(op, periods=15, freq="min")
            )
            assert (
                not mins[["open", "high", "low", "close", "volume"]].isna().any().any()
            )
            assert mins.high.max() == high and mins.low.min() == low
            for row in opening.itertuples():
                v = mins.loc[
                    row.timestamp_utc : row.timestamp_utc + pd.Timedelta(minutes=4)
                ]
                assert len(v) == 5 and (
                    row.open,
                    row.high,
                    row.low,
                    row.close,
                    row.volume,
                ) == (
                    v.open.iloc[0],
                    v.high.max(),
                    v.low.min(),
                    v.close.iloc[-1],
                    v.volume.sum(),
                )
            quality["minute_reconciliation"] = True
        coverage.append(quality)
        if reason != "FULL_SESSION":
            continue
        rth = g[(g.timestamp_utc >= op) & (g.timestamp_utc < cl)]
        detector = Detector(high, low, op + pd.Timedelta(minutes=15))
        found = []
        for row in rth.itertuples(index=False):
            s = detector.update(row)

            if s:
                found.append((s["entry_time_utc"], s["direction"]))
                signals.append(dict(**s, session_close=cl))
        assert sorted(found) == independent_signals(
            rth, high, low, op + pd.Timedelta(minutes=15)
        )
        chartbars.extend(
            rth[
                [
                    "timestamp_utc",
                    "open",
                    "high",
                    "low",
                    "close",
                    "is_complete_5m",
                    "date",
                ]
            ].to_dict("records")
        )
    assert len({s["signal_id"] for s in signals}) == len(signals)
    write("all_breakouts.csv", signals)
    write("session_coverage.csv", coverage)
    pd.DataFrame(chartbars).to_parquet(P / "chart_bars.parquet", index=False)
    print(
        "Causal breakouts",
        len(signals),
        "dates",
        len({s["date"] for s in signals}),
        flush=True,
    )
    audit = []
    trades = []
    checks = 0
    for ticks in [0, 1, 2]:
        busy = None
        for s in signals:
            at = s["entry_time_utc"]
            cl = s["session_close"]
            economics = bracket(s, ticks)
            reason = selection_reason(at, cl, busy, economics["risk_points"])
            record = dict(**s, **economics, ticks=ticks, quantity=1)
            if reason:
                audit.append(dict(**record, selection_status=reason))
                continue
            day = days[s["date"]]
            ix = pd.date_range(at, cl, freq="min", inclusive="left")
            missing = ix.difference(day.index)
            cutoff = missing[0] if len(missing) else cl
            arr = day.loc[
                (day.index >= at) & (day.index < cutoff),
                ["open", "high", "low", "close"],
            ].to_numpy(dtype=float)
            expected = len(ix)
            independent = (
                independent_fill if s["direction"] == "LONG" else short_fill
            )(
                arr,
                float(economics["entry_price"]),
                float(economics["stop_price"]),
                float(economics["target_price"]),
                ticks,
                expected,
            )
            sign = D(1) if s["direction"] == "LONG" else D(-1)
            assert (
                ref.tick(
                    economics["entry_price"]
                    + sign * economics["risk_points"] * economics["target_r"]
                )
                == economics["target_price"]
            )
            try:
                trade, _ = execute(
                    record,
                    day,
                    ref.Config(D(".73"), ticks),
                    1,
                    Entry(
                        s["direction"], economics["stop_price"], economics["target_r"]
                    ),
                    None,
                    {},
                    {},
                    cl,
                )
            except ValueError as error:
                assert "Missing execution minute" in str(error) and independent is None
                audit.append(
                    dict(
                        **record,
                        selection_status="EXECUTION_DATA_UNAVAILABLE",
                        first_missing_owned_minute=cutoff,
                    )
                )
                busy = cl
                continue
            assert independent is not None
            minute, exit_reason, price, conflict = independent
            assert (
                trade["exit_reason"] == exit_reason
                and float(trade["exit_price"]) == price
                and trade["same_minute_stop_target_conflict"] == conflict
            )
            assert trade["exit_time_utc"] == at + pd.Timedelta(minutes=minute + 1)
            assert trade["net_pnl_usd"] == (
                D(str(price)) - economics["entry_price"]
            ) * sign * 2 - D("1.46")
            assert (
                trade["final_stop_price"] == economics["stop_price"]
                and trade["management_event_count"] == 0
            )
            assert busy is None or at >= busy
            busy = trade["exit_time_utc"]
            checks += 1
            owned = arr[: minute + 1]
            entry = float(economics["entry_price"])
            assert float(trade["mfe_points"]) == max(
                0, owned[:, 1].max() - entry if sign == 1 else entry - owned[:, 2].min()
            )
            assert float(trade["mae_points"]) == max(
                0, entry - owned[:, 2].min() if sign == 1 else owned[:, 1].max() - entry
            )
            fields = [
                "exit_time_utc",
                "exit_time_ny",
                "exit_reason",
                "exit_price",
                "gross_pnl_usd",
                "commission_usd",
                "net_pnl_usd",
                "result_r",
                "gross_result_r",
                "duration_minutes",
                "mfe_points",
                "mae_points",
                "mfe_r",
                "mae_r",
                "same_minute_stop_target_conflict",
            ]
            trades.append(
                dict(
                    **record,
                    **{k: trade[k] for k in fields},
                    adverse_stop_gap=exit_reason == "STOP"
                    and (
                        owned[-1, 0] < float(economics["stop_price"])
                        if sign == 1
                        else owned[-1, 0] > float(economics["stop_price"])
                    ),
                )
            )
            audit.append(dict(**record, selection_status="SELECTED"))
        print("Scenario", ticks, "native checks", checks, flush=True)
    write("signal_audit.csv", audit)
    write("all_scenario_trades.csv", trades)
    for ticks in [0, 1, 2]:
        write(f"trades_{ticks}tick.csv", [t for t in trades if t["ticks"] == ticks])
    for name, h in hashes.items():
        assert sha(ROOT / name) == h
    save(
        "execution_verification.json",
        dict(
            raw_signals=len(signals),
            raw_dates=len({s["date"] for s in signals}),
            source_minutes=len(frames["minutes"]),
            source_bars=len(frames["bars"]),
            native_independent_checks=checks,
            source_hashes_verified=hashes,
            production_execution_changed=False,
            validation_oos_outcomes_read=False,
        ),
    )


if __name__ == "__main__":
    main()
