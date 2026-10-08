import json, itertools, hashlib
import pandas as pd, numpy as np
from analyze import R, LEVELS, DIRS, folder, K, write, OLD
from engine.research.statistics import benjamini_hochberg


def combine(name):
    return pd.concat(
        [pd.read_csv(folder(l) / name) for l in LEVELS[:10]], ignore_index=True
    )


def main():
    a = combine("atr_outcomes.csv")
    ct = combine("context_comparisons.csv")
    q = combine("data_quality.csv")
    cnt = combine("interaction_counts.csv")
    ov = combine("overlap_audit.csv")
    # Include unavailable prespecified hypotheses as p=1 in the common correction family.
    family = pd.DataFrame(
        itertools.product(LEVELS, K, ["UP", "DOWN"], ["UP", "DOWN"]),
        columns=["level", "interaction", "stored_direction", "measured_direction"],
    )
    p = family.merge(
        a[(a.horizon.astype(str) == "30") & (a.atr_target == 1)],
        on=list(family.columns),
        how="left",
        validate="one_to_one",
    )
    p["p_for_correction"] = p.p_value.fillna(1)
    p["bh_q_value"] = benjamini_hochberg(p.p_for_correction.tolist())
    # Full grid and contextual splits form explicitly exploratory families; never replace primary q.
    a["exploratory_bh_q"] = benjamini_hochberg(a.p_value.fillna(1).tolist())
    ct["exploratory_bh_q"] = benjamini_hochberg(ct.p_value.fillna(1).tolist())
    years = ct[ct.dimension == "year"]
    keys = ["level", "interaction", "stored_direction", "measured_direction"]
    stab = (
        years.assign(positive=years.effect > 0, sufficient=years.unique_dates >= 10)
        .groupby(keys)
        .agg(
            positive_years=("positive", "sum"),
            years_with_10_dates=("sufficient", "sum"),
            years_observed=("value", "nunique"),
            worst_year_effect=("effect", "min"),
            best_year_effect=("effect", "max"),
        )
        .reset_index()
    )
    p = p.merge(stab, on=keys, how="left")

    def classify(r):
        if pd.isna(r.events) or r.unique_dates < 30:
            return "INSUFFICIENT DATA"
        if r.bh_q_value <= 0.05 and r.effect <= -0.03:
            return "NEGATIVE EVIDENCE"
        if (
            r.bh_q_value <= 0.05
            and r.effect >= 0.05
            and r.unique_dates >= 100
            and r.positive_years == 4
            and r.years_with_10_dates == 4
        ):
            return "STRONG DEVELOPMENT EVIDENCE"
        if (
            r.bh_q_value <= 0.1
            and r.effect >= 0.03
            and r.unique_dates >= 30
            and r.positive_years >= 3
        ):
            return "PROMISING BUT EXPLORATORY"
        return "NO MEANINGFUL EVIDENCE"

    p["evidence_classification"] = p.apply(classify, axis=1)
    p["favorable_minus_adverse_effect"] = p.effect - p.adverse_effect
    p["interpretation"] = np.where(
        p.measured_direction == p.logical_direction,
        "mechanical reaction direction",
        "opposite direction",
    )
    p.loc[p.interaction.isin(["TOUCH", "RETEST", "BREAK_RETEST"]), "interpretation"] = (
        "direction-neutral contact; both readings retained"
    )
    write(p, R / "all_levels_primary_outcomes.csv")
    write(p, R / "all_levels_statistical_evidence.csv")
    write(a, R / "all_levels_atr_outcomes.csv")
    write(a, R / "all_levels_baseline_effects.csv")
    write(q, R / "all_levels_data_quality.csv")
    write(cnt, R / "all_levels_interaction_counts.csv")
    write(ov, R / "all_levels_overlap_audit.csv")
    write(
        combine("fixed_point_outcomes.csv"), R / "all_levels_fixed_point_outcomes.csv"
    )
    for dim, name in [
        ("year", "yearly_stability"),
        ("time_window", "time_of_day"),
        ("touch_group", "touch_number"),
        ("atr_regime", "volatility_regimes"),
    ]:
        write(ct[ct.dimension == dim], R / f"all_levels_{name}.csv")
    write(ct, R / "all_levels_context_appendix.csv")
    configs = []
    for l in LEVELS[:10]:
        configs.append(json.loads((folder(l) / "configuration.json").read_text()))
        for f in [
            "primary_outcomes",
            "statistical_evidence",
            "atr_outcomes",
            "baseline_effects",
            "yearly_stability",
            "time_of_day",
            "touch_number",
            "volatility_regimes",
        ]:
            x = pd.read_csv(R / f"all_levels_{f}.csv")
            write(x[x.level == l], folder(l) / (f + ".csv"))
    for l in LEVELS[10:]:
        f = folder(l)
        f.mkdir(exist_ok=True)
        c = {
            "logical_level_filter": l,
            "study_id": OLD,
            "status": "BLOCKED_NO_ELIGIBLE_ZONES",
            "configuration": json.loads((R / "foundation_audit.json").read_text()),
            "reason": "Strict contiguous 4h ATR14 never available; zero causal zones. Existing point-boundary adapter does not implement full zone mitigation events.",
        }
        (f / "configuration.json").write_text(json.dumps(c, indent=2))
        configs.append(c)
    (R / "all_levels_research_configurations.json").write_text(
        json.dumps(configs, indent=2)
    )
    print(
        "primary",
        len(p),
        "observed",
        p.events.notna().sum(),
        "strong",
        p.evidence_classification.eq("STRONG DEVELOPMENT EVIDENCE").sum(),
        "promising",
        p.evidence_classification.eq("PROMISING BUT EXPLORATORY").sum(),
    )


if __name__ == "__main__":
    main()
