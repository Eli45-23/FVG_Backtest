# Same-day MNQ FVG lifecycle layer

## Reproduce

```sh
work/.venv/bin/python outputs/fvg_lifecycle.py
work/.venv/bin/python outputs/lifecycle_report.py
work/.venv/bin/python -m unittest discover -s outputs/tests -v
```

No network access or credentials are needed. The two validated source Parquet files are read only. The full FVG definition is revalidated against the five-minute bars before building one lifecycle row per FVG. File SHA-256 checks verify source immutability; derived Parquet is written atomically and checked by readback. The CLI takes an explicit exclusive provider coverage endpoint, default `2026-10-06T00:00:00Z`; it never infers full-day coverage merely from the last observed trade bar.

Output data stays under ignored `outputs/data/`:

- `MNQ_FVG_LIFECYCLE_2024-01-01_2026-10-06.parquet`
- `MNQ_FVG_LIFECYCLE_sample.csv` (20 records only)
- `MNQ_FVG_LIFECYCLE_validation.json` (complete descriptive statistics and checks)

Readable summaries are in [LIFECYCLE_RESEARCH.md](LIFECYCLE_RESEARCH.md). Source files are `fvg_lifecycle.py`, `lifecycle_stats.py`, `lifecycle_report.py`, and `tests/test_fvg_lifecycle.py`. This is lifecycle/research data, with no trading strategy, order, position, stop, target, management, P&L or backtest simulation.

## Accepted interpretation and observation policy

The user explicitly selected full-day descriptive event history with **separate close- and wick-based terminal states**, and conservative handling of missing/incomplete bars.

- Formation time is Candle 3's **start**. Observable time is start + 5 minutes. Candle 3 never participates in touch, fill, invalidation, untouched-distance or MFE calculations.
- Later complete bars may be evaluated only on the formation's New York calendar date. All full-session bars are eligible, including after 16:00; there is no 11:00 entry cutoff or RTH-only lifecycle filter.
- Event `*_time` fields use **bar-start UTC**, not an invented intrabar instant. Parallel NY fields retain America/New_York. `*_confirmed_at_utc` is start + 5 minutes: OHLC-based events can only be known from the completed bar.
- Touch uses inclusive overlap of the candle range and zone. Bullish full fill is low <= bottom; bearish full fill is high >= top. Full fill alone does not invalidate.
- Close and wick invalidations use the requested strict inequalities. Their first events are retained independently, and later descriptive events still remain in the record. A jump through the entire zone can fill/invalidate without overlapping: `gap_through_without_overlap` flags that fact. The engine does not synthesize a path between candles.
- Incomplete bars are skipped and counted. The exact first and second post-formation slots are +5/+10 minutes from Candle 3 start; a missing/incomplete slot is null, never replaced by a later bar.
- Empty clock buckets are counted but not filled. These include scheduled maintenance/weekend/holiday closures and possible data gaps; OHLCV alone does not distinguish the causes. No exchange-calendar assumptions are introduced.
- NY expiration is the next calendar midnight, respecting daylight-saving offsets. The midnight instant is a boundary marking the end of the previous date, never permission to evaluate a next-date candle.
- The final source date stops at 20:00 ET. Its 18 FVGs are censored, not marked expired or declared never touched for the whole date. Positive events actually observed remain recorded.
- A further 41 records have a skipped incomplete post-formation bar. They are retained and flagged but excluded, along with censored records, from qualified full-day research aggregates. This leaves 10,549 research-eligible records from 10,608 total.

The absence of recorded touch means no overlap in the available complete candles; it does not certify tick-level completeness during entirely empty intervals. The known source limitations are retained rather than silently repaired.

## State and expiration fields

All original FVG columns and IDs are preserved. Boolean descriptive properties include `untouched`, `touched`, `fully_filled`, `close_invalidated`, and `wick_invalidated`. First event times remain available after later events occur.

`close_terminal_state` and `wick_terminal_state` each use:

- `invalidated` when that method has an observed invalidation, with terminal time at that invalidation bar's close;
- otherwise `expired_same_day` when the NY date is fully covered;
- otherwise the current observed `fully_filled`, `touched`, or `untouched` state on a censored history.

Both methods have separate `*_expired_same_day`, `*_expired_untouched`, `*_expired_after_touch`, and `*_terminal_time_utc` fields. `calendar_expiration_boundary_ny` is always recorded, including censored histories, as a scheduled boundary rather than an observed outcome.

For compatibility, the shared `expired_same_day` alias is true only when **both** methods expire (neither has invalidated). Its `expired_untouched`, `expired_after_touch`, and `expiration_time_ny` fields follow that shared alias. These do not replace or privilege either method-specific state. Quality-flagged records describe outcomes on observed complete bars; their hypothetical missing-bar outcomes are unknown and are excluded from qualified research statistics.

## Untouched movement and time

The entire first-touch candle is excluded from before-touch extremes, because OHLC does not establish whether its high/low occurred before or after the touch. Only earlier post-Candle-3 complete bars contribute.

