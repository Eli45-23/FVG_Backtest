# Simple MNQ search: decision review

**No strategy has yet earned a validated or consistently usable claim.**
The strongest exploratory lead in this twelve-policy screen is a preceding-hour
range breakout. The account-size, dollar-risk, daily-profit and one-trade/day
constraints were removed. All results use one micro, $0.73 fees per side and
1 adverse tick per side, with fixed 2R and no management.

## The simple lead

On a five-minute RTH chart, mark the highest high and lowest low of the preceding
12 complete candles. At a confirmed close above the high, buy; below the low,
sell. Put the stop one tick beyond the opposite range edge and target 2R from the
executed entry. Hold only one position, permit a later fresh signal after exit,
and close at the session close. Missing/incomplete bars reset range continuity.
No EMA, VWAP, FVG, time, weekday, or regime filter is applied to this policy.

## What is known — and what is not

The policy has 1,488 completed primary trades and one unresolved selected trade.
Known completed trades total +$14,609.52, PF 1.142, average net R +0.072.
These are **partial figures**, not certified full-period profit. Median structural
risk was 89.5 points ($179 before exit costs) per micro; the largest was 517
points. Known-trade drawdown was $3,934.04 and the worst known day lost
$1,118.34. Full drawdown remains unresolved with the missing execution interval.

| Year | Completed-trade net | Execution coverage |
| --- | ---: | --- |
| 2020 | +$2,810.68 | One selected trade unresolved |
| 2021 | +$4,810.58 | Complete |
| 2022 | +$3,987.78 | Complete |
| 2023 | +$3,000.48 | Complete |

One missing execution interval on 2020-03-18 blocks a complete result. The strict
run neither fills the gap nor deletes the signal. The raw archive also lacks those
minutes. Official halt context is documented in
`docs/MNQ_SEARCH_DATA_GAP_REVIEW.md`; exact instrument treatment remains unresolved.
No production execution rule was changed to rescue this result.

A clearly secondary, post-hoc complete-day sensitivity over 999 known days gives
mean +$14.62/day, month-block 95% CI [$3.15, $26.89], unadjusted p ≈ 0.0102. It excludes the
unknown day for measurement only, never for entry eligibility. It is **not** the
registered primary test. With 18 policies in the initial search family, that nominal p-value
would not meet Holm 0.05 (smallest-p adjustment ≈ 0.1836). Thus even that sensitivity
cannot establish a search-adjusted discovery. The subsequent two timing tests
bring the combined ledger to 20 policies; the comparable adjustment would be
approximately 0.204, also above 0.05. It cannot be used to bypass the
missing-data or multiple-testing gates.

## Other results and limits

The full report preserves all 12 policies, 36 cost scenarios, raw and rejected signals,
all years, risk, costs and losing outcomes. Several policies lose substantially.
An overall positive dollar total can coexist with negative average R or dependence
on a few days; none passed the frozen complete screen.

The lead is not an instruction to trade it. Next useful work is an independently
supported halt/session treatment and, only if justified afterward, a separately
frozen validation request. Do not change entries, stops or targets to improve
these inspected Development results. Validation/OOS were not queried.

Reproduction and local artifact paths are documented in
`docs/SIMPLE_UNRESTRICTED_REPRODUCTION.md`. The verified Lab report is available
under Research → Simple MNQ strategies · Unrestricted research.

## Separate timing follow-up

Two pre-registered, literature-motivated final-half-hour policies were tested after
the initial search, with a structural stop and session-close exit instead of 2R.
The RTH-morning-direction version lost $2,135.24; the previous-close-inclusive
version lost $5,217.16 after primary costs. Neither qualified. See
`outputs/SIMPLE_TIMING_FOLLOWUP_REPORT.md`. The initial immutable study was not
rewritten; the follow-up evidence table applies Holm across all 20 policies.

## Verification

101 relevant tests passed (94 detector/execution/session/management tests, 4 API,
2 frontend, 1 browser export workflow), and the production build passed.
The main search independently reconciled 102,022 signals and 108,441 unique native
fill calculations; the timing follow-up checked another 5,970 fills. Both studies
reproduced byte-identically. Source and normal-storage hashes remained unchanged.
No market data, raw trade exports or credentials were added to Git.
