"""Readable evidence report and stable artifact/source manifest."""

from pathlib import Path
import sys, json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pml_feasibility.run import P, M, S, sha
from engine.canonical import dumps


def table(frame, cols=None):
    x = frame[cols] if cols else frame

    def cell(v):
        if pd.isna(v):
            return "—"
        if isinstance(v, float):
            return f"{v:,.4f}"
        return str(v).replace("|", "/")

    return (
        "| "
        + " | ".join(x.columns)
        + " |\n| "
        + " | ".join(["---"] * len(x.columns))
        + " |\n"
        + "\n".join(
            "| " + " | ".join(cell(v) for v in r) + " |"
            for r in x.itertuples(index=False, name=None)
        )
    )


def run():
    load = lambda name: pd.read_csv(P / name)
    stops = load("stop_comparison.csv")
    fixed = load("fixed_target_diagnostics.csv")
    years = load("yearly_stability.csv")
    cost = load("fee_slippage_sensitivity.csv")
    episodes = load("episode_analysis.csv")
    quality = load("pml_data_quality_audit.csv")
    raw = load("exact_raw_events.csv")
    paths = load("all_event_paths.csv")
    reference = json.loads((P / "registered_finding_reproduction.json").read_text())
    concentration = load("year_2022_concentration.csv")
    method = """# Methodology and caveats

Status: DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY. All candle/outcome queries are bounded to New York 2020-01-01 inclusive / 2024-01-01 exclusive. Calendar metadata can contain later dates; those are not market outcomes. Whole-source hashes verify identity without querying later predictive observations. No database access, strategy registration, reveal, paid download or production change is performed.

## Frozen population and causality

Immutable study 78c96aa0e91147ba9913e365f33ed2f9 supplies PML compound events. PML requires every complete, valid, clock-adjacent five-minute bar starting 00:00 through 09:25 America/New_York on the same date. Exact 114-bar windows confirm at 09:30, freeze for RTH and have no stale fallback. Missing/invalid windows have no PML. DST follows timezone-aware timestamps. Actual frozen XNYS sessions include early closes.

The root BREAK_ACCEPTANCE approaches from ABOVE (previous adjacent valid RTH close, otherwise current open) and closes strictly BELOW PML. The immediately adjacent complete failure bar closes strictly ABOVE PML. Equality does not qualify. Confirmation is the failure close; no later candle participates. The compound direction DOWN is inherited from the root. Its natural reversal label in the master was UP; this task explicitly evaluates the opposite, renewed DOWN movement.

Touch numbers count distinct touching episodes, not individual candles; an episode begins when a candle spans the level after the previous candle was not touching. Missing/invalid bars reset touching/break state; day changes reset the count. The compound inherits the root touch number, observation and root identity. It is not a new touch. Every candidate/root ID is unique in this selected class, but dates repeat and other event classes overlap; observations are not independent portfolio trades. A gap-crossing break can theoretically carry count zero; any actual zero is retained and disclosed, never silently recoded.

An independent causal replay uses the same frozen level and sequence definitions, keeps only confirmations of RTH bars, and reproduces all 407 IDs and episode numbers. No future labels are exposed to that replay. Each event's root/failure OHLC, availability, origin, adjacency and PML minimum is separately checked against source bars. The 387 complete 30m events on 274 dates are a statistical reference only. Twenty session-censored events are retained in the 407-event/286-date execution population. No raw ATR or 30m missing-minute exceptions occur here.

## Entry, stop, fills and costs

All 407 signals enter the entry-definition analysis independently. No one-trade/day or overlap lock is imposed: this is event feasibility, not a deployable strategy. Short entry is tick-rounded failure close minus 0/1/2 adverse ticks. Stop A is maximum root/failure high + .25; B is failure high + .25; C is root high + .25, outward rounded. Nonpositive executed risk is explicitly rejected. Because risk uses executed entry, Stop C eligibility may differ across slippage scenarios; raw signal identity never changes. Stop C may lie inside an already completed failure candle: pre-entry activity never triggers a fill.

Target is executed entry minus original risk × 0.5/1/1.5, rounded with the unchanged engine's HALF_UP MNQ tick behavior. The actual rounded payoff can differ slightly from nominal R for fractional-tick products. Ownership begins with the minute starting at confirmation. Production engine.partial_execution.execute performs every fill; an independent mirrored numerical implementation checks exit reason, price, timestamp, fee P&L, conflict and MFE/MAE. SHORT stop gaps fill at max(stop, minute open), then adverse exit slippage; targets fill at target plus adverse exit slippage. Stop wins simultaneous stop/target touches. Final owned minute stop/target precedes actual XNYS-close exit. No management or partial exits.

Fee components per side are user-supplied actual Webull .25 commission + .35 exchange + .12 clearing + .01 NFA = .73 per MNQ; completed one-micro trades pay 1.46. $2/point. No website estimate. Gross USD includes slippage but precedes fees. Net R = net USD / original risk USD. Five signals confirm at session close and have no owned minute: retained as NO_POST_ENTRY_SESSION_MINUTES without inventing a same-close round trip. Missing owned minutes would produce EXECUTION_DATA_UNAVAILABLE; signals would remain in the causal population. None of the completed diagnostic executions encounters a missing owned minute.

## Measurement denominators and path ordering

Paths run until structural stop or session close without a target; the fixed-target table is separate. A horizon rate requires a complete 15/30/60-minute observation within session and continuous source coverage, even if a stop resolves sooner. Censored horizons are null, not losses or zeros. Session-wide races retain all resolvable paths, including short remaining sessions. ATR unavailability would null only ATR metrics. Every aggregate exposes execution, complete/censored and metric-specific denominators. Horizon races use only minutes before the stated cutoff. Thresholds are descriptive continuous point/R values; executable targets are tick-rounded.

Stop/favorable touches in one minute resolve stop-first; +0.5R versus -0.5R resolves adverse-first. Full exit-minute high/low are retained for reported excursion upper bounds, even though their order relative to the stop is unknown. Lower bounds use only prior complete minutes. MAE before a favorable hit is bounded by extrema before the hit minute versus including it. Thus an inclusive MFE >=1R does not imply +1R was reached before stop. Full-bar excursion means can be large despite poor executable races. Times are minutes to minute-end; intraminute timestamps are unavailable.

## Statistics, context and interpretation

Historical primary probabilities average within date then equally across dates, against year/half-hour/causal-volatility matched ordinary observations. The seeded date-cluster bootstrap reproduces the saved CI and p-value. BH correction retains all 672 registered hypotheses, not only this favorable candidate. The same-date sensitivity is cited from its immutable exploratory artifact. Execution tables are event-weighted descriptive results, not new statistically independent edge tests; no new selected-subset significance claim is made.

Drawdown is chronological closed-diagnostic P&L (exit timestamp then event ID), starting at zero. Overlapping hypothetical positions and concurrent exits prevent interpreting it as a one-position portfolio drawdown. Annual and episode splits are descriptions, never eligibility rules. No target or stop is chosen by maximum in-sample profit.

Confirmed structure state and ATR regime come from saved causal event context. BOS/CHoCH history is reconstructed using only complete Development 5m bars and frozen 2-left/2-right pivots; the most recent structural-break state may precede today's session. At-confirmation break field is separate. Existing compound context can inherit root-level room metadata, so this audit explicitly recalculates distance from FAILURE CLOSE to nearest known lower point-level price in saved chart_context, divided by confirmation ATR. It is available-context room, not a guarantee of support-free future travel. RTH-open minus PML / ATR is signed and descriptive. Neither context nor indicators filter events.

The candidate remains Development-only, previously selected from a multiple-comparison master study, not validated. Positive unbounded directional frequency does not establish executable profitability. No Validation or OOS result is inspected, and no new strategy is built.
"""
    (P / "methodology_and_caveats.md").write_text(method)
    raw_counts = raw.touch_group.astype(str).value_counts().sort_index()
    horizon = []
    for r in stops.itertuples():
        for h in [15, 30, 60]:
            rr = stops[stops.stop == r.stop].iloc[0]
            row = {
                "stop": r.stop,
                "horizon_minutes": h,
                "complete": rr[f"{h}m_complete"],
                "censored": rr[f"{h}m_censored"],
            }
            for col in [
                "r0p5",
                "r1",
                "r1p25",
                "r1p5",
                "r2",
                "atr0p5",
                "atr1",
                "atr1p5",
            ]:
                row[col + "_before_stop_pct"] = rr[f"{h}m_{col}_before_stop_pct"]
            horizon.append(row)
    writeframe = pd.DataFrame(horizon)
    writeframe.to_csv(
        P / "horizon_threshold_summary.csv",
        index=False,
        float_format="%.12g",
        lineterminator="\n",
    )
    doc = f"""# PML Failed Break — Execution Feasibility v1

**DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY · 2020–2023 · SHORT after failed downside hold.**

**Conclusion: DIRECTIONAL_BUT_POOR_RISK_PATH. No controlled strategy backtest is recommended from these frozen entry/stop diagnostics.** All nine primary fixed-target combinations lose after actual Webull fees and one adverse tick on each side. All nine also lose with zero slippage and actual fees. No stop, target or context filter is selected.

## Exact finding and populations

The published finding reproduces: 30m downward 1ATR probability **{reference['event_probability']*100:.5f}%**, matched **{reference['baseline_probability']*100:.5f}%**, effect **{reference['effect']*100:.5f} percentage points**, 95% date-cluster CI **[{reference['ci_low']*100:.5f}, {reference['ci_high']*100:.5f}]**, p **{reference['p_value']:.8f}**, full-family BH q **{reference['bh_q_value']:.8f}** (672 comparisons). This is exploratory Development evidence, not a net-trading edge. Historical same-date sensitivity is about +4.991pp; its exact saved row is exported separately.

| Population | Events | NY dates |
| --- | ---: | ---: |
| Raw causal execution population | 407 | 286 |
| Complete 30m outcomes | 387 | 274 |
| Complete 30m + usable ATR reference | 387 | 274 |
| Session-boundary 30m censored | 20 | {raw.loc[~raw.measurement_complete_30m,'date'].nunique()} |
| Missing-minute 30m censored | 0 | 0 |
| ATR unavailable | 0 | 0 |

407 = 387 + 20. The ATR/missing categories overlap neither group here because both are zero. Seven dates occur in both complete and censored groups: 274 + 19 - 7 = 286 unique dates. Five of the 20 session-censored signals confirm exactly at close: valid causal events, but no post-entry session minute. The other 15 remain ordinary stop/target/session-close candidates. Repeated dates and overlapping event studies are not independent observations.

## Exact mechanics and PM coverage

PML = minimum of **114 complete five-minute candles, 00:00 through 09:25 NY**, same date; confirmed/frozen at 09:30. **{int(quality.complete_pm.sum())} complete and {int((~quality.complete_pm).sum())} unavailable PM windows** across 1,006 Development XNYS sessions. Every candidate has a complete PM window, exact level minimum and same-date availability; none uses partial/stale PML. A date-level audit lists all unavailable dates.

A root close breaks strictly below PML from above; its immediately adjacent complete candle closes strictly back above PML. That failure candle close is the entry timestamp. The inherited DOWN direction is deliberately evaluated as renewed downside, not the natural upward reclaim response. Independent causal replay exactly reproduces 407 event IDs; root/failure source OHLC, adjacency, availability and touch episodes all reconcile. No future candle defines membership.

Root touch episode counts: {{k:int(v) for k,v in raw_counts.items()}}. Each compound inherits the root episode exactly; it does not increment the touch count. The class has 407 distinct roots and event IDs, no duplicate mappings. Other classes may overlap these roots.

## Primary stop comparison

Entry = confirmed failure close minus one tick. A = sequence high + tick; B = failure high + tick; C = root break high + tick. One micro, .73/side.

{table(stops,['stop','execution_events','valid_executable_events','nonpositive_risk','no_post_entry_minutes','risk_points_q25','risk_points_median','risk_points_q75','risk_points_max','r1_before_stop_pct','atr1_before_stop_pct'])}

A invalidates the whole two-bar structure; B invalidates only the reclaim/failure candle; C can sit below the newly confirmed entry and has many nonpositive-risk cases. Those are explicit structural feasibility failures, not optimized exclusions. Stop C's valid count changes with slippage because executed risk changes, while the signal set is fixed.

## Horizon-specific races

These percentages use only the indicated complete horizon denominator. All raw causal signals remain in execution analysis; a session close is not a completed 30m/60m observation. Session-wide +1R rates above use all valid resolvable paths and therefore a different denominator.

{table(writeframe)}

## Excursion path and sequencing

{table(stops,['stop','mfe_points_mean','mfe_points_median','mae_points_mean','mae_points_median','mfe_atr_mean','mae_atr_mean','mfe_r_mean','mfe_r_median','mae_r_mean','mae_r_median','half_r_before_minus_half_r_pct','stop_before_half_r_pct'])}

Inclusive full stop-minute extrema inflate apparent excursion opportunity when high/low order is unknown. Favorable MFE can exceed MAE in the unrestricted stop-bounded path while the executable 1R races still fail frequently; a few long favorable paths cannot repair many early stops at a fixed target. See lower bounds, MAE-before-hit bounds and conflicts in the machine-readable sequence table.

{table(stops,['stop','r0p5_minutes_median','r1_minutes_median','minutes_to_stop_median','r0p5_mae_before_hit_lower_mean','r0p5_mae_before_hit_upper_mean','r1_mae_before_hit_lower_mean','r1_mae_before_hit_upper_mean','r1_conflict_count','atr1_conflict_count'])}

## Fixed-target diagnostics — primary actual costs

All are independent event simulations, not a daily-locked strategy or target optimization. Net values include 1.46 per completed micro and one adverse tick at entry and exit.

{table(fixed,['stop','target_r','valid_trades','wins','losses','win_pct','gross_usd','fees_usd','net_usd','pf','avg_net_r','max_closed_diagnostic_dd_usd','same_minute_conflicts'])}

## Yearly stability — every frozen stop and target

{table(years,['stop','target_r','year','events','valid_trades','unique_dates','win_pct','net_usd','pf','avg_net_r','max_closed_diagnostic_dd_usd','r1_before_stop_pct','atr1_before_stop_pct'])}

**2020 is negative in all nine primary diagnostics.** At the 1R target all four years lose for every stop. At 1.5R, 2022 alone is positive for each stop, so it supplies **100% of positive-year profit**, but the aggregate still loses. There is no acceptable multi-year executable payoff hidden behind the pooled directional observation.

{table(concentration,['stop','target_r','combined_net','net_2022','other_years_net','share_positive_year_profit_2022_pct','positive_years'])}

## Fee and slippage sensitivity

Fee: .25 commission + .35 exchange + .12 clearing + .01 NFA = **.73/side, 1.46 round trip**. Gross already includes slippage. No invented commission or market estimate.

{table(cost,['ticks','stop','target_r','valid_trades','gross_usd','fees_usd','net_usd','pf','avg_net_r'])}

The primary A/B diagnostics pay $586.92 in fees each; C pays $421.94. All 27 cost/stop/target combinations have negative net results. Fees worsen an already poor primary gross payoff rather than solely causing the loss.

## Episode and context description

{table(episodes,['stop','touch_group','execution_events','execution_dates','valid_executable_events','r1_before_stop_pct','atr1_before_stop_pct','mfe_r_mean','mae_r_mean'])}

Structure/ATR regime and reconstructed BOS/CHoCH summaries are in [structure_context.csv](structure_context.csv); continuous RTH-open/PML and known-lower-level room/ATR values are in [event_context_values.csv](event_context_values.csv). These are descriptions only. No subgroup changes entry eligibility or overrides the negative aggregate findings.

## Recommendation and caveats

**DIRECTIONAL_BUT_POOR_RISK_PATH. Controlled Development strategy backtest warranted: NO.** The directional measurement survives reconciliation but not the frozen mechanical execution translation. Sequence-high invalidation is defensible; its session-wide 1R-before-stop rate is below 50%, fixed-target payoffs are negative, every 1R year is negative, and the only positive 1.5R year is 2022. Root-high risk is invalid for many entries. No additional confirmation, stop, target or filter was searched.

The old significance finding does not disappear: it measures whether an unbounded 30-minute path reaches a threshold, not whether a target precedes a structural stop. Intraminute ambiguity is conservative and explicitly recorded. Repeated events, overlapping hypothetical trades, tiny-risk fee drag, selection from master research and differing horizon denominators limit inference. Diagnostic closed-trade drawdown is not investable portfolio drawdown.

## Verification and reproducibility

The source study/config and 1m/5m files are SHA-256 verified. The causal replay reproduces exact IDs, and every native fill is checked by an independent short-side calculation. The full run is repeated and output hashes must match; see [determinism_results.json](determinism_results.json), [reproducibility_manifest.json](reproducibility_manifest.json) and [verification_results.json](verification_results.json).

No production engine, saved strategy/run, database, market data or old artifact changed. Validation/OOS outcomes were not queried. No reveal, paid download, strategy creation, tuning or push occurred.

## Artifact guide

The requested 16 files plus full per-event path/target execution records, frozen protocol, horizon tables, context distances and 2022 concentration are in this directory. [methodology_and_caveats.md](methodology_and_caveats.md) gives denominator and execution contracts; [exact_raw_events.csv](exact_raw_events.csv) retains all 407 signals. Generated market-data derivatives remain ignored by Git; scripts/tests/documentation are committed locally.
"""
    (P / "PML_FAILED_BREAK_EXECUTION_FEASIBILITY.md").write_text(doc)
    engine_files = [
        "engine/partial_execution.py",
        "outputs/cont_a_backtest.py",
        "scripts/swing_low_feasibility/core.py",
        "engine/research/levels.py",
        "engine/research/events.py",
        "engine/research/sequences.py",
        "engine/research/structure.py",
    ]
    verification = json.loads((P / "execution_verification.json").read_text())
    manifest = dict(
        status="DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY",
        study_id=S.name,
        source_hashes=verification["source_hashes_verified"],
        production_code_hashes={f: sha(ROOT / f) for f in engine_files},
        audit_code_hashes={
            str(f.relative_to(ROOT)): sha(f)
            for f in sorted((ROOT / "scripts/pml_feasibility").glob("*.py"))
        },
        artifacts={
            f.name: dict(sha256=sha(f), bytes=f.stat().st_size)
            for f in sorted(P.iterdir())
            if f.is_file()
            and f.name
            not in ["reproducibility_manifest.json", "determinism_results.json"]
        },
        no_validation_outcomes_read=True,
        no_oos_reveal=True,
        no_push=True,
    )
    (P / "reproducibility_manifest.json").write_text(dumps(manifest))


if __name__ == "__main__":
    run()
