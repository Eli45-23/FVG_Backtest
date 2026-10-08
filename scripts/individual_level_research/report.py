"""Narrative and evidence index generated from complete aggregate tables."""

import json, hashlib, sqlite3
from pathlib import Path
import pandas as pd, numpy as np
from analyze import R, LEVELS, DIRS, folder, write

P = pd.read_csv(R / "all_levels_primary_outcomes.csv")
C = pd.read_csv(R / "all_levels_context_appendix.csv")
Q = pd.read_csv(R / "all_levels_data_quality.csv")
COUNT = pd.read_csv(R / "all_levels_interaction_counts.csv")
S = pd.read_csv(R / "same_date_baseline_sensitivity.csv")
A = pd.read_csv(R / "causal_audit.csv")
EP = pd.read_csv(R / "episode_behavior_descriptive.csv")
EX = pd.read_csv(R / "all_levels_excursion_baselines_and_revisits.csv")
KEY = ["level", "interaction", "stored_direction", "measured_direction"]
P = P.merge(
    S[KEY + ["effect", "ci_low", "ci_high", "p_value"]],
    on=KEY,
    how="left",
    suffixes=("", "_same_date"),
)
from engine.research.statistics import benjamini_hochberg

P["same_date_exploratory_q"] = benjamini_hochberg(
    P.p_value_same_date.fillna(1).tolist()
)
P["robustness_note"] = np.where(
    P.effect * P.effect_same_date < 0,
    "SIGN REVERSES with same-date controls",
    "Same sign or unavailable; not independent confirmation",
)
write(P, R / "all_levels_statistical_evidence.csv")
DEFINITIONS = {
    "PDH": "Maximum high of the immediately prior fully completed XNYS RTH session. Incomplete prior RTH prevents availability; no substitution of an older session.",
    "PDL": "Minimum low of the immediately prior fully completed XNYS RTH session. Incomplete prior RTH prevents availability; no substitution of an older session.",
    "PMH": "Highest high of all 114 complete 5m candles from 00:00 inclusive to 09:30 exclusive America/New_York on the same calendar date; frozen and available at 09:30. This is the official deliberate research convention.",
    "PML": "Lowest low of all 114 complete 5m candles from 00:00 inclusive to 09:30 exclusive America/New_York on the same calendar date; frozen and available at 09:30. This is the official deliberate research convention.",
    "O5H": "High of the complete 09:30–09:35 New York candle. Available at 09:35, never earlier. No prior optimized opening strategy rule is used.",
    "O5L": "Low of the complete 09:30–09:35 New York candle. Available at 09:35, never earlier. No prior optimized opening strategy rule is used.",
    "5m_SWING_HIGH": "Latest strict confirmed 5m pivot high with two left and two right complete adjacent candles; available at the second right candle close, 15 minutes after pivot start. Only the latest high persists, including after a break, until replaced.",
    "5m_SWING_LOW": "Latest strict confirmed 5m pivot low with two left and two right complete adjacent candles; available at the second right candle close, 15 minutes after pivot start. Only the latest low persists, including after a break, until replaced.",
    "4h_SWING_HIGH": "Latest strict confirmed 4h pivot high with two left and two right complete adjacent candles; available at the second right candle close, 12 hours after pivot start. Extended session, UTC midnight anchor: 00/04/08/12/16/20 UTC. Only the latest high remains exposed.",
    "4h_SWING_LOW": "Latest strict confirmed 4h pivot low with two left and two right complete adjacent candles; available at the second right candle close, 12 hours after pivot start. Extended session, UTC midnight anchor: 00/04/08/12/16/20 UTC. Only the latest low remains exposed.",
}


def val(x, d=3):
    if pd.isna(x):
        return "—"
    if isinstance(x, (float, np.floating)):
        return f"{x:.{d}f}"
    return str(x).replace("|", "/")


