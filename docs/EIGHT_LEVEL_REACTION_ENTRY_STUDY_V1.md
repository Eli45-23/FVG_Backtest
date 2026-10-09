# Eight fixed levels: reaction and entry-timing study v1

Prospectively frozen October 9, 2026 before this run's outcome analysis. DEVELOPMENT_RESEARCH_NOT_VALIDATED. This is not an executable portfolio backtest and does not identify an optimal target or guarantee an edge.

## Scope

New York 2020-01-01 inclusive to 2024-01-01 exclusive. Existing research_2020_2026 data, actual XNYS RTH including its early closes; no holiday observations. No date, direction, indicator, volatility or touch-number eligibility optimization. One-minute forward outcomes; confirmed five-minute signal decisions. Every event is retained independently; overlapping observations are not separate independent experiments or simultaneous tradable positions.

Eight fixed same-date levels: previous completed XNYS RTH high/low; midnight–09:30 premarket high/low; 09:30–09:35 opening high/low; 09:30–09:45 opening high/low, all wick-inclusive. A missing/incomplete required source bar makes the corresponding level unavailable, with no stale fallback. Opening levels require all one/three complete five-minute source candles and become available at 09:35/09:45, never during construction. They persist to that day's session close. O15 is the exact high/low reduction of the first three complete five-minute bars, equivalent to the confirmed fifteen-minute opening candle.

Reuse the six matching completed Development level event artifacts without modifying them. O15 uses the existing causal EventDetector/Sequences on new opening levels. New entry-timing adapters have no forward outcomes input. Prior knowledge of Development findings is explicitly acknowledged; this is not fresh unseen discovery.

## Mechanical event definitions retained

A break requires prior adjacent close (or current open after reset) strictly on one side and current confirmed close strictly opposite. A contact episode is consecutive candles whose ranges contain the level; only its first touching candle emits TOUCH. Retest is a new touching episode from the breakout side following a recorded break. Rejection is first-touch close back on approach side with at least 0.25-point clearance and minimum penetration zero. Failed break here means the immediately adjacent complete next candle closes strictly back across the level. These are finite definitions, not every possible colloquial rejection or eventual failed break. Missing/incomplete adjacency clears compound state. Root identities and overlap are retained.

## Ten predefined entry candidates

All entry references are the indicated confirmed five-minute close, without fees/slippage because these are forward price measurements, not simulated trades. No future success qualifies an entry.

1. BREAK_CLOSE: every confirmed break, including subsequent failures and retests.
2. BREAK_FIRST_FULL: first whole candle strictly on the breakout side (wicks included), possibly the break candle itself. Later eligibility cancels on any intervening level-touch, wrong-side/equal close, missing/incomplete bar, new break or session end. This records direct departure only as known then, not absence of future retests.
3. BREAK_NEXT_CLOSE_HOLD: adjacent next complete candle closes on the new side; it may touch the level.
4. BREAK_NEXT_FULL_HOLD: adjacent next complete candle is wholly on the new side, no touching. It can still retest later.
5. RETEST_CLOSE_HOLD: frozen BREAK_RETEST_HOLD confirmation close, in original breakout direction. Every distinct supported retest is retained.
6. RETEST_RANGE_ESCAPE: after a retest closes on the breakout side, accumulate high/low of that contiguous touching episode; first subsequent complete close strictly beyond that episode extreme on the breakout side confirms. No body-ratio filter. Cancel on close at/across level, a new contact episode before escape, new root break, missing/incomplete adjacency or session end. Reference range never includes the confirming escape candle.
7. REJECTION_CLOSE: frozen rejection candle close, moving away from the approach side.
8. REJECTION_CONFIRMATION: immediately adjacent complete candle closes beyond rejection candle extreme in the reversal direction; use the existing sequence.
9. FAILED_BREAK_CLOSE: frozen adjacent failed-hold candle close; evaluated direction is opposite the root break.
10. FAILED_BREAK_CONFIRMATION: immediate next complete candle closes beyond that failure candle's extreme in the reversal direction.

The break entries belong to direct continuation; retest entries to break–retest–continuation; rejection entries to test–rejection; failed entries to break–failure–reversal. Classes overlap. Whole-candle candidates are stricter than close-only candidates. There is no hindsight grouping of initial break entries into only eventual successful continuations.

## Outcomes and denominators

Horizons 5, 10, 15, 30, 60 minutes and actual RTH close, all starting at event confirmation. Fixed distances 10, 25, 50, 75, 100, 150, 200 points; ATR distances 0.5, 1, 1.5, 2 based on causal 5m ATR14 (simple mean true range, reset on gaps). Report hits both favorable/adverse, first-hit minutes, favorable/adverse excursions, forward close change and adverse excursion through first favorable hit. The hit minute's full range is included in this last adverse metric; intraminute order is unknown and disclosed.

Keep all raw causal events, including unavailable ATR or insufficient remaining session time. A horizon crossing the close is censored, not a failure and not a shortened complete horizon. Missing/invalid required minutes censor that horizon. Show complete/censored/ATR-unavailable denominators separately. Session-close events remain in raw counts but have no forward outcome. All valid ordinary RTH five-minute observations form the baseline; no event-based baseline cherry-picking.

## Statistical protocol

Primary family: all 8 levels × 10 entry candidates × 2 evaluated directions = 160 hypotheses, 30-minute favorable 50-point probability versus matched ordinary observations. Match year × confirmation half-hour × existing fixed causal ATR bucket. Missing ATR is an explicit UNAVAILABLE bucket for fixed-point matching, never removed as entry eligibility. Use equal-weight NY-date mean differences, existing date-cluster bootstrap (2,000 repetitions, seed 1729), 95% intervals and one global BH correction across all 160 cells; empty/unsupported cells use p=1. Intervals condition on the empirical baseline pool; they do not estimate uncertainty in re-fitting the baseline or prove a causal treatment effect. Fewer than 30 dates is flagged small sample. Every other horizon/threshold, yearly/context split and paired entry comparison is descriptive/exploratory.

Candidate counts and unique dates are not reaction probabilities without a denominator. Report unique qualifying roots relative to: all breaks for break/retest/failure candidates; matching-direction raw touch observations for rejection candidates. Break-root denominators include roots that never retest/fail. Report event counts separately because multiple retests can belong to one break. Pair earliest entries per shared root and direction for timing diagnostics only; these are a selected common-root subset, not a causal proof of better entry. Report unconditional coverage and missed opportunities alongside paired results. Do not infer net profitability or select stops/targets from this study.

## Safeguards and delivery

Immutable prior studies, database records, gates and data files unchanged. No Validation/OOS outcome reads. Use columnar complete event/outcome exports; no sampling to compute results. Synthetic causal tests, independent outcome checks, deterministic rerun comparisons and source hashes accompany Markdown, aggregate CSV/JSON and a browsable local results page. No new executable strategy or parameter sweep. Production engine behavior is unchanged.
