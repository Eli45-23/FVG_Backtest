"""Denominator-explicit PML research summaries, not strategy selection."""

from pathlib import Path
import sys, json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pml_feasibility.run import P, M, write, sha
from engine.canonical import dumps


def numeric(v):
    return float(v) if pd.notna(v) else None


def rate(out, g, col):
    v = g[col].dropna()
    out[col + "_denominator"] = len(v)
    out[col + "_count"] = int(v.eq(True).sum())
    out[col + "_pct"] = float(v.eq(True).mean() * 100) if len(v) else None


def describe(g):
    valid = g[g.eligibility_status == "VALID"]
    resolved = valid[valid.path_complete.eq(True)]
    out = dict(
        execution_events=len(g),
        execution_dates=g.date.nunique(),
        valid_executable_events=len(valid),
        nonpositive_risk=int(g.eligibility_status.eq("NON_POSITIVE_RISK").sum()),
        no_post_entry_minutes=int(
            g.eligibility_status.eq("NO_POST_ENTRY_SESSION_MINUTES").sum()
        ),
        resolved_paths=len(resolved),
        execution_data_unavailable=int(
            valid.path_status.eq("EXECUTION_DATA_UNAVAILABLE").sum()
        ),
    )
    for col in ["risk_points", "risk_usd", "risk_atr"]:
        v = valid[col]
        out.update(
            {
                col + "_mean": numeric(v.mean()),
                col + "_median": numeric(v.median()),
                col + "_q25": numeric(v.quantile(0.25)),
                col + "_q75": numeric(v.quantile(0.75)),
                col + "_min": numeric(v.min()),
                col + "_max": numeric(v.max()),
            }
        )
    for col in [
        "mfe_points",
        "mae_points",
        "mfe_r",
        "mae_r",
        "mfe_atr",
        "mae_atr",
        "mfe_points_lower_bound",
        "mae_points_lower_bound",
    ]:
        out[col + "_denominator"] = int(resolved[col].notna().sum())
        out[col + "_mean"] = numeric(resolved[col].mean())
        out[col + "_median"] = numeric(resolved[col].median())
    for col in [
        c
        for c in valid
        if c.endswith("_before_stop")
        or c in ["half_r_before_minus_half_r", "stop_before_half_r"]
        or c.startswith("stop_hit_")
    ]:
        rate(out, valid, col)
    for h in [15, 30, 60]:
        out[f"{h}m_complete"] = int(valid[f"complete_{h}m"].eq(True).sum())
        out[f"{h}m_censored"] = len(valid) - out[f"{h}m_complete"]
    for col in [
        c
        for c in valid
        if c.endswith(("_minutes", "_mae_before_hit_lower", "_mae_before_hit_upper"))
        or c == "minutes_to_stop"
    ]:
        if col in ["expected_session_minutes", "owned_prefix_minutes"]:
            continue
        v = pd.to_numeric(valid[col], errors="coerce")
        out[col + "_denominator"] = int(v.notna().sum())
        out[col + "_mean"] = numeric(v.mean())
        out[col + "_median"] = numeric(v.median())
    for col in [c for c in valid if c.endswith(("_conflict", "_mae_order_ambiguous"))]:
        out[col + "_count"] = int(valid[col].eq(True).sum())
    return out


def metrics(g):
    v = g[g.execution_status == "COMPLETED"].sort_values(["exit_time_utc", "event_id"])
    net = v.net_pnl_usd
    loss = -net[net < 0].sum()
    eq = np.r_[0, net.cumsum().to_numpy()]
    rr = np.r_[0, v.result_r.cumsum().to_numpy()]
    return dict(
        events=len(g),
        valid_trades=len(v),
        unique_dates=v.date.nunique(),
        nonpositive_risk=int(g.execution_status.eq("NON_POSITIVE_RISK").sum()),
        no_post_entry_minutes=int(
            g.execution_status.eq("NO_POST_ENTRY_SESSION_MINUTES").sum()
        ),
        execution_data_unavailable=int(
            g.execution_status.eq("EXECUTION_DATA_UNAVAILABLE").sum()
        ),
        wins=int((net > 0).sum()),
        losses=int((net < 0).sum()),
        win_pct=numeric(100 * (net > 0).mean()),
        gross_usd=float(v.gross_pnl_usd.sum()),
        fees_usd=float(v.commission_usd.sum()),
        net_usd=float(net.sum()),
        pf=float(net[net > 0].sum() / loss) if loss else None,
        avg_net_r=numeric(v.result_r.mean()),
        median_net_r=numeric(v.result_r.median()),
        total_net_r=float(v.result_r.sum()),
        max_closed_diagnostic_dd_usd=float((np.maximum.accumulate(eq) - eq).max()),
        max_closed_diagnostic_dd_r=float((np.maximum.accumulate(rr) - rr).max()),
        session_exits=int(v.exit_reason.eq("SESSION_CLOSE").sum()),
        same_minute_conflicts=int(v.same_minute_stop_target_conflict.eq(True).sum()),
        adverse_stop_gaps=int(v.adverse_stop_gap.eq(True).sum()),
        average_risk=numeric(v.risk_points.mean()),
    )


