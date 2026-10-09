"""All-trade and time-of-day results without fitting time filters."""

import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.opening15_breakout.run import P, write, save
from scripts.opening15_breakout.core import BINS
from scripts.zone_reaction_backtest.report import table


def stats(g):
    g = g.sort_values(["entry_time_utc", "signal_id"])
    n = len(g)
    net = g.net_pnl_usd
    gross = g.gross_pnl_usd
    loss = -net[net < 0].sum()
    eq = np.r_[0, net.cumsum().to_numpy()]
    rs = np.r_[0, g.result_r.cumsum().to_numpy()]
    wins = losses = mw = ml = 0
    for v in net:
        wins = wins + 1 if v > 0 else 0
        losses = losses + 1 if v < 0 else 0
        mw = max(mw, wins)
        ml = max(ml, losses)
    return dict(
        trades=n,
        unique_dates=g.date.nunique(),
        wins=int((net > 0).sum()),
        losses=int((net < 0).sum()),
        breakeven=int((net == 0).sum()),
        win_pct=100 * (net > 0).mean() if n else None,
        gross_usd=float(gross.sum()),
        fees_usd=float(g.commission_usd.sum()),
        net_usd=float(net.sum()),
        profit_factor=float(net[net > 0].sum() / loss) if loss else None,
        gross_profit=float(gross[gross > 0].sum()),
        gross_loss=float(gross[gross < 0].sum()),
        average_trade=float(net.mean()) if n else None,
        median_trade=float(net.median()) if n else None,
        avg_net_r=float(g.result_r.mean()) if n else None,
        median_net_r=float(g.result_r.median()) if n else None,
        total_net_r=float(g.result_r.sum()),
        max_dd_usd=float((np.maximum.accumulate(eq) - eq).max()),
        max_dd_r=float((np.maximum.accumulate(rs) - rs).max()),
        average_risk=float(g.risk_points.mean()) if n else None,
        median_risk=float(g.risk_points.median()) if n else None,
        max_risk=float(g.risk_points.max()) if n else None,
        average_duration=float(g.duration_minutes.mean()) if n else None,
        median_duration=float(g.duration_minutes.median()) if n else None,
        mean_mfe=float(g.mfe_points.mean()) if n else None,
        mean_mae=float(g.mae_points.mean()) if n else None,
        target_exits=int(g.exit_reason.eq("TARGET").sum()),
        stop_exits=int(g.exit_reason.eq("STOP").sum()),
        session_exits=int(g.exit_reason.eq("SESSION_CLOSE").sum()),
        conflicts=int(g.same_minute_stop_target_conflict.eq(True).sum()),
        adverse_stop_gaps=int(g.adverse_stop_gap.eq(True).sum()),
        max_consecutive_wins=mw,
        max_consecutive_losses=ml,
    )


def cluster_intervals(g):
    if g.date.nunique() < 2:
        return dict(
            mean_r_ci_low=None,
            mean_r_ci_high=None,
            mean_usd_ci_low=None,
            mean_usd_ci_high=None,
        )
    by = g.groupby("date").agg(
        count=("signal_id", "size"), r=("result_r", "sum"), usd=("net_pnl_usd", "sum")
    )
    v = by.to_numpy(float)
    rng = np.random.default_rng(1729)
    samples = v[rng.integers(0, len(v), size=(5000, len(v)))].sum(axis=1)
    rr = samples[:, 1] / samples[:, 0]
    usd = samples[:, 2] / samples[:, 0]
    return dict(
        mean_r_ci_low=float(np.quantile(rr, 0.025)),
        mean_r_ci_high=float(np.quantile(rr, 0.975)),
        mean_usd_ci_low=float(np.quantile(usd, 0.025)),
        mean_usd_ci_high=float(np.quantile(usd, 0.975)),
    )


