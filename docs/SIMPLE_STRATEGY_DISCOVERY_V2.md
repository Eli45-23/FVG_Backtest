# Simple strategy search — second frozen batch

DEVELOPMENT_ONLY_NOT_VALIDATED. This continuation is exploratory on already
inspected 2020–2023 data, not independent confirmation. No Validation/OOS reads.
Freeze this document and detector before calculating outcomes. Preserve v1.

Exactly three new hypotheses, complete adjacent RTH five-minute bars A,B,P,C:

1. PULLBACK_RESUME: long when B.close>A.high, P is bearish, P.low>B.low,
   and C.close>P.high. Short mirrors all inequalities. Stop one tick beyond
   the opposite extreme of P and C. A surge, a one-candle pullback, then resumption.
2. RANGE_FAILURE: long when C.low is strictly below the lowest A/B/P low,
   C closes strictly inside their high/low range, and C.high does not exceed
   that range high. Short mirrors. Stop one tick beyond C's opposite wick.
   A candle sweeping both boundaries is ambiguous and has no signal.
3. THREE_BAR_BREAK: C closes strictly above the highest A/B/P high for long,
   or below their lowest low for short. Stop one tick beyond the opposite
   A/B/P range edge. No range-size or body filters.

Earliest confirmation 09:50. Both directions. Missing/incomplete bars reset
adjacency. Entries use only confirmed candles. First eligible signal daily.
Reuse v1 native execution, account, costs, risk and session handling unchanged:
$500 account, $75 planned all-in maximum risk, one actual trade/day, fixed 2R,
$0.73/side/micro, 1 tick/side primary and 0/2 sensitivities, full XNYS sessions,
actual close liquidation. Planned net reward must exceed planned loss. Five
v1 account/margin modes remain separately reported. $200/$400/$4763 margin
are inherited sensitivity assumptions, NOT freshly verified live/historical
broker requirements. No deposits or daily balance resets. No management.

All 1,000 full sessions, including skipped/losing/lockout days, count in daily
averages. No future missingness may remove a signal; native strict execution
handles missing owned minutes and unknown account paths.

Use identical v1 qualification gates and calendar-month bootstrap (5,000 draws,
seed1729), but Holm correction now includes ALL SIX hypotheses from both batches.
Prior published v1 evidence remains unchanged; new combined evidence is additive.
A positive result earns only potential later frozen validation, not 'works live'.
Do not change rules, target, directions, or trade times after seeing these results.
No further automatic search after this batch: report failure if none qualify.
This bounded stop rule prevents searching indefinitely until chance wins.

Goal remains $100 average net per all trading days, separately from evidence of
positive expectancy. No claim that a $75 planned stop guarantees maximum loss.
Source identities and storage must match existing preserved research manifests.