def table(df):
    if df.empty:
        return "*No eligible observations for this table.*"
    return (
        "| "
        + " | ".join(map(str, df.columns))
        + " |\n| "
        + " | ".join(["---"] * len(df.columns))
        + " |\n"
        + "\n".join(
            "| " + " | ".join(val(x) for x in row) + " |"
            for row in df.itertuples(index=False, name=None)
        )
    )


def evidence(df, classification=True):
    d = df.copy()
    d["Direction"] = d.stored_direction + " → " + d.measured_direction
    d["Event %"] = d.event_probability * 100
    d["Baseline %"] = d.baseline_probability * 100
    d["Effect pp"] = d.effect * 100
    d["95% CI pp"] = d.apply(
        lambda r: (
            f"[{r.ci_low*100:.2f}, {r.ci_high*100:.2f}]" if pd.notna(r.ci_low) else "—"
        ),
        axis=1,
    )
    d["Adverse Δ pp"] = d.adverse_effect * 100
    d["Same-date Δ pp"] = d.effect_same_date * 100
    d["Years +"] = d.positive_years
    d["p_value"] = d.p_value.map(lambda x: f"{x:.4g}" if pd.notna(x) else "—")
    d["bh_q_value"] = d.bh_q_value.map(lambda x: f"{x:.4g}" if pd.notna(x) else "—")
    cols = [
        "level",
        "interaction",
        "Direction",
        "events",
        "unique_dates",
        "Event %",
        "Baseline %",
        "Effect pp",
        "95% CI pp",
        "p_value",
        "bh_q_value",
        "Years +",
        "Adverse Δ pp",
        "Same-date Δ pp",
    ]
    if classification:
        cols += ["evidence_classification"]
    return table(d[cols])


def context_table(df):
    d = df.copy()
    d["Effect pp"] = d.effect * 100
    d["Event %"] = d.event_probability * 100
    d["Adverse %"] = d.adverse_probability * 100
    d["CI pp"] = d.apply(
        lambda r: (
            f"[{r.ci_low*100:.1f}, {r.ci_high*100:.1f}]" if pd.notna(r.ci_low) else "—"
        ),
        axis=1,
    )
    return table(
        d[
            [
                "interaction",
                "stored_direction",
                "measured_direction",
                "value",
                "events",
                "unique_dates",
                "Event %",
                "Adverse %",
                "Effect pp",
                "CI pp",
                "mean_mfe_atr",
                "mean_mae_atr",
                "exploratory_bh_q",
            ]
        ]
    )