Bullish fields are `highest_high_before_touch` and `highest_close_before_touch`; bearish fields are `lowest_low_before_touch` and `lowest_close_before_touch`. The other direction's fields are null. `maximum_points_away_before_touch` is max(0, high minus zone top) for bullish and max(0, zone bottom minus low) for bearish. No prior untouched observation gives zero distance and null directional extremes.

`bars_until_first_touch` is the clock-slot distance from Candle 3 start: next candle = 1, including missing slots in the distance. `bars_untouched` counts complete observed candles before touch; `minutes_untouched = 5 * bars_untouched` counts observed bar minutes, excluding scheduled closures/missing intervals. Separate `elapsed_minutes_until_touch_or_horizon` measures wall-clock time from observability to first-touch bar start or the observation boundary. These quantities intentionally differ across gaps.

## First and second post-formation bars

`next_*` and `second_*` contain exact-slot UTC/NY starts, OHLC, bullish/bearish/doji candle direction, inclusive zone touch, strict above/below/outside-zone tests, and favorable-side classification.

Reference breakout fields `*_closed_above_reference_high` and `*_closed_below_reference_low` compare the next candle against Candle 3 and the second candle against the first post-FVG candle. `*_closed_beyond_reference_favorable` / `adverse` mirror by FVG direction. If a reference slot is absent, these classifications are null rather than inferred from another candle. `second_bar_start` is an alias of the UTC start.

`first_two_bars_untouched` requires both slots to exist, be complete and have no overlap. `second_candle_research_trigger` adds the strict favorable reference-close comparison. This is a descriptive flag, never an entry. There is no extra invalidation filter: both invalidation alternatives remain available for later research.

## Pause research and MFE

Two definitions are retained independently: `no_new_extreme` and `opposite_close`. Their fields include `*_pause_time`, `*_pause_time_ny`, `*_pre_pause_extreme`, `*_trigger_time`, `*_trigger_time_ny`, `*_trigger_close`, and `*_mfe_points`.

Pause comparisons require adjacent complete five-minute candles; no pause comparison bridges a missing or incomplete interval. The first post-FVG candle may compare to Candle 3 as its **reference**, matching the requested current-versus-previous comparison. This does not evaluate Candle 3 as a lifecycle observation.

The pre-pause threshold is the running favorable extreme strictly **before** that pause, seeded with Candle 3's high/low as the prior reference and extended by earlier untouched post-formation bars. This explicit seed allows a pause on the first post-FVG bar to have a usable reference. It never seeds the separate untouched-distance measure. Only the first pause of each kind is retained; its threshold is frozen.

A research occurrence is the first strictly later, still-untouched bar closing beyond the frozen threshold. Neither the pause bar itself nor the first-touch bar can be an occurrence. `first_no_new_extreme_time`, `first_opposite_close_time` are convenience aliases. `pre_pause_extreme` / `pre_pause_high` / `pre_pause_low` refer to the no-new-extreme definition; the opposite-close threshold remains separate.

MFE uses the research occurrence close as reference and **strictly later** complete same-date bars, clamped to zero. The occurrence bar's high/low is excluded because it can precede its close. Subsequent touch or invalidation does not truncate descriptive MFE: the request asks for subsequent same-day excursion, without selecting an invalidation method or exit rule. No later complete bar gives null MFE; nulls are excluded from averages and threshold denominators, with counts disclosed. There is no order fill or realized outcome in these measurements.

Never-touched continuation statistics are a hindsight cohort; membership is not known until the date ends. Multiple FVGs and research occurrences can share price observations and are not independent trades. All cohort denominators, direction splits and formation-time bins are present in the JSON and readable report.

## Validation and tests

The full data run verifies one row per input FVG, preserved original fields, source-joined earliest touch/fill/invalidation events, exact first/second slots, untouched extremes/counts, separate expiration rules, pause first occurrences/thresholds, trigger first occurrences, and strictly post-trigger MFE. A separate vector reference checks pause logic, rather than trusting the loop's own results. No input file is changed.

Tests cover Candle 3 exclusion; next-bar start; same-day limits; both directions' fill and strict close/wick rules; equality boundaries; per-method expiration; next-date exclusion; directional distance; first/second classification; no-new-high/low and opposite-close pauses; pause threshold/trigger timing; no missing-slot substitutions; censoring; skipped incomplete bars; gap-through without overlap; MFE look-ahead controls and null tails; summary denominators; source validation corruption checks; DST midnight; determinism; duplicate rejection; and one record per FVG.

For this task, the explicit instruction is a **local commit only**. No push is performed. Market data, samples and JSON outputs remain ignored and uncommitted.

## Completed run

The output contains **10,608 records and 137 columns**, preserving all 10,608 source FVGs (5,709 bullish / 4,899 bearish). Independent validations passed. The test suite passed **79 tests**: 37 lifecycle tests plus the 42 existing bar/FVG tests. The complete summary is in `LIFECYCLE_RESEARCH.md`; the Parquet is 4,853,711 bytes for this pinned-runtime build.
