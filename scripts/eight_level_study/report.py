"""Readable complete report and self-contained filterable local study viewer."""

import sys, json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from scripts.eight_level_study.detect import P, LEVELS, write
from scripts.zone_reaction_backtest.report import table


def main():
    evidence = pd.read_csv(P / "primary_evidence.csv")
    points = pd.read_csv(P / "fixed_point_outcomes.csv")
    context = pd.read_csv(P / "context_comparisons.csv")
    freq = pd.read_csv(P / "entry_frequency.csv")
    coverage = pd.read_csv(P / "level_coverage.csv")
    quality = pd.read_csv(P / "data_quality.csv")
    pairs = pd.read_csv(P / "paired_entry_comparisons.csv")
    charts = pd.read_csv(P / "chart_audit.csv")
    recon = pd.read_csv(P / "source_reconciliation.csv")
    passed = evidence[
        (evidence.bh_q <= 0.05) & (evidence.effect > 0) & ~evidence.small_sample
    ]
    year = context[context.dimension == "year"]

    def shown(f):
        f = f.copy()
        for c in [
            "event_probability",
            "baseline_probability",
            "effect",
            "ci_low",
            "ci_high",
            "raw_event_hit_rate",
            "adverse_hit_rate",
        ]:
            if c in f:
                f[c] = f[c] * 100
        return f.to_dict("records")

    totals = (
        freq.groupby("level_type", sort=False)
        .agg(
            entry_observations=("events", "sum"),
            maximum_entry_dates=("unique_dates", "max"),
        )
        .reindex(LEVELS)
        .reset_index()
    )
    totals = totals.merge(
        coverage.groupby("level").available.sum().rename("available_dates"),
        left_on="level_type",
        right_index=True,
    )
    qa = json.loads((P / "quality_verification.json").read_text())
    text = [
        "# Eight-level reaction and entry-timing research — Development v1",
        "",
        "**DEVELOPMENT_RESEARCH_NOT_VALIDATED.** Fixed daily PDH/PDL, midnight PMH/PML, opening 5m and opening 15m highs/lows. Four reaction families, ten predefined entry definitions. All detection uses confirmed five-minute candles; all forward measurement uses subsequent one-minute data.",
        "",
        "## Executive findings",
        "",
        f"The complete study contains {int(freq.events.sum()):,} entry observations, not independent trades, across all eight level types. {len(passed)} of 160 registered 30-minute / favorable-50-point comparisons have a positive date-clustered difference with global BH q ≤ 0.05. These overlap heavily: they are not 29 independent edges, and no trade profit or optimal take-profit is established.",
        "",
        "The corrected results are concentrated in downward break entries: immediate break at all eight levels, first full candle at six, next close hold at six, and next full hold at six. Two upward rejection-close comparisons and one upward retest-close comparison also pass. None of the failed-break entry comparisons clears the registered correction. Failure to clear correction is not proof that a reaction never works.",
        "",
        "These are direction-specific crossings. For example, a DOWN break of PDH means price crosses PDH from above and closes below; it is not an upward breakout above PDH. “Direct” describes what was known at entry; later retests are retained, not removed with hindsight.",
        "",
        "There is no defensible universal best entry or take-profit from this study. Confirmation reduces opportunities and can miss moves; shared-root comparisons are selected subsets. A level reaction can have an elevated favorable-hit rate while suffering large adverse movement. Stops, costs and position ownership require a separate frozen execution-feasibility test.",
        "",
        "## Population and source coverage",
        "",
        table(totals.to_dict("records"), list(totals.columns)),
        "",
        "There are 1,006 XNYS Development dates. Available-date counts reflect complete source coverage; they are not tuned exclusions. All source event identities are preserved. The six old populations are reused, while O15 events are newly generated with the same causal event/sequence mechanics. No existing immutable study is overwritten.",
        "",
        table(
            recon.to_dict("records"),
            ["level", "source_events", "study_id", "reused_exactly"],
        ),
        "",
        "## What each entry means",
        "",
        "- BREAK_CLOSE: immediate confirmed close across the level, including later failures.",
        "- BREAK_FIRST_FULL: first entire candle beyond the level before a subsequent retouch; possibly the break candle itself.",
        "- BREAK_NEXT_CLOSE_HOLD / BREAK_NEXT_FULL_HOLD: adjacent next candle closes beyond / remains entirely beyond.",
        "- RETEST_CLOSE_HOLD: later distinct retest episode closes on the breakout side.",
        "- RETEST_RANGE_ESCAPE: confirmed close beyond the accumulated retest-contact range, without an invented large-body filter.",
        "- REJECTION_CLOSE / REJECTION_CONFIRMATION: frozen rejection close / adjacent close beyond its directional extreme.",
        "- FAILED_BREAK_CLOSE / FAILED_BREAK_CONFIRMATION: adjacent return across the broken level / next close beyond the failure candle extreme, measured opposite the original break.",
        "",
        "## Primary evidence: immediate downward breaks",
        "",
        "Probabilities and intervals below are percentage points on an equal-NY-date basis. Raw event-weighted hit counts/rates remain in the outcome tables and viewer. These should not be interchanged.",
        "",
        table(
            shown(
                evidence[
                    (evidence.entry_kind == "BREAK_CLOSE")
                    & (evidence.direction == "DOWN")
                ]
            ),
            [
                "level_type",
                "events",
                "matched_dates",
                "event_probability",
                "baseline_probability",
                "effect",
                "ci_low",
                "ci_high",
                "bh_q",
                "positive_years",
            ],
        ),
        "",
        "## Other corrected associations",
        "",
        table(
            shown(passed[~passed.entry_kind.str.startswith("BREAK")]),
            [
                "level_type",
                "entry_kind",
                "direction",
                "events",
                "matched_dates",
                "event_probability",
                "baseline_probability",
                "effect",
                "ci_low",
                "ci_high",
                "bh_q",
                "positive_years",
            ],
        ),
        "",
        "## Each level: all primary entry comparisons",
        "",
    ]
    for level in LEVELS:
        text += [
            f"### {level}",
            "",
            table(
                shown(evidence[evidence.level_type == level]),
                [
                    "entry_kind",
                    "direction",
                    "events",
                    "matched_dates",
                    "event_probability",
                    "baseline_probability",
                    "effect",
                    "bh_q",
                    "positive_years",
                    "mean_mfe",
                    "mean_mae",
                ],
            ),
            "",
        ]
    text += [
        "## Yearly stability",
        "",
        "All four years for every candidate are in context_comparisons.csv and the viewer. Positive-year counts alone do not prove equality across years or execution profitability. The following shows the predeclared immediate-break DOWN reference for every level/year.",
        "",
        table(
            shown(
                year[(year.entry_kind == "BREAK_CLOSE") & (year.direction == "DOWN")]
            ),
            [
                "level_type",
                "value",
                "events",
                "complete",
                "matched_dates",
                "event_probability",
                "baseline_probability",
                "effect",
                "mean_mfe",
                "mean_mae",
            ],
        ),
        "",
        "## Distances, timing and adverse path",
        "",
        "The viewer and fixed_point_outcomes.csv include every candidate at 5, 10, 15, 30, 60 minutes and actual session close, with 10/25/50/75/100/150/200-point thresholds. ATR-normalized 0.5/1/1.5/2 thresholds are secondary. There is no search for an optimal threshold.",
        "",
        "A high/low touch of a distance does not imply realizable profit: both favorable and adverse thresholds may be reached, and the ordering inside one minute is unknown. Adverse excursion through the first favorable hit conservatively includes that entire minute. Median time is conditional on reaching the threshold; non-hits are not zero-minute hits.",
        "",
        "## Entry coverage and paired comparisons",
        "",
        "entry_frequency.csv supplies all raw event counts, distinct roots/dates, available level dates and eligible root denominators. Repeated retests can generate several entry observations for one break; root coverage and event counts are separate. Root opportunities for break/retest/failure are all matching-direction breaks; rejection uses matching-approach TOUCH observations.",
        "",
        "paired_entry_comparisons.csv uses the earliest available candidate per root and direction. It reports confirmation delay, common-root hit rates, and early 50-point opportunities without a later entry. Because common-root membership is selected by the later signal, this is a diagnostic comparison, not a causal ranking or a new entry eligibility filter.",
        "",
        "## Censoring and limitations",
        "",
        table(
            quality.to_dict("records"),
            [
                "horizon",
                "raw_events",
                "complete",
                "censored",
                "atr_unavailable_complete",
                "censor_reasons",
            ],
        ),
        "",
        "Future horizon completeness never affects causal event membership. A session-close observation is not a completed 30-minute observation. Missing ATR stays eligible for point measurements; ATR-normalized values remain unavailable. No source minute is fabricated.",
        "",
        "The event detector’s rejection is the first candle of a touching episode with a close at least one tick back on the approach side. A failed break is the immediately next candle, not an arbitrary failure hours later. Retest-range escape is the explicitly frozen range mechanic; none of these claims to enumerate every discretionary visual pattern.",
        "The matched pool controls year, confirmation half-hour and causal ATR bucket, not every trend or regime feature. Bootstrap intervals condition on this empirical pool. Date clustering addresses repeated observations within dates but is not a guarantee against serial dependence across days. Development has been inspected in previous projects. All nonprimary distances, horizons, yearly and contextual splits are exploratory.",
        "",
        "## Integrity and reproducibility",
        "",
        f"Verified {qa['entry_records']:,} unique causal entries, {qa['exact_source_ohlc_checks']:,} exact source OHLC checks, all {qa['opening15_dates_checked_against_1m']} available opening-15m dates against actual one-minute extrema, and {qa['charts']} deterministic chart examples. Source hashes and prior artifacts are unchanged.",
        "Reproduction scripts are under scripts/eight_level_study. Full, unsampled source/entry observations and outcomes are retained in Parquet. Aggregate CSV/JSON, the protocol, report, viewer and audit charts are included in the bundle; the evidence manifest links full raw files by hash. Validation/OOS outcomes were not accessed; no paid downloads, strategy optimization or production execution changes occurred.",
        "",
        "## What this supports next",
        "",
        "Review exact chart examples and candidate-specific adverse paths first. The downward-break associations merit review as research observations, but this task does not select a final strategy, entry or target. Any later execution test needs frozen risk/exit/cost rules and must retain unsuccessful breaks and missed confirmations.",
        "",
    ]
    (P / "EIGHT_LEVEL_RESEARCH_REPORT.md").write_text("\n".join(text))
    data = dict(
        evidence=json.loads(evidence.to_json(orient="records")),
        points=json.loads(points.to_json(orient="records")),
        year=json.loads(year.to_json(orient="records")),
        frequency=json.loads(freq.to_json(orient="records")),
        pairs=json.loads(pairs.to_json(orient="records")),
        charts=json.loads(charts.to_json(orient="records")),
    )
    js = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    template = (ROOT / "scripts/eight_level_study/viewer.html").read_text()
    (P / "study.html").write_text(template.replace("/*STUDY_DATA*/", js))
    summary = dict(
        status="DEVELOPMENT_RESEARCH_NOT_VALIDATED",
        entry_records=int(freq.events.sum()),
        levels=8,
        entry_definitions=10,
        primary_family=160,
        positive_corrected_cells=len(passed),
        corrected_by_entry={
            k: int(v) for k, v in passed.groupby("entry_kind").size().items()
        },
        quality=qa,
    )
    (P / "study_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    print(summary, flush=True)


if __name__ == "__main__":
    main()
