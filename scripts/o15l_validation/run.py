"""Isolated Validation adapter; production fills and frozen definitions unchanged."""

import sys, json, hashlib, subprocess
from pathlib import Path
from decimal import Decimal as D
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.o15l_validation.detect import (
    P,
    SOURCE,
    sha,
    write,
    save,
    load_bars,
    generate,
)
from scripts.opening15_breakout.core import bucket, selection_reason, NY
from scripts.swing_low_feasibility.core import independent_fill
from scripts.pml_feasibility.core import short_fill
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref


def prepare(raw):
    signals = []
    for row in raw:
        at = pd.Timestamp(row["timestamp_utc"])
        known = json.loads(row["known_levels"])
        signals.append(
            dict(
                row,
                signal_id=hashlib.sha256(
                    ("o15l-clear-hold-v1|" + row["entry_id"]).encode()
                ).hexdigest(),
                source_entry_id=row["entry_id"],
                direction="LONG",
                entry_time_utc=at,
                entry_time_ny=at.tz_convert(NY),
                session_close=pd.Timestamp(row["session_close"]),
                time_bucket=bucket(at),
                opening_low=row["level_price"],
                opening_high=next(
                    float(l["price"]) for l in known if l["level"] == "O15H"
                ),
                root_confirmation=pd.Timestamp(row["original_timestamp"]),
                clearance_confirmation=at - pd.Timedelta(minutes=5),
            )
        )
    return sorted(signals, key=lambda s: (s["entry_time_utc"], s["signal_id"]))


def minute_days(start, end, identity):
    assert "2020-01-01" <= start < end <= "2025-01-01"
    path = ROOT / "outputs/data" / identity["dataset"]["files"]["minutes"]["name"]
    assert sha(path) == identity["dataset"]["files"]["minutes"]["sha256"]
    lo = pd.Timestamp(start, tz=NY).tz_convert("UTC")
    hi = pd.Timestamp(end, tz=NY).tz_convert("UTC")
    f = (
        pq.read_table(path, filters=[("ts_event", ">=", lo), ("ts_event", "<", hi)])
        .to_pandas()
        .reset_index()
    )
    assert f.ts_event.is_unique and f.ts_event.between(lo, hi, inclusive="left").all()
    for c in ["open", "high", "low", "close"]:
        f[c] = f[c].map(lambda v: D(int(v)).scaleb(-9))
    f["date"] = f.ts_event.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    days = {}
    for d, g in f.groupby("date"):
        g = g.set_index("ts_event").sort_index()
        g.index = g.index.as_unit("ns")
        days[d] = g
    return days, len(f)


def simulate(signals, days, prefix=""):
    def out(name, rows):
        write(prefix + name, rows)

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
    out("signal_audit.csv", audit)
    out("all_scenario_trades.csv", trades)
    for ticks in [0, 1, 2]:
        out(f"trades_{ticks}tick.csv", [t for t in trades if t["ticks"] == ticks])
    return trades, audit, checks


def main(mode):
    protocol = json.loads((P / "protocol.json").read_text())
    assert (
        sha(ROOT / "docs/O15L_VALIDATION_PREREGISTRATION_V1.md")
        == protocol["specification_sha256"]
    )
    assert (
        sha(ROOT / "docs/O15L_CLEAR_HOLD_SEQUENTIAL_V1.md")
        == protocol["development_specification_sha256"]
    )
    gate = json.loads((P / "development_detection_gate.json").read_text())
    assert gate["status"] == "PASS"
    if mode == "development":
        bars, sessions, identity = load_bars("2020-01-01", "2024-01-01")
        raw, _, _, _ = generate(bars, sessions, "2020-01-01", "2024-01-01")
        days, _ = minute_days("2020-01-01", "2024-01-01", identity)
        trades, audit, checks = simulate(prepare(raw), days, "development_")
        for ticks in [0, 1, 2]:
            old = (
                pd.read_csv(
                    ROOT / f"work/o15l-clear-hold-sequential-v1/trades_{ticks}tick.csv"
                )
                .set_index("signal_id")
                .sort_index()
            )
            new = (
                pd.read_csv(P / f"development_trades_{ticks}tick.csv")
                .set_index("signal_id")
                .sort_index()
            )
            assert list(old.index) == list(new.index) and len(new) == 273
            for key in [
                "entry_time_utc",
                "exit_time_utc",
                "exit_reason",
                "entry_price",
                "stop_price",
                "target_price",
                "net_pnl_usd",
                "result_r",
                "mfe_points",
                "mae_points",
                "mfe_r",
                "mae_r",
            ]:
                assert old[key].equals(new[key]), key
        save(
            "development_execution_gate.json",
            dict(
                status="PASS",
                checks=checks,
                trade_ids_and_economics_exact=True,
                detector_sha256=sha(ROOT / "scripts/o15l_validation/detect.py"),
                executor_sha256=sha(Path(__file__)),
                validation_rows_read=False,
            ),
        )
        return
    assert mode == "validation"
    gate = json.loads((P / "development_execution_gate.json").read_text())
    assert gate["status"] == "PASS"
    assert gate["detector_sha256"] == sha(
        ROOT / "scripts/o15l_validation/detect.py"
    ) and gate["executor_sha256"] == sha(Path(__file__))
    code = {
        str(p.relative_to(ROOT)): sha(p)
        for p in sorted((ROOT / "engine").rglob("*.py"))
    }
    record = dict(
        action="READ_VALIDATION_2024_ONLY",
        timestamp_utc=pd.Timestamp.now(tz="UTC").isoformat(),
        protocol_sha256=sha(P / "protocol.json"),
        preregistration_commit="6b66c12",
        end_exclusive="2025-01-01",
        oos_authorized=False,
        code_hashes=code,
    )
    with (P / "access_ledger.jsonl").open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    # December Development warmup only; no Validation trades before scoring start.
    bars, sessions, identity = load_bars("2023-12-01", "2025-01-01")
    raw, roots, opps, coverage = generate(bars, sessions, "2024-01-01", "2025-01-01")
    signals = prepare(raw)
    write("causal_signals.csv", signals)
    write("root_signals.csv", roots)
    write("waiting_opportunities.csv", opps)
    write("level_coverage.csv", coverage)
    days, n = minute_days("2024-01-01", "2025-01-01", identity)
    trades, audit, checks = simulate(signals, days)
    dates = {s["date"] for s in signals}
    bars["date"] = bars.timestamp_utc.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    chart = bars[bars.date.isin(dates)].copy()
    chart = chart[
        [
            sessions[r.date][0] <= r.timestamp_utc < sessions[r.date][1]
            for r in chart.itertuples()
        ]
    ]
    chart.to_parquet(P / "chart_bars.parquet", index=False)
    hashes = {}
    for x in identity["dataset"]["files"].values():
        path = ROOT / "outputs/data" / x["name"]
        assert sha(path) == x["sha256"]
        hashes[str(path.relative_to(ROOT))] = x["sha256"]
    save(
        "execution_verification.json",
        dict(
            status="PASS",
            segment="validation",
            raw_signals=len(raw),
            raw_roots=len(roots),
            obstacle_opportunities=len(opps),
            native_independent_checks=checks,
            source_minutes=n,
            source_bars=len(bars),
            source_hashes_verified=hashes,
            calendar_sha256=identity["calendar"]["sha256"],
            dataset=identity["dataset"],
            oos_outcomes_read=False,
            production_execution_changed=False,
        ),
    )
    print(
        "Validation execution complete",
        len(raw),
        "confirmations",
        checks,
        "native checks",
        flush=True,
    )


if __name__ == "__main__":
    main(sys.argv[1])
