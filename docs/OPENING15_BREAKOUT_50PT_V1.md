# Opening 15-minute breakout, preceding-candle stop, 50-point target

Frozen before execution on October 9, 2026. Status DEVELOPMENT_ONLY_NOT_VALIDATED. This is a sequential single-position backtest, not an overlapping event portfolio. No parameter optimization or reserved-period outcomes.

## Source and session

Use research_2020_2026, New York dates 2020-01-01 inclusive to 2024-01-01 exclusive, validated 5m candles and native 1m fills. Retain the user's prior full-XNYS-session trading convention: exclude holidays and early closes. No new entries at the session close. Close remaining positions at 16:00 ET. Preserve all existing data, saved runs and prior artifacts.

The opening range is the exact wick-inclusive maximum high and minimum low of the three complete consecutive candles starting at 09:30, 09:35 and 09:40 ET. Independently reconcile to the fifteen eligible source minutes. It becomes known at 09:45 and remains fixed all day. Missing/incomplete opening data makes the range unavailable for that date; no stale fallback.

## Causal breakouts

First later complete 5m candle closing strictly above the opening high emits LONG; strictly below the opening low emits SHORT. The earliest signal is the 09:45–09:50 candle, available at 09:50. A wick alone or an equal close is not a breakout. The immediately preceding 5m candle must be complete and adjacent. No missing-bar bridging.

After a long breakout, consecutive closes above the high do not emit more signals. A complete close strictly below the high rearms LONG; another close strictly above emits the next breakout. Mirror for SHORT (strict close above the low rearms). A close exactly on the boundary does not rearm a consumed breakout. At initial range availability both directions are armed. After a missing/incomplete bar, clear continuity and both arms; a subsequent complete close on the strict inside side may rearm, but no signal can be emitted without its complete adjacent predecessor. This rule uses only confirmed bars.

The detector runs regardless of whether a position is open. Record every qualifying breakout. One position total across both directions; no daily trade cap. Skip signals while entry time < current position exit time; do not defer them. An exit exactly at a new signal's confirmation permits the next entry. No immediate reversal or management of an existing trade.

## Prices and fills

Entry at signal close plus adverse configured slippage. LONG stop = immediately preceding candle low exactly; SHORT stop = immediately preceding candle high exactly. No tick buffer. Reject nonpositive executed risk explicitly. All executable prices remain tick-aligned.

Target = executed entry +50 points for LONG or -50 for SHORT. Fixed points, not 50 points from the pre-slippage close and not a fixed R multiple. Native executor is supplied the mathematically equivalent 50/originalRisk multiple and every target price is checked exactly. No partials, breakeven or trailing stop.

One MNQ micro, $2/point. Actual user fee per side: commission $0.25 + exchange $0.35 + clearing $0.12 + NFA $0.01 = $0.73, or $1.46 round trip. Primary: one adverse entry tick and one adverse exit tick. Sensitivity: zero and two ticks with the same raw signals, independently reselecting positions because fill timing can change occupancy. No fees invented.

Ownership begins with the minute starting at entry confirmation, excluding all activity inside the finished signal candle. Native conservative stop-first conflicts, adverse stop gaps, target fill semantics, final-minute priority and session close remain unchanged. Missing required owned minutes make the position EXECUTION_DATA_UNAVAILABLE; do not synthesize or use future missingness to reject its entry. Suspend further entries that date if an unresolved position exists, and withhold an unqualified total performance claim. Inclusive exit-minute MFE/MAE carry intraminute-order uncertainty.

## Time research: descriptive, no entry filter

Group by actual entry/confirmation time in New York, not bar start: 09:45–09:59, 10:00–10:29, 10:30–10:59, 11:00–11:59, 12:00–13:59, 14:00–15:59. Signals at 16:00 are separately ineligible. All six groups are predefined, including negative findings. Report raw breakouts, position-open skips, trades, unique dates, net win rate, net USD, PF, average/median net R, mean net USD/trade, drawdown, risk and year consistency; separate LONG/SHORT and each 2020–2023 year. Also retain monthly results and chronological equity.

Bootstrap mean net R and mean net USD/trade by NY trading date within each time group using 5,000 deterministic resamples, seed 1729. These exploratory intervals are not multiplicity-adjusted proof of the best time. Report sample sizes, yearly reversals and slippage sensitivity. Do not automatically promote a profitable window to an eligibility filter. Window-subset drawdown is descriptive; it does not constitute a rerun with that time filter, which could change position selection.

## Verification and outputs

Reconcile opening ranges to all underlying minutes; independent detector replay; synthetic edge tests; all native completed fills independently reconciled; strict no-overlap checks; frozen source/code hashes; exact full rerun equality. No Validation/OOS decoding or outcomes. Full audit, trades, summaries, yearly/time/cost tables, equity and reproducibility manifest remain in work/opening15-breakout-50pt-v1. Expose verified outputs read-only in the Lab; no alteration to the production executor.
