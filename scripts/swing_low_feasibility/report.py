"""Denominator-explicit summaries of frozen independent-event diagnostics."""

from pathlib import Path
import json, sys, hashlib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.canonical import dumps

P = ROOT / "work/5m-swing-low-execution-feasibility-v1"
M = ROOT / "work/mnq-individual-level-master-research"


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write(name, rows):
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).to_csv(
        P / name, index=False, float_format="%.12g", lineterminator="\n"
    )


def safe(value):
    return float(value) if pd.notna(value) else None


def means(out, g, col, label=None):
    v = pd.to_numeric(g[col], errors="coerce").dropna()
    label = label or col
    out[label + "_denominator"] = len(v)
    out["mean_" + label] = safe(v.mean())
    out["median_" + label] = safe(v.median())


def rate(out, g, col, label=None):
    v = g[col].dropna()
    label = label or col
    out[label + "_denominator"] = len(v)
    out[label + "_count"] = int(v.eq(True).sum())
    out[label + "_pct"] = 100 * v.eq(True).mean() if len(v) else None


def metrics(g):
    v = g[g.execution_status == "COMPLETED"]
    net = v.net_pnl_usd
    loss = -net[net < 0].sum()
    return {
        "signals": len(g),
        "completed_trades": len(v),
        "unique_dates_completed": v.date.nunique(),
        "nonpositive_risk": int(g.execution_status.eq("NON_POSITIVE_RISK").sum()),
        "no_post_entry_minutes": int(
            g.execution_status.eq("NO_POST_ENTRY_SESSION_MINUTES").sum()
        ),
        "execution_data_unavailable": int(
            g.execution_status.eq("EXECUTION_DATA_UNAVAILABLE").sum()
        ),
        "wins": int((net > 0).sum()),
        "losses": int((net < 0).sum()),
        "win_pct": 100 * (net > 0).mean() if len(v) else None,
        "gross_pnl_usd": float(v.gross_pnl_usd.sum()),
        "fees_usd": float(v.commission_usd.sum()),
        "net_pnl_usd": float(net.sum()),
        "net_pf": float(net[net > 0].sum() / loss) if loss else None,
        "net_avg_r": safe(v.result_r.mean()),
        "session_close_exits": int(v.exit_reason.eq("SESSION_CLOSE").sum()),
        "same_minute_conflicts": int(v.same_minute_stop_target_conflict.eq(True).sum()),
    }


def describe(g, t, raw):
    valid = g[g.eligibility_status == "VALID"]
    resolved = valid[valid.path_complete.eq(True)]
    out = {
        "execution_denominator": len(g),
        "execution_dates": g.date.nunique(),
        "valid_positive_risk_with_session_minutes": len(valid),
        "nonpositive_risk": int(g.eligibility_status.eq("NON_POSITIVE_RISK").sum()),
        "no_post_entry_minutes": int(
            g.eligibility_status.eq("NO_POST_ENTRY_SESSION_MINUTES").sum()
        ),
        "stop_or_session_paths_resolved": len(resolved),
        "stop_or_session_paths_data_unavailable": int(
            valid.path_status.eq("EXECUTION_DATA_UNAVAILABLE").sum()
        ),
        "raw_atr_unavailable": int(raw.atr14.isna().sum()),
        "raw_at_session_close": int(raw.entry_at_session_close.sum()),
    }
    for col in ["risk_points", "risk_usd", "risk_atr"]:
        means(out, valid, col)
        out[col + "_q25"] = safe(valid[col].quantile(0.25))
        out[col + "_q75"] = safe(valid[col].quantile(0.75))
        out[col + "_max"] = safe(valid[col].max())
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
        means(out, resolved, col)
    for horizon in [15, 30, 60]:
        out[f"raw_{horizon}m_complete"] = int(
            raw[f"complete_{horizon}m"].eq(True).sum()
        )
        out[f"raw_{horizon}m_censored"] = len(raw) - out[f"raw_{horizon}m_complete"]
        complete = valid[f"complete_{horizon}m"].eq(True)
        out[f"valid_{horizon}m_complete"] = int(complete.sum())
        out[f"valid_{horizon}m_censored"] = len(valid) - int(complete.sum())
        rate(out, valid.loc[complete], f"stop_hit_{horizon}m")
    for unit, thresholds in [
        ("r", ["0p5", "1", "1p25", "1p5", "2"]),
        ("atr", ["0p5", "1", "1p5"]),
    ]:
        for threshold in thresholds:
            key = unit + threshold
            rate(out, valid, key + "_before_stop")
            means(out, valid, key + "_minutes")
            out[key + "_conflicts"] = int(valid[key + "_conflict"].eq(True).sum())
    for key in ["r0p5", "r1"]:
        means(out, valid, key + "_mae_before_hit_lower")
        means(out, valid, key + "_mae_before_hit_upper")
        out[key + "_mae_order_ambiguous"] = int(
            valid[key + "_mae_order_ambiguous"].eq(True).sum()
        )
    rate(out, valid, "half_r_before_minus_half_r")
    rate(out, valid, "stop_before_half_r")
    means(out, valid, "minutes_to_stop")
    out.update(
        {"diagnostic_1r_" + k: v for k, v in metrics(t[t.target_r == 1]).items()}
    )
    assert (
        out["execution_denominator"]
        == out["nonpositive_risk"]
        + out["no_post_entry_minutes"]
        + out["valid_positive_risk_with_session_minutes"]
    )
    return out