coverage = []
best = []
for level in LEVELS:
    out = folder(level)
    if level in LEVELS[10:]:
        text = f"""# {level} — blocked study\n\n**Status: BLOCKED / INSUFFICIENT DATA. No behavioral conclusion is available.**\n\nThe immutable v2 Development source study ran the saved DisplacementBaseZoneDetectorV1 with its exact 4h UTC-midnight, extended-session convention. Independent replay found 6,403 4h buckets, 5,094 complete buckets, **zero usable ATR14 observations and zero zones**. Daily missing/incomplete buckets reset the strict 14-consecutive-bar ATR before it can initialize.\n\nThe frozen definition uses 1–3 base bars, maximum body/range 0.5, maximum base range/ATR 1.0, departure within 3 bars and minimum displacement 1.5 ATR, full-base bounds. It has not been relaxed to obtain a sample. In addition, the existing event adapter projects zones onto their proximal boundary. It does not implement all requested full/partial mitigation, distal close-through and zone retest semantics. Those are **NOT IMPLEMENTED**, not negative findings or valid zero hit rates.\n\nFirst entry, rejection, wick penetration, partial/full mitigation, close-through, failed break, retest and first/second/third contact analyses are all **blocked**. No chart examples exist because the provider emits no zones. No subjective zone or center line has been invented.\n\nSee [configuration](configuration.json), [foundation audit](../foundation_audit.json), and [master report](../MASTER_LEVEL_RESEARCH_REPORT.md). Exact source study: `{json.loads((out/'configuration.json').read_text())['study_id']}`. The registered primary hypothesis cells remain in the family with p=1 for correction; measured probabilities, intervals and p-values remain unavailable.\n\nBefore future zone research, freeze and version a viable gap/session-aware 4h volatility policy and a true two-boundary event adapter, prove causal regression behavior, then create new Development studies. This task preserves the existing engine and prior identities.\n"""
        (out / "LEVEL_RESEARCH_REPORT.md").write_text(text)
        coverage.append(
            dict(
                Level=level,
                Status="BLOCKED",
                Events=0,
                Dates=0,
                Complete_30m=0,
                Censored_30m=0,
                Censor_percent=np.nan,
                Study="5cb7fab0d4e7414792a3fbe59ded4999",
            )
        )
        continue
    e = pd.read_parquet(
        out / "events.parquet", columns=["event_id", "date", "observation_id"]
    )
    q = Q[(Q.level == level) & (Q.horizon.astype(str) == "30")].iloc[0]
    p = P[P.level == level]
    c = C[C.level == level]
    cfg = json.loads((out / "configuration.json").read_text())
    audit = A[A.level == level].iloc[0]
    coverage.append(
        dict(
            Level=level,
            Status="COMPLETE (point provider scope)",
            Events=len(e),
            Dates=e.date.nunique(),
            Complete_30m=q.complete,
            Censored_30m=q.censored,
            Censor_percent=q.censored / len(e) * 100,
            Study=cfg["study_id"],
        )
    )
    eligible = p[p.unique_dates >= 30]
    pos = (
        eligible[eligible.effect > 0]
        .sort_values(["bh_q_value", "effect"], ascending=[True, False])
        .head(1)
    )
    neg = eligible[eligible.effect < 0].sort_values(["bh_q_value", "effect"]).head(1)
    best.extend(pos.to_dict("records"))
    best.extend(neg.to_dict("records"))
    graded = p.evidence_classification.value_counts().to_dict()
    top = pd.concat([pos, neg])
    y = c[(c.dimension == "year") & (c.measured_direction == c.logical_direction)]
    # Display every major class/year in a compact effect matrix; full denominators/intervals remain CSV.
    ym = (
        y.pivot(
            index=["interaction", "stored_direction", "measured_direction"],
            columns="value",
            values="effect",
        )
        .mul(100)
        .reset_index()
    )
    touch = c[
        (c.dimension == "touch_group")
        & (c.interaction == "TOUCH")
        & (c.measured_direction != c.stored_direction)
    ]
    tm = c[
        (c.dimension == "time_window")
        & c.interaction.isin(["BREAK_ACCEPTANCE", "BREAK_FAILED_NEXT_CANDLE_HOLD"])
        & (c.measured_direction == c.logical_direction)
    ]
    vg = c[
        (c.dimension == "atr_regime")
        & (c.interaction == "BREAK_ACCEPTANCE")
        & (c.measured_direction == c.logical_direction)
    ]
    epi = EP[(EP.level == level) & EP.year.isna()]
    text = f"""# {level} — individual Development level study\n\n**Development only · 2020-01-01 inclusive through 2024-01-01 exclusive.** No strategy, stop, target, trade win rate or profitability is inferred.\n\n## Definition and identity\n\n{DEFINITIONS[level]}\n\nStudy `{cfg['study_id']}`; dataset `research_2020_2026`; full source hashes and settings in [configuration.json](configuration.json). Interactions are observed during actual XNYS RTH, including early closes. Numerical ranges and saved eligibility buckets are empty. Other levels are context only; no confluence requirement.\n\n{len(e):,} event records, {e.observation_id.nunique():,} root observations, {e.date.nunique():,} dates. There are {int(q.complete):,} complete and {int(q.censored):,} censored 30-minute records ({q.censored/len(e):.2%}); {int(q.missing_atr)} complete records lack ATR. Censored outcomes are retained and never treated as misses.\n\n## Main evidence and uncertainty\n\nRegistered primary grading counts: {json.dumps(graded,sort_keys=True)}. These are overlapping hypotheses, not independent discoveries. The following rows show the lowest-q positive and negative effects with at least 30 matched dates, without hiding the opposite result. The evidence-table `events` and `unique_dates` columns count matched complete outcomes; total and censored source counts are shown separately. Cells with fewer than 30 dates are too small for a stable interpretation. Direction means **stored event direction → measured future price direction**; a negative effect means reduced probability of that measured move.\n\n{evidence(top)}\n\nThe main benchmark matches year, half-hour and causal ATR bucket. The same-date sensitivity is exploratory and can overcondition on overlapping intraday paths. A sign reversal nevertheless makes a claim of a distinct standalone level effect fragile. Primary labels describe the registered benchmark; they do not override this caveat or establish a tradable edge.\n\n## Every supported interaction\n\n{table(COUNT[COUNT.level==level].drop(columns='level'))}\n\nTouch means a new touching episode. Raw rejection needs close-back clearance 0.25 points and minimum penetration 0; sweep requires strictly positive penetration. Break needs a strict close across the level. Adjacent close/full holds and failures use exact complete consecutive candles. Retest is a distinct later touching episode; retest hold/fail is its close, with full hold confirmed by the adjacent subsequent candle. Rejection/sweep confirmation requires the next close beyond the event candle extreme. Full details and direction conventions are in [method notes](../ADDITIONAL_METHOD_NOTES.md).\n\n## Forward outcomes\n\nAll six horizons and both directional interpretations are in [ATR outcomes](atr_outcomes.csv), [fixed-point outcomes](fixed_point_outcomes.csv), [forward distributions](forward_distributions.csv) and [excursion/baseline/revisit comparison](excursion_baselines_and_revisits.csv). MFE/MAE and close means/medians, threshold times and p10/p25/p50/p75/p90/p95 are retained. Hit times are one-minute upper bounds; simultaneous opposite moves have no known tick ordering.\n\n{table(Q[Q.level==level][['horizon','events','complete','censored','missing_atr','unmatched','censor_reasons']])}\n\n## Yearly repeatability\n\nEffect in percentage points at 30 minutes / 1 ATR for each mechanically intended direction. TOUCH/RETEST are neutral contacts, so both directions remain available in the full CSV. This is not a formal year-interaction test.\n\n{table(ym)}\n\n[Complete yearly table](yearly_stability.csv) includes events, dates, complete/censored, probabilities, intervals, MFE/ATR and MAE/ATR. Negative and small-sample years remain visible.\n\n## First and repeated touching episodes\n\nThese are **away-from-approach** TOUCH outcomes, not a claim that every contact rejects.\n\n{context_table(touch)}\n\nEpisode-level incidence and spacing (daily weighted incidences; descriptive, not forward trade success):\n\n{table(epi[['episode_group','episodes','dates','daily_break_incidence','daily_rejection_incidence','daily_sweep_incidence','median_gap_minutes','median_level_age']])}\n\nTouch numbering resets per level identity/date. Compound root and confirmation candles can differ. [Episode ledger](touch_episode_ledger.csv) preserves the first touching candle separately. [Overlap audit](overlap_audit.csv) preserves shared roots. Do not sum classes as independent observations.\n\n## Time of day\n\nUnfiltered break continuation and failed-break reversal at the four requested broad confirmation-time windows:\n\n{context_table(tm)}\n\n## Volatility and context\n\nCausal low/middle/high ATR regimes for unfiltered breaks:\n\n{context_table(vg)}\n\n[Context appendix](context_comparisons.csv) also includes EMA alignment, above/below VWAP, confirmed 5m structure, directional efficiency (<0.25 / 0.25–0.50 / >=0.50), prior-day range/ATR, opening range/ATR and level age. These are one-variable descriptive splits. They are not combined, optimized or converted into eligibility filters. Swing prior-break state is separately exported in the [master supplement](../swing_previously_broken_exploratory.csv).\n\n## Causal and chart audit\n\nAll {int(audit.events_checked):,} records passed independent level-price, availability, candle OHLC, session-boundary, compound-parent, strict close/full-hold and touch-count checks. {int(audit.charts)} charts and {int(audit.independent_outcome_labels_checked)} independently recalculated 1m horizon labels were checked.\n\n[Chart contact sheet](chart_audit/CONTACT_SHEET.jpg) · [exact chart/event index](../chart_audit_index.csv) · [causal audit](../causal_audit.csv). Chart examples were selected chronologically, not by favorable outcome. Levels are drawn only after availability; outcome shading begins after confirmation and ends by actual RTH close.\n\n## Complete exports and limitations\n\n`events.parquet` contains every selected event, source payload and contextual field. `outcomes_5.parquet`, `outcomes_10.parquet`, `outcomes_15.parquet`, `outcomes_30.parquet`, `outcomes_60.parquet`, and `outcomes_session_close.parquet` contain all joined labels and matched probabilities, including censored rows. They are local immutable-study-derived artifacts, referenced by hash in the bundle manifest rather than sampled into the ZIP. Original full JSON payloads and raw identities remain in the source-study Parquet files.\n\nNo Validation or OOS outcome was queried for this report. PDH/PDL Development findings were previously inspected; this expanded comparison is not presented as a fresh universally untouched sample. Primary bootstrap intervals are conditional on the matched pool. Full methodological limitations apply, including overlapping forward windows, conditional censoring, fixed-bucket residual volatility differences and continuous-contract data semantics.\n"""
    (out / "LEVEL_RESEARCH_REPORT.md").write_text(text)
