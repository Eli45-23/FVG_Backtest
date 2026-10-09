"""Complete diagnostic comparisons, with explicit overlap and execution denominators."""

import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from scripts.downward_break_feasibility.run import P, COUNTS, write
from scripts.pml_feasibility.report import describe, metrics
from scripts.zone_reaction_backtest.report import table


def main():
    paths = pd.read_csv(P / "all_event_paths.csv", low_memory=False)
    trades = pd.read_csv(P / "all_target_executions.csv", low_memory=False)
    assert len(paths) == 11364 * 6 and len(trades) == 11364 * 12
    group = ["level_type", "stop", "ticks", "target_r"]
    summaries = []
    for key, g in trades.groupby(group, sort=True):
        v = g[g.execution_status == "COMPLETED"]
        x = dict(zip(group, key), **metrics(g))
        for col in [
            "risk_points",
            "risk_usd",
            "risk_atr",
            "duration_minutes",
            "mfe_points",
            "mae_points",
            "mfe_r",
            "mae_r",
        ]:
            a = pd.to_numeric(v[col], errors="coerce")
            for name, value in [
                ("mean", a.mean()),
                ("median", a.median()),
                ("q25", a.quantile(0.25)),
                ("q75", a.quantile(0.75)),
                ("min", a.min()),
                ("max", a.max()),
            ]:
                x[f"{col}_{name}"] = value
        x["gross_avg_r"] = v.gross_result_r.mean()
        x["net_per_diagnostic"] = v.net_pnl_usd.mean()
        x["break_even_fee_per_side"] = (
            v.gross_pnl_usd.sum() / (2 * len(v)) if len(v) else None
        )
        years = v.groupby("year").net_pnl_usd.sum()
        x["positive_years"] = int((years > 0).sum())
        x["net_2022"] = years.get(2022, 0)
        x["share_2022_of_net_pct"] = (
            100 * years.get(2022, 0) / v.net_pnl_usd.sum()
            if v.net_pnl_usd.sum() > 0
            else None
        )
        summaries.append(x)
    allsummary = pd.DataFrame(summaries)
    write("fee_slippage_sensitivity.csv", allsummary)
    primary = allsummary[allsummary.ticks == 1]
    write("fixed_target_diagnostics.csv", primary)
    yearly = []
    for key, g in trades[trades.ticks == 1].groupby(
        ["level_type", "stop", "target_r", "year"]
    ):
        yearly.append(
            dict(zip(["level_type", "stop", "target_r", "year"], key), **metrics(g))
        )
    yearly = pd.DataFrame(yearly)
    write("yearly_stability.csv", yearly)
    matrix = []
    for key, g in paths[paths.ticks == 1].groupby(["level_type", "stop"]):
        matrix.append(dict(zip(["level_type", "stop"], key), **describe(g)))
    matrix = pd.DataFrame(matrix)
    write("stop_path_comparison.csv", matrix)
    breakdown = []
    for dimension in ["year", "touch_group", "time_bucket", "volatility_bucket"]:
        for key, g in paths[paths.ticks == 1].groupby(
            ["level_type", "stop", dimension], dropna=False
        ):
            breakdown.append(
                dict(
                    level_type=key[0],
                    stop=key[1],
                    dimension=dimension,
                    value=key[2],
                    **describe(g),
                )
            )
    write("descriptive_context.csv", breakdown)
    large = []
    for key, g in trades[
        (trades.ticks == 1) & (trades.execution_status == "COMPLETED")
    ].groupby(["level_type", "stop", "target_r"]):
        v = (
            g.sort_values(["risk_points", "event_id"], ascending=[False, True])
            .head(5)
            .copy()
        )
        v["group_net_usd"] = g.net_pnl_usd.sum()
        v["top_five_net_usd"] = v.net_pnl_usd.sum()
        v["group_total_positive_usd"] = g.loc[g.net_pnl_usd > 0, "net_pnl_usd"].sum()
        large.append(v)
    write("largest_risk_diagnostics.csv", pd.concat(large, ignore_index=True))
    conflict = [c for c in paths if c.endswith(("_conflict", "_mae_order_ambiguous"))]
    write(
        "ambiguity_audit.csv",
        paths[["event_id", "level_type", "ticks", "stop"] + conflict],
    )
    raw = pd.read_csv(P / "exact_raw_events.csv")
    quality = []
    for level, g in raw.groupby("level_type"):
        x = paths[
            (paths.level_type == level)
            & (paths.ticks == 1)
            & (paths.stop == "LEVEL_RECLAIM")
        ]
        quality.append(
            dict(
                level_type=level,
                raw_events=len(g),
                unique_dates=g.date.nunique(),
                atr_unavailable=int(g.atr14.isna().sum()),
                no_post_entry_minutes=int(
                    x.eligibility_status.eq("NO_POST_ENTRY_SESSION_MINUTES").sum()
                ),
                complete_15m=int(x.complete_15m.eq(True).sum()),
                complete_30m=int(x.complete_30m.eq(True).sum()),
                complete_60m=int(x.complete_60m.eq(True).sum()),
                future_gap_present=int(x.first_missing_minute.notna().sum()),
            )
        )
    write("population_and_quality.csv", quality)
    # No declaration of a winning stop/target from these in-sample diagnostic totals.
    conclusion = dict(
        status="DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY",
        selected_strategy=None,
        selected_target=None,
        selected_level=None,
        reason="Review path, costs and every year together. Overlapping diagnostics are not an investable portfolio. No Validation/OOS outcomes accessed.",
    )
    (P / "recommendation.json").write_text(
        json.dumps(conclusion, sort_keys=True, indent=2) + "\n"
    )
    verification = json.loads((P / "execution_verification.json").read_text())
    summary = dict(
        status="DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY",
        raw_events=len(raw),
        unique_dates=raw.date.nunique(),
        levels=8,
        stops=2,
        targets=[1, 2],
        slippage_ticks=[0, 1, 2],
        primary_ticks=1,
        fee_per_side=0.73,
        round_trip_fee=1.46,
        primary_positive_net_cases=int((primary.net_usd > 0).sum()),
        primary_positive_avg_r_cases=int((primary.avg_net_r > 0).sum()),
        primary_cases=len(primary),
        native_checks=verification["native_independent_checks"],
    )
    (P / "study_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    cols = [
        "level_type",
        "stop",
        "target_r",
        "events",
        "valid_trades",
        "wins",
        "losses",
        "win_pct",
        "gross_usd",
        "fees_usd",
        "net_usd",
        "pf",
        "avg_net_r",
        "positive_years",
        "max_closed_diagnostic_dd_usd",
    ]
    text = [
        "# Downward-break execution feasibility — Development v1",
        "",
        "**DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY.** Eight fixed daily levels, immediate confirmed downward-break SHORT entry, two frozen structural stops and fixed original 1R/2R targets. Actual Webull fees; no signal filters or management. All 2020–2023 signals are retained, including later failures and retests.",
        "",
        "## What was tested",
        "",
        "Stop A (LEVEL_RECLAIM) is one tick above the broken level. Stop B (BREAK_CANDLE_HIGH) is one tick above the break candle’s high. Neither uses future data. The level stop can be narrower than the signal candle; pre-entry movement through it does not count as a stop-out. One micro, $2/point, $0.73/side fees. Primary one adverse entry tick and one adverse exit tick; zero/two-tick sensitivity uses the same signals.",
        "",
        f"Exact reconciliation: **{len(raw):,} raw signals on {raw.date.nunique():,} dates**. {verification['native_independent_checks']:,} native fills/missing-data decisions were checked against an independent simulation. The production executor is unchanged.",
        "",
        "**These are independently evaluated, often overlapping event diagnostics.** There is no single-position/day policy or capital allocation. Dollar totals, trade counts and cumulative closed-result drawdowns must not be presented as a live portfolio backtest. No aggregate across all levels is used to choose a winner.",
        "",
        "## Population and future-data coverage",
        "",
        table(quality, list(quality[0])),
        "",
        "ATR missingness never excludes fixed-risk execution. Causal events at the close remain in raw counts but cannot own a post-close minute. A missing future minute affects only simulations still open at that minute. Fifteen/thirty/sixty-minute descriptive denominators require complete horizons independently of early trade exits.",
        "",
        "## Primary execution diagnostics: all levels and both stops/targets",
        "",
        table(primary.to_dict("records"), cols),
        "",
        f"Of the {len(primary)} predeclared primary level/stop/target cases, {int((primary.net_usd>0).sum())} have positive diagnostic net dollars and {int((primary.avg_net_r>0).sum())} have positive average net R. These counts are descriptive, not corrected statistical evidence or selection criteria.",
        "",
        "## Stop-bounded price paths",
        "",
        "Paths here end at original stop or actual session close, without taking either target. They answer whether the move gets to 1R/2R before stopping. Separate fixed-target simulations above can exit earlier. Inclusive exit-minute MFE/MAE are bounds because ordering inside that minute is unknown. Same-minute favorable/stop touches count stop first.",
        "",
        table(
            matrix.to_dict("records"),
            [
                "level_type",
                "stop",
                "execution_events",
                "valid_executable_events",
                "risk_points_median",
                "risk_points_q25",
                "risk_points_q75",
                "risk_points_max",
                "r1_before_stop_pct",
                "r2_before_stop_pct",
                "mfe_r_mean",
                "mae_r_mean",
                "stop_before_half_r_pct",
                "r1_conflict_count",
                "execution_data_unavailable",
            ],
        ),
        "",
        "## Every Development year",
        "",
        table(
            yearly.to_dict("records"),
            [
                "level_type",
                "stop",
                "target_r",
                "year",
                "events",
                "valid_trades",
                "win_pct",
                "net_usd",
                "pf",
                "avg_net_r",
                "max_closed_diagnostic_dd_usd",
                "average_risk",
            ],
        ),
        "",
        "## Actual costs and sensitivity",
        "",
        table(
            allsummary.to_dict("records"),
            [
                "level_type",
                "stop",
                "target_r",
                "ticks",
                "valid_trades",
                "gross_usd",
                "fees_usd",
                "net_usd",
                "pf",
                "avg_net_r",
                "break_even_fee_per_side",
            ],
        ),
        "",
        "Entry slippage changes executed entry, original risk and the target mechanically. Exit slippage is adverse even on targets, matching the existing executor. Costs therefore are not simply a constant subtraction between slippage scenarios. Break-even fee per side is gross diagnostic P&L divided by twice completed diagnostics, and may be negative.",
        "",
        "## Concentration and interpretation",
        "",
        table(
            primary.to_dict("records"),
            [
                "level_type",
                "stop",
                "target_r",
                "net_usd",
                "avg_net_r",
                "positive_years",
                "net_2022",
                "share_2022_of_net_pct",
                "risk_points_max",
                "risk_points_median",
            ],
        ),
        "",
        "A positive dollar result with negative average R may reflect large-risk observations rather than consistent opportunity. Shares above 100% mean other years offset the profitable year; a missing share means aggregate net was not positive. The top-five-risk observations and their signed contributions are retained in largest_risk_diagnostics.csv without exclusions.",
        "",
        "The previous favorable-50-point associations do not automatically imply a useful risk path. This audit does not select a best level, stop or target by in-sample profit. Review yearly consistency, stop logic, adverse paths and fee sensitivity before deciding whether to freeze one controlled strategy. Validation and OOS remain unqueried.",
        "",
        "## Reproducibility and complete exports",
        "",
        "frozen protocol.json; exact_raw_events.csv; source_reconciliation.csv; all_event_paths.csv; all_target_executions.csv; population_and_quality.csv; stop_path_comparison.csv; fixed_target_diagnostics.csv; yearly_stability.csv; fee_slippage_sensitivity.csv; descriptive_context.csv; largest_risk_diagnostics.csv; ambiguity_audit.csv; recommendation.json; execution_verification.json. All observations are retained locally. The bundle includes aggregate reports and an index linking full raw artifacts by hash; no sampling is used.",
        "",
        "The report’s standalone viewer is available from the Lab Research page. Production strategies, stored runs, source studies and market-data files are unchanged.",
        "",
    ]
    (P / "DOWNWARD_BREAK_EXECUTION_FEASIBILITY.md").write_text("\n".join(text))
    data = dict(
        summary=summary,
        primary=json.loads(primary.to_json(orient="records")),
        sensitivity=json.loads(allsummary.to_json(orient="records")),
        yearly=json.loads(yearly.to_json(orient="records")),
        paths=json.loads(matrix.to_json(orient="records")),
        quality=quality,
    )
    js = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    (P / "study.html").write_text(
        (ROOT / "scripts/downward_break_feasibility/viewer.html")
        .read_text()
        .replace("/*DATA*/", js)
    )
    print(summary, flush=True)


if __name__ == "__main__":
    main()
