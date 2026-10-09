"""All-trade and time-of-day results without fitting time filters."""

import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.o15l_clear_hold.run import P, write, save
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
    for direction in ["ALL", "LONG"]:
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
        session_quality="Source XNYS RTH calendar, including early closes",
        confidence=cluster_intervals(primary),
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
    risks = primary.risk_points.quantile([0, 0.25, 0.5, 0.75, 1]).to_dict()
    top = primary.nlargest(5, "risk_points")
    write("largest_risk_trades.csv", top)
    save(
        "risk_distribution.json",
        dict(
            quantiles=risks,
            top5_net=float(top.net_pnl_usd.sum()),
            top5_share_of_net=float(top.net_pnl_usd.sum() / primary.net_pnl_usd.sum()),
        ),
    )
    bottom = int(eq.drawdown_usd.to_numpy().argmax())
    curve = np.r_[0, primary.net_pnl_usd.cumsum().to_numpy()]
    peak = int(np.argmax(curve[: bottom + 1]))
    recovery = np.flatnonzero(curve[bottom + 2 :] >= curve[peak])
    dd = dict(
        max_dd_usd=float(eq.drawdown_usd.max()),
        peak_date="INITIAL" if peak == 0 else primary.iloc[peak - 1].exit_time_ny,
        bottom_date=primary.iloc[bottom].exit_time_ny,
        recovery_date=(
            None
            if not len(recovery)
            else primary.iloc[bottom + 1 + int(recovery[0])].exit_time_ny
        ),
        top5_net_during_drawdown=float(
            primary.iloc[peak : bottom + 1]
            .loc[lambda g: g.signal_id.isin(top.signal_id), "net_pnl_usd"]
            .sum()
        ),
    )
    save("drawdown_analysis.json", dd)
    summary["risk_distribution"] = dict(
        quantiles=risks, top5_net=float(top.net_pnl_usd.sum())
    )
    summary["drawdown"] = dd
    save("study_summary.json", summary)
    text = [
        "# O15L upward clearance-and-hold: sequential Development test",
        "",
        "**DEVELOPMENT_ONLY_NOT_VALIDATED.** Selected after prior Development research. This is not independent validation.",
        "",
        "The original root break is above the opening fifteen-minute LOW. Other known levels within one causal ATR are frozen at that break. A later clearance close followed by a full candle above the barrier triggers entry. Stop: original root break low minus one tick. Fixed 1R, one micro, one position at a time. Actual XNYS session close, including early closes. No new filters.",
        "",
        "## Reconciliation and costs",
        "",
        "280 causal confirmations reproduce exactly; 279 were executable independent diagnostics. One at session close cannot enter. Position-open confirmations are discarded, never queued. All selected fills and excursions reconcile to their previous independent diagnostics. Zero/one/two adverse ticks each side; $0.73 per side actual fees.",
        "",
        table(
            summaries,
            ["ticks", "raw_breakouts", "POSITION_OPEN", "AT_SESSION_CLOSE"]
            + cols
            + [
                "gross_usd",
                "fees_usd",
                "max_dd_r",
                "target_exits",
                "stop_exits",
                "session_exits",
                "conflicts",
                "adverse_stop_gaps",
            ],
        ),
        "",
        "## Yearly",
        "",
        table(rows["yearly"], ["year"] + cols),
        "",
        "## Comparison with previous independent diagnostics",
        "",
        "The prior overlapping 1-tick diagnostics had 279 trades, +$3,362.16, PF 1.237624 and average net R +0.066450. The only new constraint is chronological one-position selection; this is not a historical CSV filter selected by outcomes.",
        "",
        "## Uncertainty and risk",
        "",
        json.dumps(summary["confidence"], sort_keys=True),
        "",
        "Date-cluster bootstrap: 5,000 resamples, seed 1729. Intervals are descriptive and do not correct prior candidate selection. A positive dollar sum is not sufficient evidence of a repeatable edge.",
        "",
        json.dumps(summary["risk_distribution"], sort_keys=True),
        "",
        json.dumps(dd, sort_keys=True),
        "",
        "Top-five risk trades and their individual outcomes are exported. Closed-trade drawdown excludes unrealized loss. Exit-minute MFE/MAE includes the full minute; intraminute ordering is unknown.",
        "",
        "## Interpretation",
        "",
        "All four Development years are positive after costs, but 2023 contributes only $248.80. The date-cluster mean-R interval includes zero. Selection occurred after inspecting prior Development results; this does not establish a validated edge. Review the entry charts and freeze any future Validation protocol before accessing reserved data. No additional filters are suggested by this test.",
        "",
        "## Monthly",
        "",
        table(rows["monthly"], ["month"] + cols),
        "",
        "## Entry time: descriptive only",
        "",
        table(timing, ["direction", "time_bucket"] + cols),
        "",
        "No Validation or OOS outcomes read. No strategy optimization, no production execution changes. Charts show Development trades retrospectively. Source artifacts and market data remain unchanged.",
        "",
    ]
    (P / "O15L_CLEAR_HOLD_REPORT.md").write_text("\n".join(text))
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
        (ROOT / "scripts/o15l_clear_hold/viewer.html")
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