coverage = pd.DataFrame(coverage)
write(coverage, R / "coverage_summary.csv")
best = pd.DataFrame(best)
write(best, R / "level_evidence_overview.csv")
strong = P[P.evidence_classification == "STRONG DEVELOPMENT EVIDENCE"]
prom = P[P.evidence_classification == "PROMISING BUT EXPLORATORY"]
neg = P[P.evidence_classification == "NEGATIVE EVIDENCE"]
rank = P[(P.unique_dates >= 30) & (P.effect > 0)].sort_values(
    ["bh_q_value", "effect"], ascending=[True, False]
)
# Prioritize distinct event mechanisms, never duplicate retest aliases, for measurement follow-up.
hypotheses = P[
    (
        (P.level == "5m_SWING_LOW")
        & (P.interaction == "TOUCH")
        & (P.stored_direction == "DOWN")
        & (P.measured_direction == "UP")
    )
    | (
        (P.level == "PML")
        & (P.interaction == "BREAK_FAILED_NEXT_CANDLE_HOLD")
        & (P.stored_direction == "DOWN")
        & (P.measured_direction == "DOWN")
    )
].sort_values("bh_q_value")
rev = P[
    P.interaction.isin(
        [
            "REJECTION",
            "SWEEP_RECLAIM",
            "BREAK_FAILED_NEXT_CANDLE_HOLD",
            "BREAK_RETEST_FAIL",
            "REJECTION_CONFIRMATION",
            "SWEEP_RECLAIM_CONFIRMATION",
        ]
    )
    & (P.measured_direction == P.logical_direction)
    & (P.unique_dates >= 30)
].sort_values(["bh_q_value", "effect"], ascending=[True, False])
cont = P[
    P.interaction.isin(
        [
            "BREAK_ACCEPTANCE",
            "BREAK_NEXT_CANDLE_CLOSE_HOLD",
            "BREAK_NEXT_CANDLE_FULL_HOLD",
            "BREAK_RETEST_HOLD",
            "BREAK_RETEST_FULL_HOLD",
        ]
    )
    & (P.measured_direction == P.logical_direction)
    & (P.unique_dates >= 30)
].sort_values(["bh_q_value", "effect"], ascending=[True, False])
priors = P[
    (P.level == "PDH")
    & (P.interaction == "BREAK_FAILED_NEXT_CANDLE_HOLD")
    & (P.stored_direction == "UP")
    & (P.measured_direction == "DOWN")
]
text = (
    f"""# MNQ Individual Key-Level Master Research Report\n\n**Development-only, 2020–2023. Ten point-level studies completed; supply and demand remain blocked. No strategies were built or optimized.**\n\n## A — Executive summary\n\nThe common protocol measures {int(coverage.Events.sum()):,} event records across ten point-level families, with overlapping labels explicitly preserved. PMH/PML use the corrected **00:00–09:30 America/New_York** window. Eight families reuse completed study `5cb7fab0d4e7414792a3fbe59ded4999`; PMH/PML use new immutable study `78c96aa0e91147ba9913e365f33ed2f9`.\n\nThe registered 30-minute / 1-ATR family contains 672 comparisons. Against the specified year/time/volatility matched pool, {len(strong)} satisfy the numerical **STRONG DEVELOPMENT EVIDENCE** screen, {len(prom)} are **PROMISING BUT EXPLORATORY**, {len(neg)} show **NEGATIVE EVIDENCE**, {sum(P.evidence_classification=='NO MEANINGFUL EVIDENCE')} show **NO MEANINGFUL EVIDENCE**, and {sum(P.evidence_classification=='INSUFFICIENT DATA')} are **INSUFFICIENT DATA** (including the 112 unavailable zone hypotheses). These counts are hypotheses, not independent edges.\n\n**The principal finding is benchmark sensitivity.** {sum(strong.effect*strong.effect_same_date<0)} of the {len(strong)} primary strong-positive associations reverse sign against ordinary observations from the same date/time/ATR cell. Most strong pooled results concern downward moves. This is consistent with level interactions selecting different intraday paths or directional sessions; it does not establish that the level itself contributes a stable standalone advantage. Same-date controls are an exploratory, potentially overconditioned comparison, not a replacement primary test. Neither benchmark alone justifies a trading rule.\n\nNo standalone behavior is promoted to a strategy in this report. The observations below merit measurement review, with particular attention to day/path selection, overlapping controls and whether favorable effects survive a separately frozen baseline protocol.\n\n## B — All twelve level families\n\n{table(coverage)}\n\nEvent totals include overlapping interaction labels and are not summed into independent observations. Dates count sessions with at least one event for that level, not all sessions where the level was available. The source has 1,006 XNYS Development sessions. PM coverage is complete on 990 and unavailable on 16; all affected dates and missing candle starts are exported.\n\n"""
    + "\n".join(
        f"- [{l} report]({d}/LEVEL_RESEARCH_REPORT.md)" for l, d in zip(LEVELS, DIRS)
    )
    + f"""\n\n## C — Rejection and reversal behavior\n\nLowest-q mechanically directed reversal observations with at least 30 dates; all remaining, negative and inconclusive comparisons remain in the full evidence table.\n\n{evidence(rev.head(8))}\n\nPMH failed retests and confirmed rejection have notable pooled downward associations, but the same-date sensitivity substantially weakens or reverses them. Raw support/resistance names alone do not determine direction: a high level approached from above can break downward, and a low level can be reclaimed upward.\n\nThe previously investigated PDH failed upward break is not given preferred status. The broad all-touch-count comparison now shows:\n\n{evidence(priors)}\n\nThis is not the prior first-touch-only 67-event candidate sample. The new common family neither imports its old isolated q-value nor reuses strategy P&L as event evidence.\n\n## D — Breakout and continuation behavior\n\n{evidence(cont.head(10))}\n\nDownward breaks at PMH, O5H, O5L, PDH, PDL and PML produce positive pooled effects. Their same-date comparisons frequently turn negative. Clean upward holds often reduce subsequent downward-threshold probability rather than increase upward MFE substantially. Reduced adverse excursion is distinct from a profitable continuation trade.\n\n## E — First touch versus repeated tests\n\nEvery individual report displays first, second, third and fourth-plus episode outcomes, with the exact first touching candle and compound root preserved. [Complete repeated-touch evidence](all_levels_touch_number.csv) and [episode behavior](episode_behavior_descriptive.csv) provide denominators and uncertainty. Episode incidence describes whether a break/rejection/sweep was recorded while the engine carried that episode number; it is not a fixed-horizon success rate. There is no universal first-touch advantage. For 5m swing-low contacts approached from above, upward-hit effects are +3.67 percentage points on episode 1 (1,004 matched dates), +0.29 on episode 2 (240 dates), and +15.43 on episode 3 (only 18 dates). The third estimate is insufficient for a stable conclusion; there are no fourth-plus contacts in this directional slice. For the previously inspected PDH first-episode failed-upward-break slice, 67 source events become 64 complete 30-minute observations on 56 dates, with +21.49 points and exploratory q=0.0283; later-episode effects alternate sign. This is retained as prior-inspected exploratory evidence, not promoted above the common primary comparison. Differences between two subgroup estimates are descriptive unless a direct contrast is tested; separate significance in one group is not proof of a difference between groups.\n\n## F — Market regimes and indicator context\n\n[Volatility tables](all_levels_volatility_regimes.csv), [full context appendix](all_levels_context_appendix.csv), and each report retain low/middle/high ATR, fixed ATR buckets, prior-day/opening range normalization, efficiency, EMA, VWAP and confirmed structure. No context combinations were tested as eligibility rules. Regime splits are exploratory, and their global exploratory q-values do not replace primary q-values. Same-date sensitivity is a warning that broad market path matters even after year/time/ATR matching. Regime labels are local rolling percentiles, not fixed long-term volatility quantiles: 343 of 372 complete PMH failed-retest observations are HIGH, only 26 MIDDLE and 3 LOW. The low-regime estimate is insufficient. For 5m swing-low upward contact response, the pooled effect is +3.77 points in HIGH, +9.21 in MIDDLE and +1.30 in LOW, but LOW has only 26 dates. These differences cannot justify a volatility filter. The complete indicator appendix similarly reports broad single-feature differences without combining them.\n\n## G — Yearly repeatability\n\nAll 2020, 2021, 2022 and 2023 rows are retained in [yearly stability](all_levels_yearly_stability.csv). The numerical strong screen requires positive primary effects in all four years, at least 10 dates per year and at least 100 overall dates. That is evidence of sign consistency against this benchmark, not independent replication: the years were all used in Development. No level is selected because one year carries its result. The 5m swing-low upward-contact effect is +3.83, +6.93, +2.76 and +1.82 percentage points in 2020–2023, respectively. The PML failed-downside-break/downward-outcome effect is −2.84, +5.54, +18.29 and +4.77 points: 2022 is clearly larger, and 2020 contradicts a uniformly favorable claim.\n\n## H — Negative findings\n\n{evidence(neg.sort_values('effect').head(10))}\n\nMany negative rows describe a *lower* chance of the opposite-direction move following a confirmed break. They may be useful behavioral observations but are not losses or inverse trading recommendations. Four-hour support/resistance has much fewer eligible dates; no positive comparison meets the primary strong/promising screen. Supply/demand absence is a provider blocker, not evidence that zones do not work.\n\n## I — Statistical reliability\n\nPrimary family: all 12 levels × 14 interaction types × two stored directions × two measured future directions, 30 minutes and 1 ATR. The 672-cell family was registered before expanded aggregate results. The alias correction for the failed-next-candle enum is recorded. Unavailable hypotheses use p=1 only for multiplicity correction; no probabilities are invented.\n\nBaseline strata are year × confirmation half-hour × causal fixed ATR14 bucket. Per-date event and matched-baseline means are differenced, with equal date weights. The existing Lab bootstrap uses 2,000 resamples, seed 1729, centered two-sided p-values and percentile 95% intervals. Minimum attainable p is 1/2001. BH is applied over the full primary family. The complete grid and contextual analyses are separately labeled exploratory families. Small samples, unknown approach direction and censored horizons remain visible.\n\nThe pooled baseline is estimated from the same Development data and held fixed in the primary date bootstrap. This is conditional empirical-benchmark inference. It does not fully propagate re-estimation of the control pool into a new market-history sample. Overlapping labels and windows make hypotheses dependent; BH is not a cure for arbitrary dependence or prior discovery selection. See [complete method notes](ADDITIONAL_METHOD_NOTES.md).\n\n[Same-date sensitivity](same_date_baseline_sensitivity.csv) pairs ordinary controls and event observations within a date, then clusters dates. It is diagnostic, not a post-hoc replacement of the registered result. Strong sensitivity prevents a confident level-specific or economic-edge claim.\n\n## J — Cross-level evidence overview\n\nLowest-q positive and negative row per measured point family with at least 30 dates. All entries use horizon **30 minutes**, target **1 ATR**. The full [672-row primary family](all_levels_primary_outcomes.csv) and [evidence plus sensitivity](all_levels_statistical_evidence.csv) contain every comparison, including unavailable zone cells.\n\n{evidence(best)}\n\n## K — Standalone hypotheses for further measurement review\n\nThese are priorities for checking the measurement interpretation, **not selected trading edges**. No five-hypothesis quota is imposed. Two distinct level families retain positive associations in both benchmark readings; neither satisfies a strong, broadly robust standalone-edge claim.\n\n{evidence(hypotheses)}\n\nThe first is an upward response after approaching the latest confirmed 5m swing low from above: +3.84 percentage points in the primary comparison (q=0.0096), positive in all four years, but modest in magnitude. Mean favorable excursion is below mean adverse excursion, so the hit-rate difference is not an economic payoff claim. The second is renewed downward movement after a PML downside break immediately fails back above the level: +7.24 points (q=0.0893), with a negative 2020 effect and a much larger 2022 effect. It is exploratory and unstable, despite a positive same-date sensitivity. These observations deserve review of the measurement, not immediate strategy construction. No stop, target, cutoff or position sizing was selected.\n\n## L — Recommended next research phase\n\nFirst review the benchmark sensitivity, overlap and censoring tables, including the negative findings. Freeze a measurement robustness protocol before further hypothesis selection. Separately repair the zone research foundation through a versioned, documented session/gap-aware volatility convention and true upper/lower-boundary events; do not substitute a guessed zone detector or mutate old studies.\n\nOnly after that review should a small number of standalone hypotheses be considered for later controlled research. PDH/PDL, midnight PMH/PML, O5, 5m/4h structure, zones and EMA/VWAP remain available as future context; no multi-level confluence or indicator-combination experiment was performed here. Validation and sealed OOS remain outside this project.\n\n## Verification and delivery\n\nAll {int(A.events_checked.sum()):,} point-event records passed the independent causal checks. There are {int(A.charts.sum())} representative charts, {int(A.independent_outcome_labels_checked.sum())} independently recalculated one-minute horizon labels, and 70,081 independently verified strict swing confirmations. No causal audit failures were found. Point-level interaction classes overlap; full source IDs and roots are exported.\n\nThe midnight study's detection runtime was 95.99 seconds; timings, sizes and source hashes are in [evidence index](EVIDENCE_INDEX.json). Source 1m/5m identities and the reused immutable study are checked before and after analysis. Existing saved strategies, runs and reveal records are preserved. No production strategy/execution code was changed. Historical golden runs were not rerun against reserved later-year data. Relevant synthetic/Development engine tests and analysis checks are recorded in [verification](verification_results.json).\n\nThe ZIP contains reports, aggregate tables, configurations, reproducibility scripts and representative charts. Full unsampled event/label Parquet artifacts stay local and are linked by path, byte size and SHA-256 in the manifest. No Validation outcome was queried; no saved OOS study was revealed; no paid download or optimization was performed; nothing was pushed.\n"""
)
(R / "MASTER_LEVEL_RESEARCH_REPORT.md").write_text(text)
print("reports created", len(coverage))
