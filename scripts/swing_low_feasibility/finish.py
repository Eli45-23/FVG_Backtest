"""Assemble the reviewed Development-only feasibility report without selecting a strategy."""

from pathlib import Path
import json, sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.canonical import dumps
from report import P, M, sha, table, write


def finish():
    raw = pd.read_csv(P / "exact_touch_events.csv")
    paths = pd.read_csv(P / "all_event_paths.csv", low_memory=False)
    alltrades = pd.read_csv(P / "all_target_executions.csv", low_memory=False)
    m = pd.read_csv(P / "entry_stop_matrix.csv")
    primary = m[m.ticks == 1]
    targets = pd.read_csv(P / "target_diagnostics.csv")
    tp = targets[targets.ticks == 1]
    years = pd.read_csv(P / "yearly_stability.csv")
    yp = years[years.ticks == 1]
    touch = pd.read_csv(P / "touch_number_analysis.csv")
    context = pd.read_csv(P / "structure_context.csv")
    assert (tp.net_pnl_usd < 0).all() and (tp.net_pf < 1).all()
    assert (yp.diagnostic_1r_net_pnl_usd < 0).all()
    assert (targets[targets.target_r == 1].net_pnl_usd < 0).all()
    names = {"A": "RAW TOUCH CLOSE", "B": "REJECTION CLOSE", "C": "SWEEP_RECLAIM CLOSE"}
    decisions = [
        {
            "entry": k,
            "name": name,
            "classification": (
                "DIRECTIONAL_BUT_POOR_RISK_PATH" if k == "A" else "NOT_PLAUSIBLE"
            ),
            "reason": (
                "Published upward-hit association does not translate to positive fee-corrected fixed-bracket diagnostics."
                if k == "A"
                else "Both frozen stops fail the actual-fee primary diagnostics in every Development year; even zero-slippage 1R is net negative."
            ),
        }
        for k, name in names.items()
    ]
    rec = {
        "status": "DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY",
        "candidate_status": "DEVELOPMENT_MEASUREMENT_CANDIDATE_NOT_VALIDATED",
        "recommendation": "NO_EXECUTABLE_SWING_LOW_STRATEGY_CANDIDATE",
        "entries": decisions,
        "recommended_entry": None,
        "recommended_stop": None,
        "recommended_target": None,
        "population": {
            "raw_events": 5319,
            "raw_dates": 1006,
            "historical_measurement_events": 4816,
            "historical_measurement_dates": 1004,
        },
        "scope": "Only the specified Entry A/B/C, Stop A/B, targets .5/1/1.5R and costs 0/1/2 ticks; no universal claim about all swing-low ideas.",
        "next_action": "Do not create a strategy or spend Validation/OOS on these frozen definitions. Review this audit; any new hypothesis requires separate preregistration.",
        "validation_or_oos_queried": False,
        "production_code_modified": False,
    }
    (P / "recommendation.json").write_text(dumps(rec))
    e = pd.read_parquet(M / "08_5M_SWING_LOW/outcomes_30.parquet")
    missing = e[
        (e.interaction_type == "TOUCH")
        & (e.direction == "DOWN")
        & (e.censor_reason == "MISSING_MINUTES")
    ]
    assert len(missing) == 1
    missing_id = missing.iloc[0].event_id
    mt = alltrades[alltrades.event_id == missing_id]
    assert len(mt) == 18 and mt.execution_status.eq("COMPLETED").all()
    assert mt.exit_reason.eq("STOP").all()
    missing_at = pd.to_datetime(
        paths.loc[(paths.event_id == missing_id), "first_missing_minute"], utc=True
    ).iloc[0]
    assert (pd.to_datetime(mt.exit_time_utc, utc=True) < missing_at).all()
    write("missing_minute_ownership_audit.csv", mt)
    unavailable = int(alltrades.execution_status.eq("EXECUTION_DATA_UNAVAILABLE").sum())
    assert unavailable == 0
    # Overlap across gates explicitly retained, not added as disjoint exclusions.
    sets = {
        "SESSION_BOUNDARY": set(e.loc[e.censor_reason == "OUTSIDE_SESSION", "event_id"])
        & set(raw.event_id),
        "MISSING_MINUTES": set(missing.event_id),
        "ATR_UNAVAILABLE": set(raw.loc[raw.atr14.isna(), "event_id"]),
    }
    census = []
    for name, ids in sets.items():
        census.append(
            {
                "category": name,
                "events": len(ids),
                "overlap_with_session_boundary": len(ids & sets["SESSION_BOUNDARY"]),
                "overlap_with_missing_minutes": len(ids & sets["MISSING_MINUTES"]),
                "overlap_with_atr_unavailable": len(ids & sets["ATR_UNAVAILABLE"]),
            }
        )
    write("censoring_reconciliation.csv", census)
    atrtrades = alltrades[alltrades.event_id.isin(sets["ATR_UNAVAILABLE"])]
    write("atr_unavailable_execution_audit.csv", atrtrades)
    assert atrtrades[atrtrades.execution_status == "COMPLETED"].shape[0] > 0
    # Amend the prior stopped report's semantics gate; preserve its archived original.
    sem = pd.read_csv(
        P / "preflight_before_population_amendment/event_semantics_audit.csv"
    )
    sem.loc[sem.topic == "gate", "frozen_semantics"] = (
        "User-authorized raw population: 5319/1006; historical 4816/1004 retained only as measurement reference. No future completeness/ATR label eligibility gate."
    )
    write("event_semantics_audit.csv", sem)

    def scaled(f, cols):
        return table(f, cols)

    yearnet = yp.pivot(
        index=["entry", "stop"], columns="year", values="diagnostic_1r_net_pnl_usd"
    ).reset_index()
    yearnet.columns = [str(x) for x in yearnet.columns]
    atc = raw[raw.entry_at_session_close]
    limitations = """# Methodology and caveats

Status: DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY / DEVELOPMENT_MEASUREMENT_CANDIDATE_NOT_VALIDATED.

## Population and causality

All 5,319 raw causal TOUCH/DOWN events on 1,006 NY dates remain in the entry analysis. The 4,816/1,004 historical measurement subset is never an execution eligibility filter. Rejection and sweep subsets join by exact observation ID and identical event timestamp. They overlap; their totals must not be added together. All event IDs are unique within the raw population. Entry subsets and stops use only information confirmed by the entry instant.

The approved three entry definitions are A raw touch close, B frozen REJECTION overlap, C frozen SWEEP_RECLAIM overlap. The only stops are A confirmed level minus one tick and B event low minus one tick, rounded outward. No time, weekday, EMA, VWAP, ATR, structure or touch-number filter was added. A signal-candle penetration of the future stop is recorded but never invalidates a post-close entry.

Five events lack ATR and remain in structural/R-based execution. Their ATR-normalized values are null. The historical 30-minute censor categories are disjoint: 497 session-boundary, one missing-minute, then five complete observations without ATR; 5,319−497−1−5=4,816. Annual execution starts from all raw events, not these measured rows.

## Ownership, censoring and fills

Minute timestamps are bar starts. Ownership begins with the minute starting at the confirmed event close. The already completed signal candle is excluded. All actual XNYS session closes, including early closes, come from the saved study calendar. No unowned minutes are synthesized. Signals confirmed exactly at session close remain in the population but have NO_POST_ENTRY_SESSION_MINUTES; there is no fabricated immediate round trip or overnight ownership. If also nonpositive risk, NON_POSITIVE_RISK takes precedence in mutually exclusive execution-status tables, while the raw-at-close count is reported independently.

The production `engine.partial_execution.execute` performs every valid fixed-target diagnostic, using no management, one micro, $2/point and original executed risk. Long entry adds adverse ticks; stop/target/session exit subtract adverse ticks. Stop gaps fill at the worse of stop and minute open. Stop wins simultaneous stop/target touches. Targets use existing nearest-tick rounding. Zero/one/two adverse ticks each side and the supplied $0.73/side fee are the only cost cases. Stop-A risk validity can differ across slippage cases because executed entry changes; source event membership never changes.

Every native fill is independently checked using numerical OHLC arrays. A required missing minute raises an error and would be reported as EXECUTION_DATA_UNAVAILABLE, without retroactively rejecting the source signal. No completed fill may cross an unknown owned minute. The observed missing-minute event exits before the gap in every specified diagnostic; consequently no actual diagnostic is execution-data-unavailable.

15/30/60-minute descriptive metrics require the entire horizon to be present within the session. Their complete/censored denominators are distinct from execution eligibility, and are cross-checked against the original horizon artifacts for every valid event. Session-close exits do not complete a longer research horizon. Risk and raw-signal columns make each stage visible. Probabilities use the stated event denominator, not equal date weights; this differs intentionally from the original equal-date-weighted matched-baseline evidence. No new p-values or significance claims are attached to these overlapping trade diagnostics.

## Excursion interpretation

Primary path measurements stop at the first structural stop or actual session close, with no fixed target; target-specific records use the earlier native target exit. This differs from the master report's unrestricted 30-minute excursions. Never interpret these conditional excursions as reproducing the same MFE/MAE statistic.

As in the validated engine, MFE/MAE include the exit minute's full extremes. On stop exits those are upper bounds on movement while owned; prior complete minutes supply lower bounds in separate columns. An exit-minute high may occur after the stop. Small risk magnifies both R excursions and costs. Positive mean MFE/R alone is not evidence of capturable profit. For MAE before first +0.5R/+1R, prior-minute extrema give the lower bound and including the hit minute gives the upper bound; the low/high order is marked ambiguous. Adverse-first ordering governs same-minute +0.5R/−0.5R races. Threshold races end at the stop; stopped events cannot count later favorable moves.

## Economic interpretation

Every event is evaluated independently. Trades overlap in time, share dates and may share price paths. There is no daily lock, capital allocation or single-position sequencing in this feasibility audit. Summed diagnostic P&L and PF are not the return of an implementable portfolio, and events are not independent statistical evidence. A subsequent controlled strategy would need separately frozen selection and portfolio rules. No candidate is recommended here.

Year/touch/structure splits are descriptive and never eligibility conditions. Structure progression is reconstructed for the exact interacted swing, including HL/LL/EL/unclassified. Previously-broken status is captured before processing the touch candle, not inferred from its close-context flag. No sampled observations were substituted for full execution.

The user-supplied observed fee schedule is applied uniformly through history; it is not a claim about Webull's historical fee schedule in each year. No bid/ask or tick-event ordering data is available. Conclusions apply to these frozen entries/stops/targets/costs only, not every possible swing-low strategy.

Only Development bars, immutable Development study artifacts and source-file hashes were accessed. No Validation or OOS outcomes were queried or revealed. No production strategy/execution code, source market data or existing study was altered; no paid data was downloaded. The earlier population-gate report remains archived locally. Nothing was pushed.
"""
    (P / "methodology_and_caveats.md").write_text(limitations)
    report = f"""# Five-minute swing-low execution feasibility

**NO_EXECUTABLE_SWING_LOW_STRATEGY_CANDIDATE** under the frozen protocol.

Status: **DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY**. No strategy was registered, optimized or validated. The upward-response observation does not survive these mechanically executable entries/stops and actual fees: all 18 primary Entry × Stop × Target diagnostics have negative net P&L, and all six 1R combinations are negative in each Development year. Zero-slippage 1R remains negative after fees for every combination.

## Population and historical reference

Raw causal population: **5,319 events / 1,006 dates**. Historical 30m-complete count: **4,821**. Historical complete+ATR reference: **4,816 / 1,004 dates**. Exactly **497** session-boundary censored, **one** missing-minute outcome, and **five** complete outcomes without ATR account for the difference; these sets are disjoint. None is an entry filter.

The separately reproduced historical evidence remains 55.903% versus 52.062%, +3.841 percentage points, 95% interval [+2.315,+5.512], BH q=0.009595 over the original family. It is a matched forward-hit association, not a stop-before-target result or trading win rate.

The original immutable source is Event Study `5cb7fab0d4e7414792a3fbe59ded4999`, Development NY dates [2020-01-01,2024-01-01), dataset `research_2020_2026`. The archived preflight retains the exact 4,816-event historical measurement extract. Current `exact_touch_events.csv` contains all 5,319 raw events.

## Frozen event semantics

A strict five-minute low is lower than both preceding and both following candle lows. Its formation timestamp is the pivot start; availability is the second right candle close. Only the latest confirmed swing low is exposed. TOUCH/DOWN means entry into a touching episode approached from ABOVE, measured from prior adjacent close or current open after discontinuity. Confirmation is touch-candle close. TOUCH does not require closing above the level; it can overlap break, rejection and sweep labels. Previously broken levels remain eligible until replaced. There are no duplicate raw event/observation IDs.

Low progression can be HL, LL, EL or unclassified; HH/LH describe swing highs. All metadata is descriptive. Replayed swing IDs, prices and availability matched every raw event. **{int(raw.already_broken_before_touch.sum())}** touch events involved swings already broken before the event candle, without being excluded.

## Raw candle and overlap breakdown

{table(pd.read_csv(P/'touch_close_classification.csv'))}

Close ABOVE/AT/BELOW are a partition. Wick-only means both body edges above the level and the low touching/crossing it; it overlaps penetration/reclaim and is not added to those categories. Exact-level touch means low equals the level. B is the exact frozen REJECTION overlap (penetration >=0, close back on approach side by >=0.25); C is strict penetration with close back on the approach side. C is nested in B. No new threshold was introduced.

## Primary entry/stop comparison

Primary costs: **one adverse tick each side, $0.73/side ($1.46 round trip), one MNQ micro**. Entry A=raw touch, B=rejection, C=sweep/reclaim. Stop A=swing low−0.25; Stop B=event low−0.25.

{scaled(primary,['entry','stop','execution_denominator','execution_dates','valid_positive_risk_with_session_minutes','nonpositive_risk','no_post_entry_minutes','r1_before_stop_pct','atr1_before_stop_pct','diagnostic_1r_net_pnl_usd','diagnostic_1r_net_pf','diagnostic_1r_net_avg_r'])}

All raw events remain accounted for. There are **77** confirmations exactly at session close; these have no owned minute and no invented fill. For raw Entry A/Stop A, the nonpositive-risk status may overlap that raw boundary count; exclusive table statuses prioritize nonpositive risk. Session-close events are exported separately.

## Structural risk distribution

{scaled(primary,['entry','stop','mean_risk_points','median_risk_points','risk_points_q25','risk_points_q75','risk_points_max','mean_risk_usd','mean_risk_atr','median_risk_atr','risk_atr_denominator'])}

`risk_atr_distribution.csv` provides the fixed broad buckets, with unavailable ATR separate. No threshold was used as an eligibility filter. Risk-mean denominators count valid positive-risk events with an owned session interval, not the full raw source population.

## Stop timing and censoring

{scaled(primary,['entry','stop','execution_denominator','raw_15m_complete','raw_15m_censored','valid_15m_complete','stop_hit_15m_pct','valid_30m_complete','valid_30m_censored','stop_hit_30m_pct','valid_60m_complete','valid_60m_censored','stop_hit_60m_pct'])}

Each stop-hit percentage uses its complete valid-event horizon denominator. The complete matrix also gives raw 30m/60m denominators. In contrast, actual fixed-target trades remain active until stop/target/session close. Censored fixed-duration labels never remove a signal or prevent a session-close fill.

Missing-minute case: event `{missing_id}` confirms at 12:40 ET on 2020-03-18. All 18 specified Stop × Cost × Target diagnostics stop at **12:42 ET**, before the absent **12:58 ET** source minute. There are **{unavailable} EXECUTION_DATA_UNAVAILABLE target diagnostics**. The owned-minute audit is exported; other missing minutes later in some sessions likewise occur after these positions have exited.

## Favorable thresholds before stop

{scaled(primary,['entry','stop','r0p5_before_stop_pct','r1_before_stop_pct','r1p25_before_stop_pct','r1p5_before_stop_pct','r2_before_stop_pct','atr0p5_before_stop_pct','atr1_before_stop_pct','atr1p5_before_stop_pct','r1_before_stop_denominator','atr1_before_stop_denominator'])}

Thresholds are measured to actual session close and stop-first within ambiguous minutes. These are threshold-before-stop rates, not fixed-target net win rates; a positive session-close exit can be a net winner without hitting 1R. ATR-unavailable events remain in R denominators.

## Excursion path and sequencing

{scaled(primary,['entry','stop','mean_mfe_points','median_mfe_points','mean_mae_points','median_mae_points','mean_mfe_atr','mean_mae_atr','mean_mfe_r','median_mfe_r','mean_mae_r','median_mae_r'])}

{scaled(primary,['entry','stop','mean_mfe_points_lower_bound','mean_mae_points_lower_bound','half_r_before_minus_half_r_pct','stop_before_half_r_pct','median_r0p5_minutes','median_r1_minutes','median_minutes_to_stop','median_r0p5_mae_before_hit_lower','median_r0p5_mae_before_hit_upper','median_r1_mae_before_hit_lower','median_r1_mae_before_hit_upper'])}

All mean/median points, ATR and R fields are retained in `excursion_sequence_analysis.csv`; hit-time/MAE-before-hit denominators include only qualifying hits. The exit-minute extrema convention yields upper bounds when intraminute order is unknown. This especially inflates ratios with tiny structural risk: a high may occur after the stop. The original unrestricted 30-minute finding (mean adverse excursion greater than mean favorable) and this stop-bounded diagnostic use different observation windows. Neither a large mean MFE/R nor that change of window repairs the negative executable payoff.

## Predeclared fixed targets — primary cost

{scaled(tp,['entry','stop','target_r','completed_trades','win_pct','gross_pnl_usd','fees_usd','net_pnl_usd','net_pf','net_avg_r','session_close_exits','same_minute_conflicts'])}

No target is selected from these results. All targets were specified beforehand. Fees and conservative ordering matter; gross P&L is already negative for every primary combination. There is no management or position sizing adaptation.

## Yearly stability

Net 1R diagnostic dollars by year; every year uses raw causal eligibility:

{table(yearnet)}

{scaled(yp,['entry','stop','year','execution_denominator','valid_positive_risk_with_session_minutes','execution_dates','r1_before_stop_pct','atr1_before_stop_pct','mean_mfe_r','mean_mae_r','diagnostic_1r_net_pf','diagnostic_1r_net_avg_r'])}

No year was dropped. The negative result is not confined to one year. The CSV contains all three cost scenarios and their full denominators.

## First, second and third-plus episodes

{scaled(touch[(touch.ticks==1)&(touch.stop=='B')],['entry','value','execution_denominator','execution_dates','valid_positive_risk_with_session_minutes','r1_before_stop_pct','diagnostic_1r_net_pnl_usd','diagnostic_1r_net_pf'])}

This table displays the event-candle stop for readability; both stops/all costs are in `touch_number_analysis.csv`. Only 18 raw third-plus events exist. Sparse later-touch results cannot justify a new filter.

## Structure description

{scaled(context[(context.ticks==1)&(context.stop=='B')&(context.entry=='A')],['dimension','value','execution_denominator','execution_dates','r1_before_stop_pct','diagnostic_1r_net_pnl_usd','diagnostic_1r_net_pf'])}

Displayed slice is raw touch/event-candle stop. Every Entry × Stop × Cost context combination is exported. Already-broken status is reconstructed BEFORE the event candle; the event-close snapshot was not substituted. No context selected or removed a trade.

## Actual-fee sensitivity at 1R

{scaled(targets[targets.target_r==1],['entry','stop','ticks','completed_trades','gross_pnl_usd','fees_usd','net_pnl_usd','net_pf','net_avg_r'])}

$0.73/side consists of $0.25 commission + $0.35 exchange + $0.12 clearing + $0.01 NFA, as supplied by the user. Source signal counts never change. Raw Stop-A positivity can change when adverse entry slippage changes executed entry and risk; the immutable signal population is unchanged. Zero slippage with actual fees is still negative in all six 1R cases.

## Candidate classification and recommendation

{table(pd.DataFrame(decisions))}

**NO_EXECUTABLE_SWING_LOW_STRATEGY_CANDIDATE.** Samples are large and span many dates, but the required payoff/path/cost conditions fail. Rejection/reclaim with the event-candle stop reduces stop-first failures relative to the swing stop, yet primary +1R-before-stop remains below 48%, and its fee-corrected 1R diagnostics are negative in each year. No strategy, stop/target winner, touch filter or Validation run is recommended. This conclusion applies to the frozen audit, not every possible use of swing lows.

## Verification and preservation

The audit runs the unchanged native executor and independently verifies **70,962 valid fixed-bracket diagnostics** across all costs/stops/targets, with overlapping B/C reusing identical executions rather than duplicating fills. There are **31,914 event-path rows** and **95,742 target-status rows**, including nonpositive-risk and session-close nonexecution records. Every valid 15/30/60-minute completeness flag matches the original immutable horizon artifact. Synthetic tests cover stop-first conflicts, missing owned minutes, ATR-null handling, post-confirmation ownership, adverse gaps, session close, MAE ordering bounds and horizon denominators. Deterministic rerun evidence is recorded in `determinism.json`.

All source data/study identities remain unchanged. No production code or saved Lab strategy/run was changed. The original blocked preflight is archived under `preflight_before_population_amendment/`. Validation/OOS were not queried or revealed, no paid data was downloaded, and nothing was pushed. Full caveats: `methodology_and_caveats.md`.
"""
    (P / "SWING_LOW_EXECUTION_FEASIBILITY.md").write_text(report)
    old = json.loads(
        (
            P / "preflight_before_population_amendment/reproducibility_manifest.json"
        ).read_text()
    )
    for path, h in old["source_hashes_verified"].items():
        assert sha(ROOT / path) == h
    manifest = {
        "source_hashes_verified": old["source_hashes_verified"],
        "status": "DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY",
        "analysis_sources": {
            str(p.relative_to(ROOT)): sha(p)
            for p in sorted((ROOT / "scripts/swing_low_feasibility").glob("*.py"))
        },
        "production_engine_sources": {
            str(p.relative_to(ROOT)): sha(p)
            for p in [
                ROOT / "engine/partial_execution.py",
                ROOT / "outputs/cont_a_backtest.py",
            ]
        },
        "artifacts": {
            p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
            for p in sorted(P.iterdir())
            if p.is_file()
            and p.name not in ["reproducibility_manifest.json", "determinism.json"]
        },
        "no_validation_oos_access": True,
        "no_paid_download": True,
        "no_production_changes": True,
    }
    (P / "reproducibility_manifest.json").write_text(dumps(manifest))
    print("Complete report:", P / "SWING_LOW_EXECUTION_FEASIBILITY.md")


if __name__ == "__main__":
    finish()