def main():
    trades = pd.read_csv(P / "all_scenario_trades.csv", low_memory=False)
    audit = pd.read_csv(P / "signal_audit.csv", low_memory=False)
    raw = pd.read_csv(P / "all_breakouts.csv")
    primary = trades[trades.ticks == 1].copy()
    primary["month"] = primary.date.str[:7]
    coverage = pd.read_csv(P / "session_coverage.csv")
    assert len(audit) == len(raw) * 3
    summaries = []
    for ticks, g in trades.groupby("ticks"):
        a = audit[audit.ticks == ticks]
        assert g.signal_id.is_unique
        times = pd.to_datetime(
            g.sort_values("entry_time_utc").entry_time_utc, utc=True
        ).reset_index(drop=True)
        ends = pd.to_datetime(
            g.sort_values("entry_time_utc").exit_time_utc, utc=True
        ).reset_index(drop=True)
        assert (times.iloc[1:].to_numpy() >= ends.iloc[:-1].to_numpy()).all()
        summaries.append(
            dict(
                ticks=int(ticks),
                raw_breakouts=len(raw),
                **stats(g),
                **{
                    str(k): int(v) for k, v in a.selection_status.value_counts().items()
                },
            )
        )
    write("cost_sensitivity.csv", summaries)
    rows = {}
    for name, cols in [
        ("yearly", ["year"]),
        ("direction", ["direction"]),
        ("yearly_direction", ["year", "direction"]),
        ("monthly", ["month"]),
        ("time_yearly", ["time_bucket", "year", "direction"]),
    ]:
        out = []
        for key, g in primary.groupby(cols, sort=True):
            key = key if isinstance(key, tuple) else (key,)
            out.append(dict(zip(cols, key), **stats(g)))
        rows[name] = out
        write(name + ".csv", out)
    timing = []
    for direction in ["ALL", "LONG", "SHORT"]:
        for window in BINS:
            g = primary[
                (primary.time_bucket == window)
                & ((primary.direction == direction) if direction != "ALL" else True)
            ]
            a = audit[
                (audit.ticks == 1)
                & (audit.time_bucket == window)
                & ((audit.direction == direction) if direction != "ALL" else True)
            ]
            annual = g.groupby("year").agg(
                net=("net_pnl_usd", "sum"), r=("result_r", "mean")
            )
            timing.append(
                dict(
                    direction=direction,
                    time_bucket=window,
                    raw_breakouts=len(a),
                    position_open_skips=int(
                        a.selection_status.eq("POSITION_OPEN").sum()
                    ),
                    **stats(g),
                    **cluster_intervals(g),
                    positive_dollar_years=int((annual.net > 0).sum()),
                    positive_r_years=int((annual.r > 0).sum()),
                    years_present=len(annual),
                )
            )
    write("time_of_day.csv", timing)
    ts = []
    for key, g in trades.groupby(["ticks", "time_bucket", "direction"]):
        ts.append(
            dict(ticks=int(key[0]), time_bucket=key[1], direction=key[2], **stats(g))
        )
    write("time_cost_sensitivity.csv", ts)
    primary = primary.sort_values(["entry_time_utc", "signal_id"])
    eq = primary[["signal_id", "exit_time_ny", "net_pnl_usd", "result_r"]].copy()
    eq["equity_usd"] = primary.net_pnl_usd.cumsum()
    eq["peak_usd"] = eq.equity_usd.cummax().clip(lower=0)
    eq["drawdown_usd"] = eq.peak_usd - eq.equity_usd
    write("equity.csv", eq)
    selected = {t: set(trades.loc[trades.ticks.eq(t), "signal_id"]) for t in [0, 1, 2]}
    write(
        "scenario_selection_changes.csv",
        [
            dict(
                ticks=t,
                selected=len(selected[t]),
                shared_with_primary=len(selected[t] & selected[1]),
                only_in_scenario=len(selected[t] - selected[1]),
                primary_not_in_scenario=len(selected[1] - selected[t]),
            )
            for t in [0, 1, 2]
        ],
    )
    summary = dict(
        status="DEVELOPMENT_ONLY_NOT_VALIDATED",
        segment="development",
        raw_breakouts=len(raw),
        raw_dates=raw.date.nunique(),
        primary=next(x for x in summaries if x["ticks"] == 1),
        session_quality={
            str(k): int(v) for k, v in coverage.status.value_counts().items()
        },
        unresolved_execution=int(
            audit.selection_status.eq("EXECUTION_DATA_UNAVAILABLE").sum()
        ),
        time_bins_frozen=True,
        automatic_time_filter_selected=False,
    )
    save("study_summary.json", summary)
    cols = [
        "trades",
        "unique_dates",
        "win_pct",
        "net_usd",
        "profit_factor",
        "average_trade",
        "avg_net_r",
        "max_dd_usd",
    ]
    text = [
        "# Opening 15-minute breakout · 50-point target",
        "",
        "**DEVELOPMENT_ONLY_NOT_VALIDATED.** Sequential one-position, one-micro backtest, 2020–2023 only. Opening high/low fixed at 09:45; first subsequent 5m close outside triggers. Repeated crossings permitted, no time filter. Exact preceding-candle stop with no buffer. Fifty-point target from executed entry, no management. Full XNYS sessions only.",
        "",
        "## Primary result and costs",
        "",
        table(
            summaries,
            ["ticks", "raw_breakouts", "POSITION_OPEN", "AT_SESSION_CLOSE"]
            + cols
            + [
                "gross_usd",
                "fees_usd",
                "target_exits",
                "stop_exits",
                "session_exits",
                "conflicts",
                "adverse_stop_gaps",
            ],
        ),
        "",
        "One adverse entry tick and one adverse exit tick are primary; zero/two tick runs keep the same causal signals but reselect positions as fills change. Actual user fees $0.73/side/micro, $1.46 round trip. Native 1m fills, stop-first conflicts and adverse stop gaps are unchanged. Only owned post-confirmation minutes can fill. Missing data never rejects a signal using future knowledge. Any unresolved execution prevents an unqualified full-period performance claim.",
        "",
        "## Yearly results",
        "",
        table(rows["yearly"], ["year"] + cols),
        "",
        "## Long versus short",
        "",
        table(rows["direction"], ["direction"] + cols),
        "",
        "## Time windows — descriptive, not an optimized entry filter",
        "",
        "Bins use the actual confirmed entry time in New York, not the start of the trigger candle. The first possible entry is 09:50. Every defined window remains in the report. Bootstrap 95% intervals resample trading dates, 5,000 repetitions with seed 1729; they are exploratory and not adjusted for selecting the best of multiple windows. Subset drawdowns do not represent a rerun restricted to that window.",
        "",
        table(
            timing,
            ["direction", "time_bucket", "raw_breakouts", "position_open_skips"]
            + cols
            + [
                "mean_r_ci_low",
                "mean_r_ci_high",
                "mean_usd_ci_low",
                "mean_usd_ci_high",
                "positive_dollar_years",
                "positive_r_years",
                "years_present",
            ],
        ),
        "",
        "## Time windows by year and direction",
        "",
        table(rows["time_yearly"], ["time_bucket", "year", "direction"] + cols),
        "",
        "## Monthly",
        "",
        table(rows["monthly"], ["month"] + cols),
        "",
        "## Coverage, accounting and limitations",
        "",
        json.dumps(summary["session_quality"], sort_keys=True),
        "",
        f"All {len(raw):,} breakouts and their selected/skipped reasons are retained for every cost scenario. Full opening ranges reconcile exactly to fifteen source minutes. Independent vector and stateful detectors agree. No missing or incomplete candles are bridged. Source hashes and source studies remain unchanged.",
        "",
        "This tests one specified target and stop, not their optimality. There is no starting-equity, margin or return-percentage model. Dollar results assume one MNQ micro. Intraminute excursion ordering is unknown; exit-minute MFE/MAE include the full exit minute. Closed-equity drawdown excludes unrealized movement. Results are in-sample Development evidence, not Validation. A strongest observed time window is not automatically the best future trading window.",
        "",
        "The complete trade list, all breakouts, audit reasons, coverage, costs, yearly/monthly/time tables and chronological equity are exported locally. Chart inspections show Development candles only. No Validation/OOS outcomes, data download or production-executor change.",
        "",
    ]
    (P / "OPENING15_BREAKOUT_50PT_REPORT.md").write_text("\n".join(text))
    data = dict(
        summary=summary,
        costs=summaries,
        yearly=rows["yearly"],
        direction=rows["direction"],
        time=timing,
        time_yearly=rows["time_yearly"],
        monthly=rows["monthly"],
        equity=json.loads(eq.to_json(orient="records")),
        trades=json.loads(primary.to_json(orient="records")),
    )
    data = json.loads(json.dumps(data, default=str))
    (P / "study.html").write_text(
        (ROOT / "scripts/opening15_breakout/viewer.html")
        .read_text()
        .replace(
            "/*DATA*/",
            json.dumps(data, separators=(",", ":"), allow_nan=False).replace(
                "</", "<\\/"
            ),
        )
    )
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
