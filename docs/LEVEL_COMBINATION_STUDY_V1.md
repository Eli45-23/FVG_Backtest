# Eight-level combinations: frozen Development protocol v1

Status: DEVELOPMENT_RESEARCH_NOT_VALIDATED. Frozen before outcome calculation for this task. Existing Development evidence has already been inspected; this is not independent validation. No threshold search or strategy selection.

## Inputs and identity

Reuse all BREAK_CLOSE and REJECTION_CLOSE signals from the verified eight-level study, both directions, 2020-01-01 inclusive to 2024-01-01 exclusive. Reuse its exact daily level coverage, availability timestamps, source identities, XNYS sessions (including early closes), and causal ATR14. PDH/PDL, midnight–09:30 PMH/PML, first opening five-minute O5H/O5L and first opening fifteen-minute O15H/O15L are the eight levels. They are fixed for their date once available. Only levels available by signal confirmation enter context; unavailable levels are explicitly missing, not assumed absent. Signal definitions and past studies remain unchanged.

## Context measured at the original signal

A nearby forward obstacle is another known level strictly beyond the raw signal close in its evaluated direction, at distance <= 1.0 causal ATR14. Freeze the entire set and its farthest price at the original signal; do not add later levels retrospectively. Record all known levels, exact coincident levels, nearest forward level, room in points/ATR, and known level count. No ATR means UNKNOWN context, never removal from immediate execution. No known obstacle is not proof of unrestricted room.

A rejection cluster means at least one OTHER known level within 1.0 causal ATR14 of the rejection's root level, either side. Equality counts. This describes proximity, not independent confirmations: also record how many of those levels the actual rejection candle touched. ISOLATED means no such known nearby level; report incomplete level coverage separately. One ATR is a predeclared coarse research convention, not a tuned distance, and will not be varied.

## Comparison 1: wait versus immediate

For every raw break, IMMEDIATE enters at its confirmed close. For roots with a nearby forward obstacle, WAIT_CLEAR_HOLD waits for a later complete five-minute candle to close strictly beyond the frozen farthest obstacle; the immediately adjacent next complete candle must be wholly beyond it (wicks included). Enter that hold candle's close. A failed full hold can start a new clearance attempt if that candle closes beyond the barrier. Cancel waiting on any close at/across the original root level, missing/incomplete five-minute adjacency, or session close. Do not use future outcomes or future levels. Keep the original root signal candle invalidation stop for both entries. Waiting can enter even if the hypothetical immediate trade would already have closed: they are separate policies.

All obstacle roots remain in the waiting-policy denominator. No confirmation is NO_ENTRY, with zero economic exposure, not a hypothetical losing or winning trade. ATR-unavailable or no-nearby-obstacle roots have no WAIT policy comparison; their IMMEDIATE results remain reported. Report entry coverage, cancellation reasons, trade-conditional results and net USD/R per original opportunity separately. Conditional common-root comparisons are selection diagnostics, not proof that the immediate entry could know the future hold.

## Comparison 2: clustered versus isolated rejection

Execute every existing confirmed rejection independently. Compare CLUSTERED with ISOLATED within root level and direction, matching year × original confirmation half-hour × causal volatility bucket × full-eight-level-coverage indicator. Unknown ATR remains in execution but not an invented cluster group. Report supported and unmatched observations explicitly. Clustering may reflect common price information; shared candles/roots overlap and are not independent evidence.

## Frozen execution diagnostics

One MNQ micro, $2/point, tick 0.25. LONG stop = original signal candle low minus one tick; SHORT stop = original signal candle high plus one tick. No optimized stop or management. Fixed 1R primary and 2R secondary from executed entry; normal validated tick rounding. Entry/exit adverse slippage 1 tick primary, 0 and 2 ticks sensitivity. Actual user fee $0.73 per side ($0.25 commission + $0.35 exchange + $0.12 clearing + $0.01 NFA). Session-close exit, no overnight. Production native executor handles all fills; stop first for same-minute conflicts, strict missing owned minutes. Event candle is over before execution begins. Nonpositive risk and confirmation-at-close are explicitly non-executable, not removed from raw populations.

Independent overlapping diagnostic trades, NOT a sequential portfolio. No daily lock, no aggregate claim of achievable portfolio profit or portfolio drawdown. Dollar sums are diagnostic sums only. Stops do not move when waiting; larger risk is reported. Source event overlap and identical trigger candles are audited. No time, weekday, EMA/VWAP, structure or availability-of-future-label filters.

## Statistical comparisons

Primary family has exactly 32 slots: 8 levels × 2 directions × {WAIT_MINUS_IMMEDIATE, CLUSTERED_MINUS_MATCHED_ISOLATED}. Outcome = after-fee net R, 1R target, 1 adverse tick. Waiting: paired original opportunities, no-entry=0; incomplete execution pairs excluded from estimate with count reported. Cluster: subtract stratum mean isolated net R from each matched clustered rejection. Aggregate differences within NY date, then equal-weight dates. Bootstrap 2,000 resamples, seed 1729, 95% percentile CI and two-sided centered bootstrap p-value (plus-one correction). One BH adjustment across all 32 slots; unsupported slots p=1. Cluster CIs condition on the empirical isolated benchmark, not uncertainty in re-estimating it. These are exploratory Development comparisons, not causal claims. Report every year, event/date counts, costs and negative results. Fewer than 30 dates is flagged. Other targets/costs/context summaries are descriptive only.

## Preservation and delivery

No Validation/OOS outcomes, new market downloads, source mutation, old artifact rewrites, DB writes or production execution changes. New immutable reproducible artifacts, synthetic timing tests, independent fill verification, byte-identical full rerun, local Lab results page and complete exports. Existing repository commit/push policy applies. No new final executable strategy is selected by this study.
