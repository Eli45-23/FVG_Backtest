# Downward breaks: immediate next-candle full-hold controlled audit

Status: DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY. Frozen before execution analysis on October 9, 2026. This follow-up changes only entry eligibility/timing relative to DOWNWARD_BREAK_EXECUTION_FEASIBILITY_V1.md, whose results remain unchanged.

SHORT at the close of the immediately adjacent complete five-minute candle following a downward break, only when its entire range is strictly below the level (high < level). Equality is not sufficient. Both candles must be complete, adjacent and within the same actual XNYS RTH session. The level must already be available. Entry ownership starts after confirmation, using the minute starting at confirmation. No candle inside the completed confirmation bar is owned.

Use all 4,784 causal BREAK_NEXT_FULL_HOLD / DOWN observations on 889 Development dates: PDH 366, PDL 391, PMH 499, PML 633, O5H 692, O5L 841, O15H 628, O15L 734. Independently reconcile all 11,364 original break roots to complete next-bar OHLC. Preserve the 6,580 without confirmation in the opportunity audit; do not filter on subsequent outcomes, ATR availability, future missingness or horizon completeness.

All other conventions are inherited unchanged from the immediate-break audit: research_2020_2026, NY 2020-01-01 inclusive to 2024-01-01 exclusive, all eight levels separately, actual XNYS sessions including early closes. No Validation/OOS outcomes, additional filters or management.

Stop A: level + 0.25. Stop B: ORIGINAL ROOT BREAK candle high + 0.25, not confirmation candle high. Outward tick rounding is unchanged. Risk and fixed original 1R/2R targets use the later executed entry. Nonpositive risk is explicitly rejected. Quantity one MNQ, $2/point, actual user fee $0.73/side ($1.46 round trip), primary one adverse tick each side; zero/two-tick sensitivity. Native one-minute stop-first execution, adverse gaps, actual session-close exit and missing-owned-minute failure remain unchanged. At-close signals remain in raw counts but cannot enter a post-close trade.

Every event is an independent potentially overlapping diagnostic, not a portfolio or one-trade-per-day strategy. Use the prior frozen path/horizon, excursion ambiguity, yearly and fee reporting conventions unchanged. No optimization or best-target selection.

Compare every level/stop/target/cost against original all-root results and against original immediate entries on the same confirmed roots. Also report omitted-root results and original trades already closed by delayed entry. Matched-root comparisons condition on a later observed confirmation, so they are descriptive selection-conditioned comparisons, not causal proof that waiting improves an entry. No claims of corrected statistical significance from diagnostic P&L.

Require exact root mapping, original absolute stop equality across both audits, independently verified complete five-minute OHLC, unchanged source identities, native/independent fill equivalence and byte-identical reruns. Existing studies, saved runs, production engine and source files remain untouched.
