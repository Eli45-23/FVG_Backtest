# Research v2: mechanical definitions and evidence

Research version 2 is opt-in for new studies; version 1 JSON artifacts remain readable.
No old artifact is migrated or overwritten. Studies snapshot dataset identity, frozen XNYS
calendar, engine code digest, and every resolved setting. The v2 storage schema is local
Parquet with Zstandard compression; DuckDB filters/groups on the server. Source bars remain
in memory, but event/outcome writes use bounded batches and exports stream. API pages cap at
1,000 records. No event or baseline observation is sampled away.

## Timeframes and causality

Raw fixed-point minutes are scaled by Decimal 1e9 and grouped into exact anchored windows.
Presets are extended UTC 00:00 or RTH America/New_York 09:30; the JSON configuration also
accepts explicit NY extended anchors. Anchors are local wall-clock times, localized before
elapsed-duration grouping. Ambiguous/nonexistent DST anchors fail; no silent clock shift.
A complete frame contains every exact minute, including first and last. RTH partial 4h bars
at close are incomplete and cannot confirm features. Half-days use actual XNYS closes.
No 4h information appears until all 240 minutes close. The validated 5m file is used intact.

The primary callback timeframe is selectable; 1m fills always remain separate. FeatureHub
merges confirmation iterators; public snapshots have no future rows and are read-only.
Thirty calendar days of warmup precede requested dates (limited by source availability).
A shorter beginning-of-dataset warmup is reflected by unavailable measurements.

## Structure and 4h levels

A strict high pivot exceeds every high among L left and R right candles; lows mirror this.
Equality does not qualify. It becomes available at the Rth right candle's close. Displacement
is the pivot-to-opposite-extreme range across the confirmation window. Both configured point
and ATR minima must pass, using ATR known at confirmation. Defaults L=R=2, both minima zero.
Gaps/incomplete bars reset the pivot window.

Successive confirmed highs classify HH/LH/equal; lows HL/LL/equal. HH+HL establishes BULLISH;
LH+LL establishes BEARISH. Otherwise the prior state persists (initially NEUTRAL). A strict
close through a known swing in the established direction is BOS; against it is CHOCH and
changes state. A neutral close break is STRUCTURE_BREAK. Each swing can break once. Old
progression cannot undo a CHOCH until a new pivot confirms. No retroactive timestamps.

Latest confirmed 5m and 4h high/low remain research levels until replaced by a newer swing,
including after breaks so retests can be studied. Broken status is explicit; a break is not
silently treated as a fresh unbroken level. Snapshots include formation/availability,
displacement, touch episodes in the source timeframe, distances and broken status. These
are support/resistance references, not an inferred persistent order-book level.

## Compound sequences

Individual v1 interaction definitions are preserved. Sequences consume confirmed events only.
A break and immediately adjacent complete candle can emit CLOSE_HOLD (close strictly on new
side), FULL_HOLD (entire range strictly on new side), or FAILED_HOLD (close on old side).
An exact-level close is neither hold nor fail. A later separate touch episode from the new
side links a RETEST to its most recent break, with close HOLD/FAIL on that retest candle.

A candle cannot touch a level and remain strictly outside it simultaneously. The explicit
`retest_full_hold=adjacent_after_retest` convention therefore requires the next complete
candle after retest to lie strictly on the new side. Both stage times are retained. Sweep
or rejection confirmation requires the next adjacent close beyond the event candle's
away-side extreme. No wick-only confirmation. Gaps, incomplete bars and NY date changes
reset sequence state. Components, root IDs, availability and deterministic IDs are retained.

## DisplacementBaseZoneDetectorV1

Only 4h zones are used by platform FeatureHub (the detector itself is timeframe reusable).
Defaults are descriptive configuration, not optimized parameters: 1–3 consecutive base
candles, each body/range <=0.5, aggregate base range <=1 ATR; departure within 3 bars.
Departure close must leave the base by >=1.5 base-known ATR AND either break a confirmed
swing or exceed the configured point displacement (default zero, explicitly disabling that
extra point hurdle). Demand departs upward; supply downward. Full-base bounds use max high/
min low. Alternative body-proximal/wick-distal uses maximum base body for demand proximal
and minimum base body for supply proximal, retaining the opposite wick boundary.