def run():
    paths = pd.read_csv(P / "all_event_paths.csv")
    targets = pd.read_csv(P / "all_target_executions.csv")
    raw = pd.read_csv(P / "exact_raw_events.csv")
    primary = paths[paths.ticks == 1]
    t = targets[targets.ticks == 1]
    stops = [dict(stop=k, **describe(g)) for k, g in primary.groupby("stop")]
    write("stop_comparison.csv", stops)
    write("excursion_sequence_analysis.csv", stops)
    fixed = [
        dict(stop=k[0], target_r=k[1], **metrics(g))
        for k, g in t.groupby(["stop", "target_r"])
    ]
    write("fixed_target_diagnostics.csv", fixed)
    cost = [
        dict(ticks=k[0], stop=k[1], target_r=k[2], **metrics(g))
        for k, g in targets.groupby(["ticks", "stop", "target_r"])
    ]
    write("fee_slippage_sensitivity.csv", cost)
    years = []
    for (stop, target, year), g in t.groupby(["stop", "target_r", "year"]):
        desc = describe(primary[(primary.stop == stop) & (primary.year == year)])
        years.append(
            dict(
                stop=stop,
                target_r=target,
                year=year,
                **metrics(g),
                **{
                    k: v
                    for k, v in desc.items()
                    if k.startswith(
                        ("r1_before_stop", "atr1_before_stop", "mfe_r", "mae_r")
                    )
                },
            )
        )
    write("yearly_stability.csv", years)
    episodes = []
    contexts = []
    for (stop, group), g in primary.groupby(["stop", "touch_group"]):
        episodes.append(dict(stop=stop, touch_group=group, **describe(g)))
    write("episode_analysis.csv", episodes)
    for dimension in [
        "structure_state",
        "atr_regime",
        "latest_structure_break",
        "confirmation_structure_break",
    ]:
        for (stop, value), g in primary.groupby(["stop", dimension], dropna=False):
            contexts.append(
                dict(stop=stop, dimension=dimension, value=value, **describe(g))
            )
    write("structure_context.csv", contexts)
    write(
        "event_context_values.csv",
        raw[
            [
                "event_id",
                "date",
                "structure_state",
                "atr_regime",
                "latest_structure_break",
                "confirmation_structure_break",
                "open_minus_pml_atr",
                "room_below_confirmation_atr",
                "touch_number",
            ]
        ],
    )
    contextstats = []
    for col in ["open_minus_pml_atr", "room_below_confirmation_atr"]:
        v = raw[col].dropna()
        contextstats.append(
            dict(
                context=col,
                events=len(raw),
                available=len(v),
                mean=v.mean(),
                median=v.median(),
                q25=v.quantile(0.25),
                q75=v.quantile(0.75),
                minimum=v.min(),
                maximum=v.max(),
            )
        )
    write("context_distance_summary.csv", contextstats)
    conflictcols = [
        c for c in primary if c.endswith(("_conflict", "_mae_order_ambiguous"))
    ]
    write(
        "ambiguity_audit.csv",
        primary[
            [
                "event_id",
                "date",
                "stop",
                "eligibility_status",
                "exit_minute_extrema_order_unknown",
            ]
            + conflictcols
        ],
    )
    concentration = []
    yf = pd.DataFrame(years)
    for (stop, target), g in yf.groupby(["stop", "target_r"]):
        yr = g.set_index("year").net_usd
        net = yr.sum()
        positive = yr[yr > 0].sum()
        concentration.append(
            dict(
                stop=stop,
                target_r=target,
                combined_net=net,
                net_2022=yr.loc[2022],
                other_years_net=net - yr.loc[2022],
                share_net_2022_pct=100 * yr.loc[2022] / net if net else None,
                share_positive_year_profit_2022_pct=(
                    100 * max(0, yr.loc[2022]) / positive if positive else None
                ),
                positive_years=int((yr > 0).sum()),
            )
        )
    write("year_2022_concentration.csv", concentration)
    ref = pd.read_csv(M / "same_date_baseline_sensitivity.csv")
    ref = ref[
        (ref.level == "PML")
        & (ref.interaction == "BREAK_FAILED_NEXT_CANDLE_HOLD")
        & (ref.stored_direction == "DOWN")
        & (ref.measured_direction == "DOWN")
    ]
    write("historical_same_date_reference.csv", ref)
    recommendation = dict(
        status="DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY",
        classification="DIRECTIONAL_BUT_POOR_RISK_PATH",
        controlled_development_backtest_warranted=False,
        reason="Published downward tendency reproduces, but every primary structural-stop/fixed-target diagnostic loses after actual costs; no stop/target is promoted. Low 1R-before-stop rates and adverse stop-bounded paths prevent actionable translation.",
        provider_or_production_changes=False,
        validation_queried=False,
        oos_revealed=False,
    )
    assert all(r["net_usd"] < 0 and r["avg_net_r"] < 0 for r in fixed)
    (P / "recommendation.json").write_text(dumps(recommendation))
    print(
        pd.DataFrame(stops)[
            [
                "stop",
                "execution_events",
                "valid_executable_events",
                "nonpositive_risk",
                "risk_points_median",
                "r1_before_stop_pct",
                "atr1_before_stop_pct",
                "mfe_points_mean",
                "mae_points_mean",
            ]
        ].to_string(index=False)
    )
    print(
        pd.DataFrame(fixed)[
            ["stop", "target_r", "net_usd", "pf", "avg_net_r"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    run()
