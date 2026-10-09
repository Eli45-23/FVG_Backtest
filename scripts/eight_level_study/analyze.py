"""Full-population summaries, one registered global family, exploratory timing pairs."""

import sys, json, itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from engine.research.statistics import clustered, benjamini_hochberg
from scripts.eight_level_study.detect import P, LEVELS, write
from scripts.eight_level_study.core import ENTRIES, FAMILY
from scripts.eight_level_study.label import POINTS, ATR, HORIZONS

KEY = ["year", "time_bucket", "volatility_bucket"]
GROUP = ["level_type", "entry_kind", "direction"]


def describe(g):
    c = g[g.complete]
    side = "up" if g.direction.iloc[0] == "UP" else "down"
    other = "down" if side == "up" else "up"
    return dict(
        events=len(g),
        roots=g.root_id.nunique(),
        dates=g.date.nunique(),
        complete=len(c),
        censored=len(g) - len(c),
        complete_dates=c.date.nunique(),
        atr_available=int((c.atr14 > 0).sum()),
        mean_mfe=c[f"{side}_excursion"].mean(),
        median_mfe=c[f"{side}_excursion"].median(),
        mean_mae=c[f"{other}_excursion"].mean(),
        median_mae=c[f"{other}_excursion"].median(),
        mean_forward=(c.forward_change * (1 if side == "up" else -1)).mean(),
        median_forward=(c.forward_change * (1 if side == "up" else -1)).median(),
        mean_mfe_atr=(c[f"{side}_excursion"] / c.atr14.where(c.atr14 > 0)).mean(),
        mean_mae_atr=(c[f"{other}_excursion"] / c.atr14.where(c.atr14 > 0)).mean(),
    )


def daily_stats(g, y, b):
    x = g[g.complete].dropna(subset=[y, b])
    if x.empty:
        return dict(
            event_probability=np.nan,
            baseline_probability=np.nan,
            effect=np.nan,
            matched_events=0,
            matched_dates=0,
        )
    d = x.groupby("date")[[y, b]].mean()
    return dict(
        event_probability=d[y].mean(),
        baseline_probability=d[b].mean(),
        effect=(d[y] - d[b]).mean(),
        matched_events=len(x),
        matched_dates=len(d),
    )