Availability is departure confirmation, not base formation. Later range overlap starts a
new touch episode; close strictly through distal invalidates. Touch marks mitigation.
Missing/incomplete source bars clear pending bases/departures. Historical zone metadata
retains invalidated zones; active zones alone become interaction levels at their proximal
boundary. No subjective drop/base/rally judgment is applied.

## Indicators and context

EMA9/20 seed at first complete close with alpha 2/(N+1), resetting after gaps. ATR14 is the
simple mean of 14 true ranges, not Wilder ATR. Percentile ranks current ATR against the
prior 252 available ATR observations; low/middle/high split at 1/3 and 2/3. No future ranks.
Directional efficiency uses 20 close changes. Rolling range uses the same window.

VWAP uses typical HLC3 × volume from the explicit same-date NY session (default RTH
09:30–16:00, clipped to actual XNYS close). Missing/incomplete contributing bars make the
session VWAP unavailable; no forward-filled or partial-session VWAP is presented as complete.
A timeframe without a candle at the configured session start has no valid session VWAP.
Slope, separation, cross times, cross frequency, alignment and normalized distance are
causal descriptive fields. EMA/VWAP chart overlays are snapshots at event confirmation,
not fabricated historical indicator curves.

PDH/PDL and previous close require the immediately prior fully observed RTH session. Current
RTH open, previous range, open-minus-prior-close gap, and (open-PDL)/(PDH-PDL) are explicit.
Opening location is not clamped. O5 range exists after 09:35. Premarket range requires an
explicit SessionConfig window; it is disabled by default.

## Outcomes and inference

Detection finishes before the separate forward label pass. All original point horizons and
thresholds remain. ATR thresholds divide by ATR fixed at confirmation, never future ATR.
Missing/invalid minutes or out-of-session horizons are censored. Directional continuation or
rejection chooses high/low excursion; raw price-up/down labels remain separately exportable.
Threshold times are minute-end bounds, not inferred intraminute timestamps.

Ordinary complete RTH 5m confirmations are baseline observations. Matching uses year,
confirmation half-hour, and the existing fixed ATR14 bucket. For each event, its stratum's
baseline probability is matched; then differences average within NY date. Each date gets
one equal weight in inference regardless of event count. Bootstrap resamples date differences
with replacement using stored seed 1729 and 2,000 iterations by default. CI is percentile
2.5/97.5%; a centered bootstrap null gives a two-sided p-value with +1 correction. BH q-values
correct only the groups shown in the current screen, not every exploratory query ever made.

Assumptions: dates are approximately independent/exchangeable; serial dependence across dates
is not modeled. Baseline means are treated as fixed descriptive references, so intervals do
not incorporate a separate baseline-estimation stage. Matching is observational, not causal
proof. Fewer than 10 matched dates is flagged; fewer than 2 yields no CI/p-value. Degenerate
bootstrap samples can have zero-width intervals and must not be interpreted as certainty.
Repeated exploration still requires held-out validation. No profitability or best-strategy
classification is generated.

## API and UI

Create `/api/level-research/studies` with `research_version:2` and `research_settings`.
Resolved keys: frame, structure, zones, indicators, sequences, numeric_filters, statistics,
atr_thresholds. Numeric rules accept inclusive min/max and strictly increasing finite edges;
buckets are lower-inclusive, upper-exclusive. Missing values fail bounded filters.

POST `.../{id}/query` supports categorical/numeric filters, stable sort and pagination.
POST `.../{id}/statistics` adds group, horizon, direction interpretation and a point/ATR
threshold. Grouping fields are allow-listed; numeric grouping requires saved/supplied edges.
GET export streams JSON including configuration or CSV event payloads. Charts use persisted
causal context with optional session-level, swing, zone, indicator and sequence overlays.
Query changes are exploratory views; the creation filter/bucket definition is immutable.
Create a new study to freeze another view. Existing v1 endpoints remain supported.

OOS outcome gates apply to statistics and all exports; sealed charts stop at confirmation.
No reveal state is mutable or resettable. An old sealed study still requires its original
frozen engine identity to label; this upgrade does not silently relabel it with new code.
