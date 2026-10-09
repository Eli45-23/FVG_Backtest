"""Fixed-run results; no optimization."""

import json
import pandas as pd
from scripts.zone_rejection_v2.run import P
from scripts.zone_reaction_backtest.report import metrics, table


def measure(g):
    return {
        **metrics(g),
        **{f"reached_{r}r": int(g[f"reached_{r}r"].sum()) for r in (1, 2)},
        **{
            f"reached_{r}r_pct": (
                float(g[f"reached_{r}r"].mean() * 100) if len(g) else None
            )
            for r in (1, 2)
        },
        **{
            f"{r}r_ambiguity": int(g[f"{r}r_stop_same_minute_ambiguity"].sum())
            for r in (1, 2)
        },
    }


def main():
    t = pd.read_csv(P / "all_trades.csv")
    a = pd.read_csv(P / "signal_selection_audit.csv")
    life = pd.read_csv(P / "zone_selection_lifecycle.csv")
    v = json.loads((P / "execution_verification.json").read_text())
    assert (
        t.trade_id.is_unique and t.reached_2r.sum() == (t.exit_reason == "TARGET").sum()
    )
    total = measure(t)
    total["signals"] = len(a)
    total["selection_counts"] = {
        k: int(v) for k, v in a.selection_status.value_counts().items()
    }
    yearly = [dict(year=y, **measure(t[t.year == y])) for y in range(2020, 2024)]
    direction = [
        dict(direction=d, **measure(t[t.direction == d])) for d in ["LONG", "SHORT"]
    ]
    monthly = [
        dict(month=str(m), **measure(t[t.date.str.startswith(str(m))]))
        for m in pd.period_range("2020-01", "2023-12", freq="M")
    ]
    for name, rows in [
        ("yearly", yearly),
        ("direction", direction),
        ("monthly", monthly),
    ]:
        pd.DataFrame(rows).to_csv(P / f"{name}.csv", index=False, float_format="%.12g")
    (P / "summary.json").write_text(
        json.dumps(total, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    eq = (
        t[["trade_id", "exit_time_utc", "net_pnl_usd"]]
        .sort_values(["exit_time_utc", "trade_id"])
        .copy()
    )
    eq["equity"] = eq.net_pnl_usd.cumsum()
    eq["drawdown"] = eq.equity.cummax().clip(lower=0) - eq.equity
    eq.to_csv(P / "equity.csv", index=False, float_format="%.12g")
    cols = [
        "trades",
        "wins",
        "losses",
        "win_rate",
        "net_usd",
        "pf",
        "average_r",
        "max_drawdown_usd",
        "reached_1r",
        "reached_2r",
    ]
    text = [
        "# Newest-zone penetration/rejection — Development v2",
        "",
        "**DEVELOPMENT_ONLY_NOT_VALIDATED.** This tests only the user-confirmed penetration/rejection setup. No taps, breakout entries, additional filters or optimization.",
        "",
        "## Rules and scope",
        "",
        "Accepted Development 2020–2023 historical subset. One newest confirmed supply and one newest demand; permanent same-type replacement, no older-zone fallback. Entire confirmed five-minute candle beyond the distal edge invalidates a zone at any trading hour. Body-only or wick-only penetration does not invalidate. Zone state persists overnight, but pending entry episodes remain RTH-only and reset overnight, as in the frozen previous entry convention.",
        "",
        "Price must penetrate the near edge, then the first separate full five-minute candle including wicks back outside triggers: short below supply, long above demand. Entry at confirmation close; subsequent one-minute activity only. One open position overall; a fresh episode after exit is needed for reentry. No holidays/half-days, session-close exit.",
        "",
        "One MNQ micro; one-tick buffer beyond the opposite zone boundary; fixed original 2R; no management. One adverse tick each side and actual $0.73/side fees. Replacing or invalidating the source zone does not move an already-open trade’s stop or target.",
        "",
        "## Overall results",
        "",
        table([total], cols),
        "",
        table(
            [total],
            [
                "gross_usd",
                "fees_usd",
                "net_usd",
                "total_r",
                "median_r",
                "average_risk_points",
                "median_risk_points",
                "max_risk_points",
                "session_close_exits",
            ],
        ),
        "",
        "## Requested milestone counts",
        "",
        table(
            [total],
            [
                "trades",
                "reached_1r",
                "reached_1r_pct",
                "reached_2r",
                "reached_2r_pct",
                "1r_ambiguity",
                "2r_ambiguity",
            ],
        ),
        "",
        "Milestones are gross price movement from the executed entry divided by original structural risk. They are counted only before actual exit. Reaching 1R does not exit or move the stop. Same-minute stop/threshold contact counts stop-first, not success; ambiguity is reported separately. The two counts overlap: trades reaching 2R also reach 1R. Costs mean a target fill is slightly less than net 2R.",
        "",
        "## Yearly",
        "",
        table(yearly, ["year", *cols]),
        "",
        "## Direction",
        "",
        table(direction, ["direction", *cols]),
        "",
        "## Excursions",
        "",
        table(
            [total],
            [
                "average_mfe_points",
                "median_mfe_points",
                "average_mae_points",
                "median_mae_points",
                "average_mfe_r",
                "average_mae_r",
                "average_duration_minutes",
                "same_minute_conflicts",
            ],
        ),
        "",
        "MFE/MAE preserve the native full exit-minute range and can include movement after the actual fill; milestone counts instead use conservative ordering.",
        "",
        "## Accounting and preservation",
        "",
        f"Raw signals: {len(a)}. Selection outcomes: {json.dumps(total['selection_counts'],sort_keys=True)}.",
        f"Zone-state transitions: {json.dumps({k:int(v) for k,v in life.reason.value_counts().items()},sort_keys=True)}.",
        f"Reproduced all {v['zones']} accepted zone formations exactly. {v['eligible_full_sessions']} eligible full XNYS sessions; 104 unresolved historical dates excluded from entries; {v['incomplete_rth_bars']} incomplete RTH bars cleared pending patterns. All {v['independently_checked_fills']} completed fills independently reconciled, including fees, exit time, stop/target conflicts and excursions.",
        "",
        "Historical provider lifecycle and prior backtest files are unchanged. This strategy’s five-minute lifecycle is separate. Confirmed complete source bars are used for all-hours invalidation even when a date is excluded from entry eligibility. Absent/incomplete source bars cannot establish a break; no hidden break is guessed. Owned execution gaps are explicit failures, never fabricated fills.",
        "",
        "No Validation/OOS outcome rows read; both data files are predicate-scanned only within Development. Full-file hashes verify preservation. No paid downloads, database changes or parameter searches. Results are reproducible research artifacts, not saved-run database entries.",
        "",
        "## Reproduction and checks",
        "",
        "Run `work/.venv/bin/python scripts/zone_rejection_v2/verify.py`. It runs scoped synthetic/regression tests and two full backtests, requiring byte-identical result/configuration artifacts. See reproducibility_manifest.json and synthetic_test_results.txt. Detailed signals, zone transitions, per-trade milestones, monthly tables and equity remain local in the results directory.",
        "",
    ]
    (P / "DEVELOPMENT_BACKTEST_REPORT.md").write_text("\n".join(text))
    print(table([total], cols), flush=True)


if __name__ == "__main__":
    main()
