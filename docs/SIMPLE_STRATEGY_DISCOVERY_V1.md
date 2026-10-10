# Simple MNQ strategy discovery v1 — preregistration

DEVELOPMENT_ONLY_NOT_VALIDATED. Frozen before running any new hypothesis outcomes.
This is a bounded search, not a claim to exhaust all simple strategies.
Previously inspected Development history is known; these are fresh rules for this
project, not unprecedented inventions or an independent untouched sample.

## Objective and data

2020-01-01 inclusive to 2024-01-01 exclusive, research_2020_2026. Full XNYS RTH
sessions only, no holidays/half-days. The denominator is EVERY eligible full
session including no-trade and capital-lockout days. $500 initial capital, no
external deposits, no withdrawals, at most one actual entry per NY date.
Objective: >=$100 average net per eligible day. At most $75 planned all-in loss
per trade. Actual gaps can exceed that budget and are reported, never clipped.
No Validation/OOS decoding or outcome queries. Hashing entire source files is
identity verification only. Normal storage and past research artifacts preserved.

## Exactly three hypotheses; no tuning after seeing results

Each uses complete adjacent five-minute RTH candles M, P, C (oldest to newest).
Incomplete/missing bars reset continuity. Entry at C confirmed close, never before.

1. TWO_PUSH: long when P and C are bullish, P.close > M.high and C.close > P.high.
   Short mirrors: both bearish, P.close < M.low and C.close < P.low.
   Stop: minimum P/C low minus .25 for long; maximum P/C high plus .25 for short.
2. OUTSIDE_REVERSAL: long when P is bearish, C bullish, C.low < P.low and
   C.close > P.high. Short when P bullish, C bearish, C.high > P.high and
   C.close < P.low. Stop beyond C's opposite wick by .25. Still requires three
   adjacent bars for a common minimum observation window; M is not a price filter.
3. INSIDE_BREAK: P.high < M.high and P.low > M.low; C closes strictly above
   M.high (long) or below M.low (short). Stop beyond M's opposite wick by .25.

No other indicators, key levels, time/risk subgroup filters, repeated entry or
management. Earliest signal close 09:45. Both directions included. A first signal
that fails known risk/capital eligibility does NOT consume the daily lock. First
eligible signal wins; all later signals logged DAILY_LIMIT_REACHED, not optimized.

## Execution / cost / sizing

Native production 1m executor unchanged. Entry/exit each suffer 1 adverse tick
primary; 0 and 2 ticks sensitivity, not selected as a winner. Target fixed original
2R from executed entry. Stop-first simultaneous hits, adverse opening stop gaps,
actual session-close exit. No fills inside completed trigger candle.
User costs: commission .25, exchange .35, clearing .12, NFA .01 = .73 per side per
micro. Per-contract planned stop loss L = 2*risk_points + .50*ticks + 1.46.
Per-contract planned target gain W = 4*risk_points - .50*ticks - 1.46.
Require risk>0, L<=75 and W>L: planned net reward exceeds planned all-in loss.
No minimum $100 winning trade filter. Entire daily loss budget includes all fees
and assumed exit slippage; entry slippage is already in structural risk.

Study layers, never pooled or cherry-picked:
- ONE_MICRO_DIAGNOSTIC: first eligible one-micro signal daily, risk/reward rules,
  without account/margin constraints. Not a feasible $500 account claim.
- ONE_MICRO_200: chronological $500 account, 1 micro, assumed $200 margin.
- RISK_SIZED_200: largest whole quantity q with q*L<=75 and q*(margin+L)<=equity.
- RISK_SIZED_400: same, assumed $400 margin stress.
- RISK_SIZED_4763: same, current full-initial-margin proxy stress, $4,763.
All account scenarios reserve the complete planned stop loss in addition to margin.
No rule changes or target/stop grid. Slippage can change first eligible selection.
A hypothetical margin breach from unrealized adverse movement is flagged; no
invented broker liquidation price. Such a breach ends the account's certified
path and prevents unqualified subsequent-account claims. Any missing owned minute
also ends the account's known path: subsequent equity/returns NULL, not zero, and
no later trades simulated on unknown capital. A diagnostic missing outcome is
recorded unknown; other dates remain separately measurable. No fabricated minutes.

## Margin source and limits

Accessed 2026-10-10: https://www.webull.com/trading-investing/futures
Official product table retrieved with MNQ initial 4763.00 / intraday 166.71.
https://www.webull.com/futures-margin-rates returned 503 directly; search cache
showed a different 161.82. These are variable/current quotes, NOT a 2020–2023
historical margin series. Primary $200 is an explicitly assumed rounded scenario,
not a verified broker rate. $400 and $4763 test fragility only. Intraday eligibility,
margin changes, real liquidation timing and account-specific permissions remain
unverified. Do not claim live or historical Webull affordability from these tests.

## Evidence / gate frozen in advance

Record every hypothesis/scenario, raw/rejected/selected signals, all daily statuses,
all costs, wins/losses, 2R hits, daily average including zero days, yearly results,
closed and adverse-intratrade drawdown, capital lockout, >$75 losses and costs.
Account average after an unknown path is unavailable, not estimated by dropping
unknown days. All four years shown. No automatic deployment or Validation run.

Promising DEVELOPMENT candidate gate: complete primary RISK_SIZED_200 path;
positive net and positive average net R; PF>1; positive yearly daily-average
net in at least 3/4 years; no one year >50% of sum of positive yearly profits;
positive lower 95% calendar-month block bootstrap CI for ONE_MICRO_DIAGNOSTIC
mean daily net and Holm-adjusted one-sided centered bootstrap p<.05 over exactly
3 hypotheses (5,000 draws, seed 1729); no unknown execution, margin-breach or
terminal inability to afford a minimum tick-risk trade in primary account.
Objective met additionally requires >=100 net per ALL full session days, not
just active days. A gate pass is still only a proposed later Validation test.
Margin stress, yearly/direction/subgroup analyses are secondary descriptive,
not fresh independent discoveries or grounds to rewrite frozen eligibility.
