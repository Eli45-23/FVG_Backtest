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
    bucket,
    selection_reason,
    NY,
    independent_signals,
)
from scripts.level_combination.core import wait_entry
from scripts.swing_low_feasibility.core import independent_fill
from scripts.pml_feasibility.core import short_fill
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref

P = ROOT / "work/o15l-clear-hold-sequential-v1"
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
        ROOT / "docs/O15L_CLEAR_HOLD_SEQUENTIAL_V1.md"
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
    old = ROOT / "work/level-combination-study-v1"
    old_manifest = json.loads((old / "reproducibility_manifest.json").read_text())
    assert old_manifest["status"] == "PASS"
    for name in [
        "causal_signals.csv",
        "all_executions.csv",
        "waiting_opportunities.csv",
    ]:
        assert sha(old / name) == old_manifest["artifacts"][name]["sha256"]
        hashes[str((old / name).relative_to(ROOT))] = sha(old / name)
    raw = pd.read_csv(old / "causal_signals.csv")
    raw = raw[
        (raw.level_type == "O15L")
        & (raw.direction == "UP")
        & (raw.policy == "WAIT_CLEAR_HOLD")
    ]
    assert len(raw) == 280 and raw.entry_id.is_unique
    reference = pd.read_csv(old / "all_executions.csv", low_memory=False)
    reference = reference[
        reference.entry_id.isin(raw.entry_id) & reference.target_r.eq(1)
    ]
    assert len(reference) == 840
    assert all(
        len(
            reference[
                (reference.ticks == t) & (reference.execution_status == "COMPLETED")
            ]
        )
        == 279
        for t in [0, 1, 2]
    )
    refrows = reference.set_index(["entry_id", "ticks"])
    signals, reconciliation, chartbars = [], [], []
    for row in raw.to_dict("records"):
        at = pd.Timestamp(row["timestamp_utc"])
        root_at = pd.Timestamp(row["original_timestamp"])
        cl = pd.Timestamp(row["session_close"])
        assert "2020-01-01" <= row["date"] < "2024-01-01"
        bars = bar_days[row["date"]]
        root = bars[bars.timestamp_utc.eq(root_at - pd.Timedelta(minutes=5))].iloc[0]
        assert (
            float(root.low) == row["low"] and float(root.close) == row["original_close"]
        )
        assert root.close > D(str(row["level_price"])) and root.is_complete_5m
        event = dict(row, timestamp_utc=root_at, price_at_event=row["original_close"])
        found, reason = wait_entry(event, bars.itertuples(index=False))
        assert reason == "CONFIRMED" and found["timestamp_utc"] == at
        assert found["price_at_event"] == row["price_at_event"]
        known = json.loads(row["known_levels"])
        assert all(pd.Timestamp(l["availability"]) <= root_at for l in known)
        obstacles = [
            l
            for l in known
            if l["level"] != "O15L"
            and 0 < float(l["price"]) - row["original_close"] <= row["atr14"]
        ]
        assert max(float(l["price"]) for l in obstacles) == row["barrier_price"]
        sid = hashlib.sha256(
            ("o15l-clear-hold-v1|" + row["entry_id"]).encode()
        ).hexdigest()
        s = dict(
            row,
            signal_id=sid,
            source_entry_id=row["entry_id"],
            direction="LONG",
            entry_time_utc=at,
            entry_time_ny=at.tz_convert(NY),
            session_close=cl,
            time_bucket=bucket(at),
            opening_low=row["level_price"],
            opening_high=next(float(l["price"]) for l in known if l["level"] == "O15H"),
            root_confirmation=root_at,
            clearance_confirmation=at - pd.Timedelta(minutes=5),
        )
        signals.append(s)
        reconciliation.append(
            dict(
                signal_id=sid,
                source_entry_id=row["entry_id"],
                date=row["date"],
                causal_sequence_match=True,
                before_session_close=at < cl,
            )
        )
    signals.sort(key=lambda s: (s["entry_time_utc"], s["signal_id"]))
    for date in sorted({s["date"] for s in signals}):
        op, cl = sessions[date]
        g = bar_days[date]
        chartbars.extend(
            g[(g.timestamp_utc >= op) & (g.timestamp_utc < cl)][
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
    write("all_breakouts.csv", signals)
    write("signal_reconciliation.csv", reconciliation)
    pd.DataFrame(chartbars).to_parquet(P / "chart_bars.parquet", index=False)
    print(
        "Reconciled 280 causal confirmations / 279 prior executable events", flush=True
    )
    audit = []
    trades = []
    checks = 0
    for ticks in [0, 1, 2]:
        busy = None
        for s in signals:
            at = s["entry_time_utc"]
            cl = s["session_close"]
            entry = D(str(s["price_at_event"])) + D(".25") * ticks
            stop = D(str(s["low"])) - D(".25")
            risk = entry - stop
            economics = dict(
                entry_price=entry,
                stop_price=stop,
                risk_points=risk,
                risk_usd=risk * 2,
                target_price=ref.tick(entry + risk),
                target_r=D(1),
            )
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
            previous = refrows.loc[(s["source_entry_id"], ticks)]
            for key in ["entry_price", "stop_price", "target_price", "risk_points"]:
                assert float(economics[key]) == float(previous[key]), key
            for key in [
                "exit_price",
                "net_pnl_usd",
                "result_r",
                "mfe_points",
                "mae_points",
                "mfe_r",
                "mae_r",
                "duration_minutes",
            ]:
                assert format(float(trade[key]), ".12g") == format(
                    float(previous[key]), ".12g"
                ), key
            assert pd.Timestamp(previous.exit_time_utc) == trade["exit_time_utc"]
            assert previous.exit_reason == trade["exit_reason"]
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