def table(f, cols=None):
    if cols:
        f = f[cols]

    def format(x):
        if pd.isna(x):
            return "—"
        if isinstance(x, (float, np.floating)):
            return f"{x:,.4f}".rstrip("0").rstrip(".")
        return str(x)

    return (
        "| "
        + " | ".join(f.columns)
        + " |\n| "
        + " | ".join(["---"] * len(f.columns))
        + " |\n"
        + "\n".join(
            "| " + " | ".join(format(x) for x in row) + " |"
            for row in f.itertuples(index=False, name=None)
        )
    )


def report():
    raw = pd.read_csv(P / "exact_touch_events.csv")
    paths = pd.read_csv(P / "all_event_paths.csv", low_memory=False)
    trades = pd.read_csv(P / "all_target_executions.csv", low_memory=False)
    assert (
        len(raw) == 5319
        and raw.date.nunique() == 1006
        and len(paths) == 5319 * 6
        and len(trades) == 5319 * 18
    )
    for h in [15, 30, 60]:
        e = pd.read_parquet(M / f"08_5M_SWING_LOW/outcomes_{h}.parquet").set_index(
            "event_id"
        )
        raw[f"complete_{h}m"] = raw.event_id.map(e.complete)
    assert raw.complete_30m.sum() == 4821 and raw.atr14.isna().sum() == 5
    for h in [15, 30, 60]:
        v = paths[paths.eligibility_status == "VALID"]
        expected = v.event_id.map(raw.set_index("event_id")[f"complete_{h}m"])
        assert (v[f"complete_{h}m"].to_numpy() == expected.to_numpy()).all(), h

    subsets = {
        "A": set(raw.event_id),
        "B": set(raw.loc[raw.is_rejection, "event_id"]),
        "C": set(raw.loc[raw.is_sweep, "event_id"]),
    }
    assert subsets["C"] <= subsets["B"] <= subsets["A"]
    matrix = []
    yearly = []
    touches = []
    contexts = []
    targetrows = []
    riskbins = []
    for name, ids in subsets.items():
        r = raw[raw.event_id.isin(ids)]
        for stop in ["A", "B"]:
            for ticks in [0, 1, 2]:
                g = paths[
                    (paths.event_id.isin(ids))
                    & (paths.stop == stop)
                    & (paths.ticks == ticks)
                ]
                t = trades[
                    (trades.event_id.isin(ids))
                    & (trades.stop == stop)
                    & (trades.ticks == ticks)
                ]
                base = {"entry": name, "stop": stop, "ticks": ticks}
                matrix.append({**base, **describe(g, t, r)})
                for target in [0.5, 1, 1.5]:
                    targetrows.append(
                        {**base, "target_r": target, **metrics(t[t.target_r == target])}
                    )
                for year in range(2020, 2024):
                    yearly.append(
                        {
                            **base,
                            "year": year,
                            **describe(
                                g[g.year == year], t[t.year == year], r[r.year == year]
                            ),
                        }
                    )
                for dim, values in [
                    ("touch_group", ["1", "2", "3+"]),
                    ("swing_progression", ["HL", "LL", "EL", "UNCLASSIFIED"]),
                    ("structure_state", ["BULLISH", "BEARISH", "NEUTRAL"]),
                    ("already_broken_before_touch", [True, False]),
                ]:
                    for value in values:
                        gg = g[g[dim].astype(str) == str(value)]
                        tt = t[t[dim].astype(str) == str(value)]
                        rr = r[r[dim].astype(str) == str(value)]
                        row = {
                            **base,
                            "dimension": dim,
                            "value": value,
                            **describe(gg, tt, rr),
                        }
                        (touches if dim == "touch_group" else contexts).append(row)
                valid = g[g.eligibility_status == "VALID"]
                bins = pd.cut(
                    valid.risk_atr,
                    [0, 0.5, 1, 2, 4, np.inf],
                    right=False,
                    labels=["0–<0.5", "0.5–<1", "1–<2", "2–<4", "4+"],
                )
                for bucket in ["0–<0.5", "0.5–<1", "1–<2", "2–<4", "4+"]:
                    riskbins.append(
                        {
                            **base,
                            "risk_atr_bucket": bucket,
                            "count": int((bins == bucket).sum()),
                            "valid_risk_count": len(valid),
                            "atr_available_count": int(valid.risk_atr.notna().sum()),
                        }
                    )
    mf = pd.DataFrame(matrix)
    yf = pd.DataFrame(yearly)
    tf = pd.DataFrame(targetrows)
    for name, rows in [
        ("entry_stop_matrix.csv", mf),
        ("excursion_sequence_analysis.csv", mf),
        ("target_diagnostics.csv", tf),
        ("yearly_stability.csv", yf),
        ("touch_number_analysis.csv", touches),
        ("structure_context.csv", contexts),
        ("fee_slippage_sensitivity.csv", tf),
        ("risk_atr_distribution.csv", riskbins),
    ]:
        write(name, rows)
    ambiguity = []
    for r in paths.itertuples():
        for field in [
            "r0p5_conflict",
            "r1_conflict",
            "r1p25_conflict",
            "r1p5_conflict",
            "r2_conflict",
            "atr0p5_conflict",
            "atr1_conflict",
            "atr1p5_conflict",
            "half_r_race_conflict",
            "r0p5_mae_order_ambiguous",
            "r1_mae_order_ambiguous",
        ]:
            value = getattr(r, field)
            if pd.notna(value) and value:
                ambiguity.append(
                    {
                        "event_id": r.event_id,
                        "stop": r.stop,
                        "ticks": r.ticks,
                        "kind": field,
                        "target_r": None,
                    }
                )
    for r in trades[trades.same_minute_stop_target_conflict.eq(True)].itertuples():
        ambiguity.append(
            {
                "event_id": r.event_id,
                "stop": r.stop,
                "ticks": r.ticks,
                "kind": "FIXED_TARGET_STOP_FIRST",
                "target_r": r.target_r,
            }
        )
    write("ambiguity_audit.csv", ambiguity)
    write(
        "execution_unavailable.csv",
        trades[trades.execution_status == "EXECUTION_DATA_UNAVAILABLE"],
    )
    write("session_close_signals.csv", raw[raw.entry_at_session_close])
    primary = mf[mf.ticks == 1]
    print(
        primary[
            [
                "entry",
                "stop",
                "execution_denominator",
                "valid_positive_risk_with_session_minutes",
                "r1_before_stop_pct",
                "mean_mfe_r",
                "mean_mae_r",
                "diagnostic_1r_net_pnl_usd",
                "diagnostic_1r_net_pf",
                "diagnostic_1r_net_avg_r",
            ]
        ].to_string(index=False)
    )
    # Preserve all comparisons. Final reasoned classification is supplied after table review.
    (P / "aggregate_verification.json").write_text(
        dumps(
            {
                "raw_events": 5319,
                "raw_dates": 1006,
                "entry_counts": {k: len(v) for k, v in subsets.items()},
                "matrix_rows": len(mf),
                "target_rows": len(tf),
                "yearly_rows": len(yf),
                "all_denominator_partitions_pass": True,
            }
        )
    )


if __name__ == "__main__":
    report()