def main():
    ev = pd.read_parquet(P / "entry_events.parquet")
    base = pd.read_parquet(P / "baseline_observations.parquet")
    src = pd.read_parquet(P / "source_events.parquet")
    coverage = pd.read_csv(P / "level_coverage.csv")
    for f in [ev, base]:
        f["timestamp_utc"] = pd.to_datetime(f.timestamp_utc, utc=True)
        f["year"] = pd.to_numeric(f.year).astype(int)
    assert ev.event_id.is_unique and base.timestamp_utc.is_unique
    joined = ev.merge(
        base[["timestamp_utc", "price_at_event"]],
        on="timestamp_utc",
        suffixes=("", "_baseline"),
        validate="many_to_one",
    )
    assert len(joined) == len(ev) and np.array_equal(
        joined.price_at_event, joined.price_at_event_baseline
    )
    counts = []
    for keys, g in ev.groupby(GROUP, sort=True):
        kind, entry, direction = keys
        family = FAMILY[entry]
        if family == "REJECTION":
            root_kind = "TOUCH"
            stored = "DOWN" if direction == "UP" else "UP"
        else:
            root_kind = "BREAK_ACCEPTANCE"
            stored = (
                ("DOWN" if direction == "UP" else "UP")
                if family == "FAILED_BREAK_REVERSAL"
                else direction
            )
        denom = src[
            (src.level_type == kind)
            & (src.interaction_type == root_kind)
            & (src.direction == stored)
        ]
        available = int(
            coverage[(coverage.level == kind) & coverage.available].date.nunique()
        )
        counts.append(
            dict(
                zip(GROUP, keys),
                family=family,
                events=len(g),
                unique_roots=g.root_id.nunique(),
                unique_dates=g.date.nunique(),
                available_level_dates=available,
                events_per_available_date=len(g) / available if available else None,
                dates_with_event_pct=(
                    g.date.nunique() / available * 100 if available else None
                ),
                root_opportunities=len(denom),
                opportunity_type=root_kind,
                root_coverage_pct=(
                    100 * g.root_id.nunique() / len(denom) if len(denom) else None
                ),
            )
        )
    write("entry_frequency.csv", pd.DataFrame(counts))
    points = []
    atrs = []
    contexts = []
    primary = {}
    quality = []
    primary_frame = None
    for horizon in HORIZONS:
        o = pd.read_parquet(
            P / "baseline_outcomes.parquet", filters=[("horizon", "=", horizon)]
        )
        b = base.merge(o, on="event_id", validate="one_to_one")
        bcols = [c for c in o if "_hit_" in c or "_atr_" in c]
        pool = (
            b[b.complete]
            .groupby(KEY, dropna=False)[bcols]
            .mean()
            .add_prefix("baseline_")
            .reset_index()
        )
        e = ev.merge(
            b[["timestamp_utc"] + [c for c in o if c not in ["event_id", "horizon"]]],
            on="timestamp_utc",
            validate="many_to_one",
        ).merge(pool, on=KEY, how="left", validate="many_to_one")
        assert len(e) == len(ev)
        quality.append(
            dict(
                horizon=horizon,
                raw_events=len(e),
                complete=int(e.complete.sum()),
                censored=int((~e.complete).sum()),
                atr_unavailable_complete=int((e.complete & e.atr14.isna()).sum()),
                censor_reasons=json.dumps(
                    e.censor_reason.value_counts().to_dict(), sort_keys=True
                ),
            )
        )
        for keys, g in e.groupby(GROUP, sort=True):
            common = dict(zip(GROUP, keys), horizon=horizon, **describe(g))
            side = "up" if keys[2] == "UP" else "down"
            other = "down" if side == "up" else "up"
            c = g[g.complete]
            for t in POINTS:
                col = f"{side}_hit_{t}"
                bk = f"baseline_{col}"
                points.append(
                    dict(
                        **common,
                        points=t,
                        **daily_stats(g, col, bk),
                        raw_hit_count=int(c[col].sum()),
                        raw_event_hit_rate=c[col].mean(),
                        adverse_hit_rate=c[f"{other}_hit_{t}"].mean(),
                        median_minutes_to_hit=c[f"{side}_time_{t}"].median(),
                        mean_mae_through_hit=c[f"{side}_mae_before_{t}"].mean(),
                        median_mae_through_hit=c[f"{side}_mae_before_{t}"].median(),
                    )
                )
            for t in ATR:
                col = f"{side}_atr_{t:g}"
                bk = f"baseline_{col}"
                atrs.append(
                    dict(
                        **common,
                        atr_threshold=t,
                        **daily_stats(g, col, bk),
                        adverse_hit_rate=c[f"{other}_atr_{t:g}"].mean(),
                    )
                )
            if horizon == "30":
                col = f"{side}_hit_50"
                bk = f"baseline_{col}"
                good = c.dropna(subset=[col, bk])
                stats = clustered(good.date, good[col], good[bk])
                primary[keys] = dict(
                    **common,
                    **{
                        k: v
                        for k, v in stats.items()
                        if k not in ["events", "unique_dates", "ci95"]
                    },
                    matched_events=stats["events"],
                    matched_dates=stats["unique_dates"],
                    ci_low=stats["ci95"][0] if stats["ci95"] else None,
                    ci_high=stats["ci95"][1] if stats["ci95"] else None,
                )
                for dim in ["year", "time_bucket", "volatility_bucket", "touch_number"]:
                    for value, x in g.groupby(dim, dropna=False):
                        contexts.append(
                            dict(
                                zip(GROUP, keys),
                                dimension=dim,
                                value=value,
                                **describe(x),
                                **daily_stats(x, col, bk),
                            )
                        )
        if horizon == "30":
            primary_frame = e
        print("Aggregated horizon", horizon, flush=True)
    evidence = []
    for keys in itertools.product(LEVELS, ENTRIES, ["UP", "DOWN"]):
        row = primary.get(
            keys,
            dict(
                zip(GROUP, keys),
                events=0,
                matched_events=0,
                matched_dates=0,
                effect=None,
                p_value=None,
            ),
        )
        row["family_p_value"] = (
            row.get("p_value") if row.get("p_value") is not None else 1.0
        )
        evidence.append(row)
    q = benjamini_hochberg([r["family_p_value"] for r in evidence])
    for r, qv in zip(evidence, q):
        r["bh_q"] = qv
        r["small_sample"] = r["matched_dates"] < 30
        years = [
            x
            for x in contexts
            if (x["level_type"], x["entry_kind"], x["direction"])
            == (r["level_type"], r["entry_kind"], r["direction"])
            and x["dimension"] == "year"
        ]
        r["positive_years"] = sum(x["effect"] > 0 for x in years)
        r["years_with_10_dates"] = sum(x["matched_dates"] >= 10 for x in years)
        r["classification"] = (
            "INSUFFICIENT_DATA"
            if r["small_sample"]
            else (
                "CORRECTED_DEVELOPMENT_ASSOCIATION"
                if qv <= 0.05 and (r.get("effect") or 0) > 0
                else (
                    "NEGATIVE_ASSOCIATION"
                    if qv <= 0.05 and (r.get("effect") or 0) < 0
                    else "NO_CORRECTED_EVIDENCE"
                )
            )
        )
    write("primary_evidence.csv", pd.DataFrame(evidence))
    write("fixed_point_outcomes.csv", pd.DataFrame(points))
    write("atr_outcomes.csv", pd.DataFrame(atrs))
    write("context_comparisons.csv", pd.DataFrame(contexts))
    write("data_quality.csv", pd.DataFrame(quality))
    # Earliest candidate per root/direction. Common-root selection is diagnostic, not causal superiority.
    pairs = []
    comparisons = [
        ("BREAK_CLOSE", k)
        for k in [
            "BREAK_FIRST_FULL",
            "BREAK_NEXT_CLOSE_HOLD",
            "BREAK_NEXT_FULL_HOLD",
            "RETEST_CLOSE_HOLD",
            "RETEST_RANGE_ESCAPE",
        ]
    ] + [
        ("REJECTION_CLOSE", "REJECTION_CONFIRMATION"),
        ("FAILED_BREAK_CLOSE", "FAILED_BREAK_CONFIRMATION"),
    ]
    f = primary_frame.sort_values(["timestamp_utc", "event_id"]).drop_duplicates(
        ["level_type", "entry_kind", "root_id", "direction"]
    )
    for kind in LEVELS:
        for early, late in comparisons:
            for direction in ["UP", "DOWN"]:
                s = "up" if direction == "UP" else "down"
                side = f[(f.level_type == kind) & (f.direction == direction)]
                a = side[side.entry_kind == early]
                b = side[side.entry_kind == late]
                joined = a.merge(
                    b, on="root_id", suffixes=("_early", "_late"), validate="one_to_one"
                )
                c = joined[joined.complete_early & joined.complete_late]
                missed = a[~a.root_id.isin(b.root_id)]
                mc = missed[missed.complete]
                pairs.append(
                    dict(
                        level_type=kind,
                        direction=direction,
                        early=early,
                        later=late,
                        early_roots=len(a),
                        later_roots=len(b),
                        shared_roots=len(joined),
                        paired_complete=len(c),
                        paired_dates=c.date_early.nunique(),
                        mean_delay_minutes=(
                            (
                                c.timestamp_utc_late - c.timestamp_utc_early
                            ).dt.total_seconds()
                            / 60
                        ).mean(),
                        early_50_rate=c[f"{s}_hit_50_early"].mean(),
                        later_50_rate=c[f"{s}_hit_50_late"].mean(),
                        unavailable_later_roots=len(missed),
                        unavailable_later_complete=len(mc),
                        early_50_hits_without_later_entry=int(mc[f"{s}_hit_50"].sum()),
                    )
                )
    write("paired_entry_comparisons.csv", pd.DataFrame(pairs))
    overlap = (
        ev.groupby(["date", "timestamp_utc", "level_type", "root_id"])
        .agg(
            entry_records=("event_id", "size"),
            entry_kinds=("entry_kind", lambda x: ";".join(sorted(set(x)))),
        )
        .reset_index()
    )
    write("overlap_audit.csv", overlap)
    print("Primary family", len(evidence), "entry events", len(ev), flush=True)


if __name__ == "__main__":
    main()
