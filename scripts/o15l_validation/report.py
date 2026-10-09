"""Apply the preregistered gate to the primary run, without selecting new rules."""

import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.o15l_validation.detect import P, write, save
from scripts.o15l_validation.gate import classify
from scripts.opening15_breakout.report import stats, cluster_intervals
from scripts.zone_reaction_backtest.report import table


def main():
    trades = pd.read_csv(P / "all_scenario_trades.csv")
    audit = pd.read_csv(P / "signal_audit.csv")
    raw = pd.read_csv(P / "causal_signals.csv")
    v = json.loads((P / "execution_verification.json").read_text())
    protocol = json.loads((P / "protocol.json").read_text())
    primary = (
        trades[trades.ticks.eq(1)].sort_values(["entry_time_utc", "signal_id"]).copy()
    )
    assert primary.date.between("2024-01-01", "2024-12-31").all()
    costs = []
    for ticks, g in trades.groupby("ticks"):
        g = g.sort_values(["entry_time_utc", "signal_id"])
        times = pd.to_datetime(g.entry_time_utc, utc=True).reset_index(drop=True)
        ends = pd.to_datetime(g.exit_time_utc, utc=True).reset_index(drop=True)
        assert (times.iloc[1:].to_numpy() >= ends.iloc[:-1].to_numpy()).all()
        counts = audit[audit.ticks.eq(ticks)].selection_status.value_counts().to_dict()
        assert sum(counts.values()) == len(raw) and g.signal_id.is_unique
        costs.append(
            dict(
                ticks=int(ticks),
                **stats(g),
                **{k: int(val) for k, val in counts.items()},
            )
        )
    write("cost_sensitivity.csv", costs)
    interval = cluster_intervals(primary)
    unresolved = int(audit.selection_status.eq("EXECUTION_DATA_UNAVAILABLE").sum())
    primary_stats = next(c for c in costs if c["ticks"] == 1)
    gate = classify(primary_stats, interval, unresolved, protocol)
    primary["month"] = primary.date.str[:7]
    primary["quarter"] = pd.to_datetime(primary.date).dt.to_period("Q").astype(str)
    groups = {}
    for name, col in [
        ("monthly", "month"),
        ("quarterly", "quarter"),
        ("time_of_day", "time_bucket"),
    ]:
        groups[name] = [
            dict(**{col: key}, **stats(g)) for key, g in primary.groupby(col)
        ]
        write(name + ".csv", groups[name])
    eq = primary[["signal_id", "exit_time_ny", "net_pnl_usd", "result_r"]].copy()
    eq["equity_usd"] = primary.net_pnl_usd.cumsum()
    eq["peak_usd"] = eq.equity_usd.cummax().clip(lower=0)
    eq["drawdown_usd"] = eq.peak_usd - eq.equity_usd
    write("equity.csv", eq)
    write("largest_risk_trades.csv", primary.nlargest(5, "risk_points"))
    summary = dict(
        status=gate["classification"],
        segment="validation",
        start="2024-01-01",
        end_exclusive="2025-01-01",
        primary=primary_stats,
        confidence=interval,
        gate=gate,
        raw_breakouts=len(raw),
        raw_roots=v["raw_roots"],
        obstacle_opportunities=v["obstacle_opportunities"],
        unresolved_execution=unresolved,
        risk_quantiles={
            str(k): float(val)
            for k, val in primary.risk_points.quantile([0, 0.25, 0.5, 0.75, 1]).items()
        },
        top5_risk_net=float(primary.nlargest(5, "risk_points").net_pnl_usd.sum()),
        oos_accessed=False,
    )
    save("study_summary.json", summary)
    save("validation_gate.json", gate)
    cols = [
        "trades",
        "unique_dates",
        "wins",
        "losses",
        "win_pct",
        "net_usd",
        "profit_factor",
        "avg_net_r",
        "max_dd_usd",
        "max_dd_r",
    ]
    text = [
        "# O15L clearance-and-hold: 2024 Validation",
        "",
        f"**{gate['classification']}**",
        "",
        "Unchanged full-session setup. Root O15L upward break, frozen nearby-level clearance then full hold. Original root low minus one tick stop, fixed 1R target, one micro, one position at a time. No 10:30 filter and no stop management. Includes actual XNYS early closes. All-in fees $0.73 per side; primary one adverse tick each side.",
        "",
        "## Results",
        "",
        table(
            costs,
            ["ticks"]
            + cols
            + ["gross_usd", "fees_usd", "POSITION_OPEN", "AT_SESSION_CLOSE"],
        ),
        "",
        f"Raw upward roots: {v['raw_roots']}; obstacle opportunities: {v['obstacle_opportunities']}; causal hold confirmations: {len(raw)}. Unresolved execution rows: {unresolved}.",
        "",
        "## Preregistered decision",
        "",
        table(
            [{"criterion": k, "passed": val} for k, val in gate["checks"].items()],
            ["criterion", "passed"],
        ),
        "",
        "Minimum 30 trades / 30 dates; net USD > 0, mean net R > 0, PF > 1, max closed R drawdown <= 7.031524868463503. Positive lower 95% date-cluster mean-R bound is required for full support; otherwise positive economics alone are conditional. Sensitivity cases cannot rescue a failing primary. These thresholds were committed before this task read 2024 bars.",
        "",
        json.dumps(interval, sort_keys=True),
        "",
        "The percentile bootstrap resamples NY dates 5,000 times, seed 1729. This single frozen candidate was selected using Development; Validation outcomes cannot now be used to adjust rules while retaining the same validation claim. 2024 was previously inspected by unrelated project research, so it is not universally untouched market history.",
        "",
        "## Quarterly",
        "",
        table(groups["quarterly"], ["quarter"] + cols),
        "",
        "## Monthly",
        "",
        table(groups["monthly"], ["month"] + cols),
        "",
        "## Entry time — descriptive, no selected time filter",
        "",
        table(groups["time_of_day"], ["time_bucket"] + cols),
        "",
        "## Risk and execution",
        "",
        json.dumps(
            {
                "risk_quantiles": summary["risk_quantiles"],
                "top5_risk_net": summary["top5_risk_net"],
            },
            sort_keys=True,
        ),
        "",
        "Risk concentration is descriptive; no trades removed. One-minute stop-first ordering, adverse gaps and strict missing owned minutes use the existing executor. Full exit-minute extrema enter MFE/MAE; intraminute order is unknown. Closed drawdown excludes unrealized exposure and is not a future maximum-loss guarantee.",
        "",
        "## Preservation and evidence",
        "",
        "Portable detector exactly reproduced 280 Development confirmations and 865 waiting opportunities. All three Development scenarios reproduced the same 273 sequential trades and exact serialized economic fields before Validation access. OOS (2025+) was not decoded or revealed. Old study artifacts and normal database records were not modified. Complete trades, audits, code/source hashes, access ledger and deterministic checks are retained locally. No automatic OOS run or live deployment.",
        "",
    ]
    (P / "VALIDATION_REPORT.md").write_text("\n".join(text))
    timing = [dict(r, direction="ALL") for r in groups["time_of_day"]] + [
        dict(r, direction="LONG") for r in groups["time_of_day"]
    ]
    data = dict(
        summary=summary,
        costs=costs,
        yearly=[dict(year=2024, **stats(primary))],
        direction=[dict(direction="LONG", **stats(primary))],
        monthly=groups["monthly"],
        time=timing,
        time_yearly=[
            dict(r, year=2024, direction="LONG") for r in groups["time_of_day"]
        ],
        equity=json.loads(eq.to_json(orient="records")),
        trades=json.loads(primary.to_json(orient="records")),
    )
    template = (ROOT / "scripts/o15l_validation/viewer.html").read_text()
    html = template.replace(
        "/*DATA*/",
        json.dumps(data, separators=(",", ":"), allow_nan=False).replace("</", "<\\/"),
    )
    (P / "study.html").write_text(html)
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
