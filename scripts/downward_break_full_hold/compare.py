"""Selection-conditioned comparisons; never a causal estimate of waiting."""

import json
import pandas as pd
from scripts.downward_break_full_hold.run import P, ROOT, write
from scripts.pml_feasibility.report import metrics


def main():
    old = ROOT / "work/downward-break-execution-feasibility-v1"
    a = pd.read_csv(old / "all_target_executions.csv", low_memory=False)
    b = pd.read_csv(P / "all_target_executions.csv", low_memory=False)
    ids = set(b.root_id)
    assert len(ids) == 4784
    keys = ["root_id", "level_type", "stop", "ticks", "target_r"]
    matched = a.merge(
        b, on=keys, suffixes=("_immediate", "_confirmed"), validate="one_to_one"
    )
    assert len(matched) == len(b)
    assert (matched.stop_price_immediate == matched.stop_price_confirmed).all()
    assert (
        (
            pd.to_datetime(matched.entry_time_utc_confirmed, utc=True)
            - pd.to_datetime(matched.entry_time_utc_immediate, utc=True)
        ).dt.total_seconds()
        == 300
    ).all()
    matched["original_closed_by_delayed_entry"] = pd.to_datetime(
        matched.exit_time_utc_immediate, utc=True
    ) <= pd.to_datetime(matched.entry_time_utc_confirmed, utc=True)
    matched["net_change"] = (
        matched.net_pnl_usd_confirmed - matched.net_pnl_usd_immediate
    )
    matched["risk_change"] = (
        matched.risk_points_confirmed - matched.risk_points_immediate
    )
    write("matched_root_details.csv", matched)
    rows = []
    datasets = {
        "ALL_IMMEDIATE": a,
        "MATCHED_IMMEDIATE": a[a.root_id.isin(ids)],
        "OMITTED_IMMEDIATE": a[~a.root_id.isin(ids)],
        "CONFIRMED": b,
    }
    group = ["level_type", "stop", "ticks", "target_r"]
    for cohort, frame in datasets.items():
        for key, g in frame.groupby(group, sort=True):
            rows.append(dict(cohort=cohort, **dict(zip(group, key)), **metrics(g)))
    write("entry_timing_comparison.csv", rows)
    paired = []
    for key, g in matched.groupby(group, sort=True):
        complete = g[
            g.execution_status_immediate.eq("COMPLETED")
            & g.execution_status_confirmed.eq("COMPLETED")
        ]
        paired.append(
            dict(
                **dict(zip(group, key)),
                roots=len(g),
                complete_pairs=len(complete),
                original_closed_by_delayed_entry=int(
                    g.original_closed_by_delayed_entry.sum()
                ),
                mean_risk_change=complete.risk_change.mean(),
                mean_entry_change=(
                    complete.entry_price_confirmed - complete.entry_price_immediate
                ).mean(),
                net_change_on_complete_pairs=complete.net_change.sum(),
                average_r_change_on_complete_pairs=(
                    complete.result_r_confirmed - complete.result_r_immediate
                ).mean()
            )
        )
    write("paired_entry_changes.csv", paired)
    audit = pd.read_csv(P / "opportunity_reconciliation.csv")
    write(
        "opportunity_counts.csv",
        audit.groupby(["level_type", "status"], sort=True)
        .size()
        .rename("events")
        .reset_index(),
    )


if __name__ == "__main__":
    main()
