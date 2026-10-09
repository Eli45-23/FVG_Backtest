"""Descriptive results only: no parameter search or automatic strategy selection."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from scripts.zone_reaction_backtest.run import P, ROOT, sha

NAMES = {
    "A": "Penetrate, then full-candle rejection",
    "B": "Exact tap, then full-candle rejection",
    "C": "Full break and adjacent full-candle hold",
}


def metrics(g):
    n = len(g)
    if not n:
        return dict(
            trades=0,
            net_usd=0,
            gross_usd=0,
            fees_usd=0,
            wins=0,
            losses=0,
            win_rate=None,
            pf=None,
            average_r=None,
            median_r=None,
            total_r=0,
            max_drawdown_usd=0,
        )
    g = g.sort_values(["exit_time_utc", "trade_id"])
    p = g.net_pnl_usd.astype(float)
    r = g.result_r.astype(float)
    eq = np.r_[0, p.cumsum().to_numpy()]
    dd = np.maximum.accumulate(eq) - eq
    gp = p[p > 0].sum()
    gl = -p[p < 0].sum()
    return dict(
        trades=n,
        wins=int((p > 0).sum()),
        losses=int((p < 0).sum()),
        breakeven=int((p == 0).sum()),
        win_rate=float((p > 0).mean() * 100),
        net_usd=float(p.sum()),
        gross_usd=float(g.gross_pnl_usd.sum()),
        fees_usd=float(g.commission_usd.sum()),
        gross_profit_usd=float(gp),
        gross_loss_usd=float(gl),
        pf=float(gp / gl) if gl else None,
        average_trade_usd=float(p.mean()),
        average_r=float(r.mean()),
        median_r=float(r.median()),
        total_r=float(r.sum()),
        max_drawdown_usd=float(dd.max()),
        average_risk_points=float(g.risk_points.mean()),
        median_risk_points=float(g.risk_points.median()),
        max_risk_points=float(g.risk_points.max()),
        average_mfe_points=float(g.mfe_points.mean()),
        median_mfe_points=float(g.mfe_points.median()),
        average_mae_points=float(g.mae_points.mean()),
        median_mae_points=float(g.mae_points.median()),
        average_mfe_r=float(g.mfe_r.mean()),
        average_mae_r=float(g.mae_r.mean()),
        average_duration_minutes=float(g.duration_minutes.mean()),
        session_close_exits=int((g.exit_reason == "SESSION_CLOSE").sum()),
        same_minute_conflicts=int(g.same_minute_stop_target_conflict.sum()),
    )


def table(rows, columns):
    def fmt(v):
        if v is None or pd.isna(v):
            return "—"
        if isinstance(v, (float, np.floating)):
            return f"{v:,.3f}"
        return str(v)

    return (
        "| "
        + " | ".join(columns)
        + " |\n| "
        + " | ".join(["---"] * len(columns))
        + " |\n"
        + "\n".join(
            "| " + " | ".join(fmt(r.get(k)) for k in columns) + " |" for r in rows
        )
    )


def main():
    t = pd.read_csv(P / "all_trades.csv")
    a = pd.read_csv(P / "signal_selection_audit.csv")
    verification = json.loads((P / "execution_verification.json").read_text())
    summary = []
    yearly = []
    directions = []
    monthly = []
    episodes = []
    equity = []
    for setup in NAMES:
        g = t[t.setup == setup]
        sel = a[a.setup == setup]
        summary.append(
            dict(
                setup=setup,
                name=NAMES[setup],
                signals=len(sel),
                **metrics(g),
                selection_counts={
                    str(k): int(v)
                    for k, v in sel.selection_status.value_counts().items()
                },
            )
        )
        for year in range(2020, 2024):
            yearly.append(dict(setup=setup, year=year, **metrics(g[g.year == year])))
        for side in ["LONG", "SHORT"]:
            directions.append(
                dict(setup=setup, direction=side, **metrics(g[g.direction == side]))
            )
        for m in pd.period_range("2020-01", "2023-12", freq="M"):
            monthly.append(
                dict(
                    setup=setup,
                    month=str(m),
                    **metrics(g[g.date.str.startswith(str(m))]),
                )
            )
        for label, mask in [
            ("first", g.episode_number == 1),
            ("second", g.episode_number == 2),
            ("third+", g.episode_number >= 3),
        ]:
            episodes.append(dict(setup=setup, episode=label, **metrics(g[mask])))
        e = g.sort_values(["exit_time_utc", "trade_id"]).copy()
        e["equity_usd"] = e.net_pnl_usd.cumsum()
        e["peak_usd"] = e.equity_usd.cummax().clip(lower=0)
        e["drawdown_usd"] = e.peak_usd - e.equity_usd
        equity.extend(
            e[
                [
                    "setup",
                    "trade_id",
                    "exit_time_utc",
                    "net_pnl_usd",
                    "equity_usd",
                    "peak_usd",
                    "drawdown_usd",
                ]
            ].to_dict("records")
        )
    for name, rows in [
        ("summary", summary),
        ("yearly", yearly),
        ("direction", directions),
        ("monthly", monthly),
        ("episode", episodes),
        ("equity", equity),
    ]:
        if name == "summary":
            (P / "summary.json").write_text(
                json.dumps(rows, sort_keys=True, indent=2, allow_nan=False) + "\n"
            )
        else:
            pd.DataFrame(rows).to_csv(
                P / f"{name}.csv",
                index=False,
                float_format="%.12g",
                lineterminator="\n",
            )
    cols = [
        "setup",
        "trades",
        "wins",
        "losses",
        "win_rate",
        "net_usd",
        "pf",
        "average_r",
        "max_drawdown_usd",
    ]
    lines = [
        "# Four-hour zone reaction backtests — Development v1",
        "",
        "**DEVELOPMENT_ONLY_NOT_VALIDATED.** Human-label approval is no longer a prerequisite for this explicitly authorized mechanical experiment. It is not evidence of a trading edge.",
        "",
        "## Frozen experiment",
        "",
        "2020–2023 New York Development dates; accepted/resolved historical subset only. Supply/demand geometry, bar construction and lifecycle remain unchanged. Each setup is an independent account: one open position at a time, new contact episode required after exit. Results must not be added as though they were a combined portfolio.",
        "",
        "One MNQ micro; fixed 2R; stop one tick beyond the opposite zone edge; confirmed whole five-minute candle including wicks; native one-minute fills starting at confirmation. One adverse tick entry and exit plus actual $0.73/side fees. No holidays, half-days, management, maximum-risk or indicator filters.",
        "",
        "## Results after fees and slippage",
        "",
        table(summary, cols),
        "",
        "*A: penetrate then reject. B: exact boundary tap without penetration then reject. C: whole-candle break then immediate adjacent whole-candle confirmation.*",
        "",
        "Profit factor uses net winning/losing trade dollars. Gross P&L already includes adverse slippage but excludes fees; R uses original executed risk. Drawdown starts from zero and uses closed trades.",
        "",
        table(
            summary,
            [
                "setup",
                "signals",
                "gross_usd",
                "fees_usd",
                "net_usd",
                "total_r",
                "median_r",
                "average_risk_points",
                "median_risk_points",
                "max_risk_points",
            ],
        ),
        "",
        "## Year-by-year results",
        "",
        table(
            yearly,
            [
                "setup",
                "year",
                "trades",
                "win_rate",
                "net_usd",
                "pf",
                "average_r",
                "max_drawdown_usd",
            ],
        ),
        "",
        "## Long / short",
        "",
        table(
            directions,
            [
                "setup",
                "direction",
                "trades",
                "net_usd",
                "pf",
                "average_r",
                "max_drawdown_usd",
            ],
        ),
        "",
        "## Path and execution",
        "",
        table(
            summary,
            [
                "setup",
                "average_mfe_points",
                "average_mae_points",
                "average_mfe_r",
                "average_mae_r",
                "average_duration_minutes",
                "session_close_exits",
                "same_minute_conflicts",
            ],
        ),
        "",
        "MFE/MAE include the exit minute’s full range. Intraminute ordering is unknown; these excursions can include movement after the simulated exit. Stop-first resolves same-minute stop/target ambiguity. Native adverse stop-gap fills are retained.",
        "",
        "## Signal selection audit",
        "",
    ]
    for row in summary:
        lines.append(
            f"- {row['setup']}: {json.dumps(row['selection_counts'],sort_keys=True)}"
        )
    lines += [
        "",
        "## Source and causality checks",
        "",
        f"Replayed {verification['zones']} accepted zones (168 supply, 152 demand) and reproduced saved formation identities and lifecycle invalidations exactly. {verification['calendar_unresolved_dates']} unresolved calendar dates remain excluded. {verification['eligible_full_sessions']} eligible full XNYS sessions; {verification['incomplete_rth_bars']} incomplete/invalid five-minute RTH bars reset pending patterns. All {verification['independently_checked_fills']} completed fills were independently checked against the native executor, including exits, fees, timing, conflicts and MFE/MAE.",
        "",
        "No future completeness or outcome label is used to select a signal. Any missing owned execution minute is reported as EXECUTION_DATA_UNAVAILABLE and locks that setup for the rest of the session; it is not silently dropped at signal detection. Entry at the session-closing instant is not permitted.",
        "",
        "## Limitations",
        "",
        "- These are new Development hypotheses, not validated strategies. The detector’s visual agreement with discretionary zones has not been established; the user explicitly waived that prerequisite.",
        "- Results cover the accepted historical subset, not every Development session. Zone availability also depends on causal ATR warmup and source completeness.",
        "- Contact episodes are measured within each RTH session and reset after data gaps; they are not the all-hours lifecycle touch counter.",
        "- Pending C confirmation may complete after invalidation caused by that same breakout. The saved lifecycle is not changed; unrelated later breaks cannot reuse invalidated zones.",
        "- The first pass does not optimize parameters or select a winning strategy. Monthly, direction, episode, equity, signal and trade tables accompany this report.",
        "- These runs use the trusted native execution engine through a reproducible research runner; they are not inserted into the application’s saved-run database.",
        "- Validation/OOS outcomes were not read. Existing market files and historical artifacts retain their hashes. No paid data was downloaded.",
        "",
        "## Reproduction",
        "",
        "Run `work/.venv/bin/python scripts/zone_reaction_backtest/verify.py` from the repository. The verification script runs the same experiment twice and requires byte-identical economic/configuration artifacts. Source identities and scoped test evidence are saved alongside results.",
        "",
    ]
    (P / "DEVELOPMENT_BACKTEST_REPORT.md").write_text("\n".join(lines))
    print(table(summary, cols))


if __name__ == "__main__":
    main()
