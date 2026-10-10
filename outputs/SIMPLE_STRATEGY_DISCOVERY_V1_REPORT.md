# Simple MNQ strategy search · $500 account / $75 risk

**DEVELOPMENT_ONLY_NOT_VALIDATED**. Three preregistered candle patterns, four Development years. No strategy tuning after inspection. No claim of an exhaustive search.

## Objective

Average at least $100 net per full trading session, including losing/no-trade/lockout days, at most one entry daily. No deposits. $75 planned all-in risk, whole-contract sizing, structural stop, fixed 2R.

## Primary risk-sized accounts ($200 assumed margin)

| hypothesis | days | trades | avg_daily_net | known_net_usd | ending_balance | net_pf | max_closed_dd | lockout_days | unknown_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INSIDE_BREAK | 1000 | 76 | -0.300 | -299.940 | 200.060 | 0.884 | 646.800 | 884 | 0 |
| OUTSIDE_REVERSAL | 1000 | 35 | -0.299 | -298.620 | 201.380 | 0.702 | 364.900 | 957 | 0 |
| TWO_PUSH | 1000 | 15 | -0.300 | -299.700 | 200.300 | 0.361 | 384.980 | 973 | 0 |

## One-micro accounts ($200 assumed margin)

| hypothesis | days | trades | avg_daily_net | known_net_usd | ending_balance | net_pf | max_closed_dd | lockout_days | unknown_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INSIDE_BREAK | 1000 | 77 | -0.299 | -299.420 | 200.580 | 0.876 | 630.960 | 884 | 0 |
| OUTSIDE_REVERSAL | 1000 | 36 | -0.298 | -297.560 | 202.440 | 0.664 | 387.360 | 961 | 0 |
| TWO_PUSH | 1000 | 950 | 1.245 | 1,245.000 | 1,745.000 | 1.035 | 3,318.600 | 0 | 0 |

## One-micro diagnostic without capital constraints

| hypothesis | days | trades | avg_daily_net | known_net_usd | ending_balance | net_pf | max_closed_dd | lockout_days | unknown_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INSIDE_BREAK | 1000 | 765 | -3.669 | -3,669.400 | -3,169.400 | 0.860 | 4,457.640 | 0 | 0 |
| OUTSIDE_REVERSAL | 1000 | 820 | -4.170 | -4,169.700 | -3,669.700 | 0.847 | 4,324.440 | 0 | 0 |
| TWO_PUSH | 1000 | 950 | 1.245 | 1,245.000 | 1,745.000 | 1.035 | 3,318.600 | 0 | 0 |

The diagnostic is not a feasible $500 account result. Zero days stay in every complete average. Unknown paths are NULL rather than silently removed. Closed drawdown does not represent worst intratrade account stress; see complete CSV.


## Every registered hypothesis

| hypothesis | raw_signals | dates |
| --- | --- | --- |
| INSIDE_BREAK | 3212 | 959 |
| OUTSIDE_REVERSAL | 2725 | 929 |
| TWO_PUSH | 12994 | 1000 |

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


## Every primary year

| hypothesis | year | days | trades | avg_daily_net | known_net_usd | net_pf | lockout_days | unknown_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INSIDE_BREAK | 2020 | 251 | 76 | -1.195 | -299.940 | 0.884 | 135 | 0 |
| INSIDE_BREAK | 2021 | 251 | 0 | 0.000 | 0.000 | — | 251 | 0 |
| INSIDE_BREAK | 2022 | 250 | 0 | 0.000 | 0.000 | — | 250 | 0 |
| INSIDE_BREAK | 2023 | 248 | 0 | 0.000 | 0.000 | — | 248 | 0 |
| OUTSIDE_REVERSAL | 2020 | 251 | 35 | -1.190 | -298.620 | 0.702 | 208 | 0 |
| OUTSIDE_REVERSAL | 2021 | 251 | 0 | 0.000 | 0.000 | — | 251 | 0 |
| OUTSIDE_REVERSAL | 2022 | 250 | 0 | 0.000 | 0.000 | — | 250 | 0 |
| OUTSIDE_REVERSAL | 2023 | 248 | 0 | 0.000 | 0.000 | — | 248 | 0 |
| TWO_PUSH | 2020 | 251 | 15 | -1.194 | -299.700 | 0.361 | 224 | 0 |
| TWO_PUSH | 2021 | 251 | 0 | 0.000 | 0.000 | — | 251 | 0 |
| TWO_PUSH | 2022 | 250 | 0 | 0.000 | 0.000 | — | 250 | 0 |
| TWO_PUSH | 2023 | 248 | 0 | 0.000 | 0.000 | — | 248 | 0 |

## Diagnostic yearly results

| hypothesis | year | days | trades | avg_daily_net | known_net_usd | net_pf | avg_net_r |
| --- | --- | --- | --- | --- | --- | --- | --- |
| INSIDE_BREAK | 2020 | 251 | 205 | -2.637 | -661.800 | 0.901 | -0.037 |
| INSIDE_BREAK | 2021 | 251 | 215 | -4.982 | -1,250.400 | 0.824 | -0.125 |
| INSIDE_BREAK | 2022 | 250 | 140 | -5.822 | -1,455.400 | 0.743 | -0.168 |
| INSIDE_BREAK | 2023 | 248 | 205 | -1.217 | -301.800 | 0.955 | -0.071 |
| OUTSIDE_REVERSAL | 2020 | 251 | 210 | -10.779 | -2,705.600 | 0.626 | -0.248 |
| OUTSIDE_REVERSAL | 2021 | 251 | 213 | -2.149 | -539.480 | 0.918 | -0.081 |
| OUTSIDE_REVERSAL | 2022 | 250 | 184 | -0.117 | -29.140 | 0.996 | -0.015 |
| OUTSIDE_REVERSAL | 2023 | 248 | 213 | -3.611 | -895.480 | 0.868 | -0.060 |
| TWO_PUSH | 2020 | 251 | 236 | 14.751 | 3,702.440 | 1.503 | 0.250 |
| TWO_PUSH | 2021 | 251 | 247 | 1.121 | 281.380 | 1.032 | 0.032 |
| TWO_PUSH | 2022 | 250 | 220 | -9.167 | -2,291.700 | 0.762 | -0.169 |
| TWO_PUSH | 2023 | 248 | 247 | -1.803 | -447.120 | 0.953 | -0.050 |

## Registered evidence family

| hypothesis | ci_low | ci_high | p_value | holm_p | evidence_status |
| --- | --- | --- | --- | --- | --- |
| TWO_PUSH | -3.498 | 5.983 | 0.302 | 0.906 | COMPLETE |
| OUTSIDE_REVERSAL | -7.271 | -1.148 | 0.996 | 1 | COMPLETE |
| INSIDE_BREAK | -7.563 | 0.277 | 0.968 | 1 | COMPLETE |

Calendar-month block bootstrap (5,000 draws, seed 1729), ONE_MICRO_DIAGNOSTIC mean net/day. One-sided centered bootstrap p and Holm adjustment across exactly three hypotheses. Previously inspected Development is not independent new evidence.


## Frozen qualification gates

```json
[
  {
    "hypothesis": "TWO_PUSH",
    "status": "DOES_NOT_QUALIFY",
    "positive_years": 0,
    "largest_positive_year_share": null,
    "checks": {
      "complete": true,
      "positive_net": false,
      "positive_r": false,
      "pf_above_one": false,
      "positive_three_years": false,
      "no_single_year_dominance": false,
      "positive_ci": false,
      "holm_significant": false,
      "no_margin_breach": true,
      "no_terminal_lockout": false
    },
    "average_daily_objective_met": false
  },
  {
    "hypothesis": "OUTSIDE_REVERSAL",
    "status": "DOES_NOT_QUALIFY",
    "positive_years": 0,
    "largest_positive_year_share": null,
    "checks": {
      "complete": true,
      "positive_net": false,
      "positive_r": false,
      "pf_above_one": false,
      "positive_three_years": false,
      "no_single_year_dominance": false,
      "positive_ci": false,
      "holm_significant": false,
      "no_margin_breach": true,
      "no_terminal_lockout": false
    },
    "average_daily_objective_met": false
  },
  {
    "hypothesis": "INSIDE_BREAK",
    "status": "DOES_NOT_QUALIFY",
    "positive_years": 0,
    "largest_positive_year_share": null,
    "checks": {
      "complete": true,
      "positive_net": false,
      "positive_r": true,
      "pf_above_one": false,
      "positive_three_years": false,
      "no_single_year_dominance": false,
      "positive_ci": false,
      "holm_significant": false,
      "no_margin_breach": true,
      "no_terminal_lockout": false
    },
    "average_daily_objective_met": false
  }
]
```

## All costs and margin scenarios — not an optimization grid

| hypothesis | mode | ticks | trades | avg_daily_net | ending_balance | net_pf | lockout_days | unknown_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INSIDE_BREAK | ONE_MICRO_200 | 0 | 155 | -0.299 | 200.700 | 0.939 | 792 | 0 |
| INSIDE_BREAK | ONE_MICRO_DIAGNOSTIC | 0 | 768 | -2.082 | -1,581.780 | 0.919 | 0 | 0 |
| INSIDE_BREAK | RISK_SIZED_200 | 0 | 152 | -0.294 | 205.840 | 0.947 | 0 | 0 |
| INSIDE_BREAK | RISK_SIZED_400 | 0 | 15 | -0.097 | 402.600 | 0.606 | 975 | 0 |
| INSIDE_BREAK | RISK_SIZED_4763 | 0 | 0 | 0.000 | 500.000 | — | 1000 | 0 |
| INSIDE_BREAK | ONE_MICRO_200 | 1 | 77 | -0.299 | 200.580 | 0.876 | 884 | 0 |
| INSIDE_BREAK | ONE_MICRO_DIAGNOSTIC | 1 | 765 | -3.669 | -3,169.400 | 0.860 | 0 | 0 |
| INSIDE_BREAK | RISK_SIZED_200 | 1 | 76 | -0.300 | 200.060 | 0.884 | 884 | 0 |
| INSIDE_BREAK | RISK_SIZED_400 | 1 | 12 | -0.088 | 411.980 | 0.587 | 0 | 0 |
| INSIDE_BREAK | RISK_SIZED_4763 | 1 | 0 | 0.000 | 500.000 | — | 1000 | 0 |
| INSIDE_BREAK | ONE_MICRO_200 | 2 | 74 | -0.284 | 215.960 | 0.877 | 0 | 0 |
| INSIDE_BREAK | ONE_MICRO_DIAGNOSTIC | 2 | 758 | -4.343 | -3,843.180 | 0.835 | 0 | 0 |
| INSIDE_BREAK | RISK_SIZED_200 | 2 | 70 | -0.298 | 202.320 | 0.878 | 671 | 0 |
| INSIDE_BREAK | RISK_SIZED_400 | 2 | 5 | -0.099 | 401.200 | 0.218 | 992 | 0 |
| INSIDE_BREAK | RISK_SIZED_4763 | 2 | 0 | 0.000 | 500.000 | — | 1000 | 0 |
| OUTSIDE_REVERSAL | ONE_MICRO_200 | 0 | 37 | -0.299 | 200.980 | 0.661 | 920 | 0 |
| OUTSIDE_REVERSAL | ONE_MICRO_DIAGNOSTIC | 0 | 827 | -3.108 | -2,607.920 | 0.885 | 0 | 0 |
| OUTSIDE_REVERSAL | RISK_SIZED_200 | 0 | 35 | -0.299 | 200.600 | 0.661 | 957 | 0 |
| OUTSIDE_REVERSAL | RISK_SIZED_400 | 0 | 6 | -0.092 | 407.740 | 0.340 | 0 | 0 |
| OUTSIDE_REVERSAL | RISK_SIZED_4763 | 0 | 0 | 0.000 | 500.000 | — | 1000 | 0 |
| OUTSIDE_REVERSAL | ONE_MICRO_200 | 1 | 36 | -0.298 | 202.440 | 0.664 | 961 | 0 |
| OUTSIDE_REVERSAL | ONE_MICRO_DIAGNOSTIC | 1 | 820 | -4.170 | -3,669.700 | 0.847 | 0 | 0 |
| OUTSIDE_REVERSAL | RISK_SIZED_200 | 1 | 35 | -0.299 | 201.380 | 0.702 | 957 | 0 |
| OUTSIDE_REVERSAL | RISK_SIZED_400 | 1 | 6 | -0.097 | 403.240 | 0.332 | 993 | 0 |
| OUTSIDE_REVERSAL | RISK_SIZED_4763 | 1 | 0 | 0.000 | 500.000 | — | 1000 | 0 |
| OUTSIDE_REVERSAL | ONE_MICRO_200 | 2 | 41 | -0.288 | 211.640 | 0.717 | 0 | 0 |
| OUTSIDE_REVERSAL | ONE_MICRO_DIAGNOSTIC | 2 | 815 | -5.386 | -4,885.900 | 0.806 | 0 | 0 |
| OUTSIDE_REVERSAL | RISK_SIZED_200 | 2 | 35 | -0.299 | 201.340 | 0.704 | 957 | 0 |
| OUTSIDE_REVERSAL | RISK_SIZED_400 | 2 | 6 | -0.096 | 404.240 | 0.336 | 993 | 0 |
| OUTSIDE_REVERSAL | RISK_SIZED_4763 | 2 | 0 | 0.000 | 500.000 | — | 1000 | 0 |
| TWO_PUSH | ONE_MICRO_200 | 0 | 954 | 1.935 | 2,434.660 | 1.055 | 0 | 0 |
| TWO_PUSH | ONE_MICRO_DIAGNOSTIC | 0 | 954 | 1.935 | 2,434.660 | 1.055 | 0 | 0 |
| TWO_PUSH | RISK_SIZED_200 | 0 | 954 | 1.876 | 2,376.480 | 1.051 | 0 | 0 |
| TWO_PUSH | RISK_SIZED_400 | 0 | 10 | -0.091 | 408.900 | 0.575 | 0 | 0 |
| TWO_PUSH | RISK_SIZED_4763 | 0 | 0 | 0.000 | 500.000 | — | 1000 | 0 |
| TWO_PUSH | ONE_MICRO_200 | 1 | 950 | 1.245 | 1,745.000 | 1.035 | 0 | 0 |
| TWO_PUSH | ONE_MICRO_DIAGNOSTIC | 1 | 950 | 1.245 | 1,745.000 | 1.035 | 0 | 0 |
| TWO_PUSH | RISK_SIZED_200 | 1 | 15 | -0.300 | 200.300 | 0.361 | 973 | 0 |
| TWO_PUSH | RISK_SIZED_400 | 1 | 10 | -0.098 | 401.900 | 0.558 | 990 | 0 |
| TWO_PUSH | RISK_SIZED_4763 | 1 | 0 | 0.000 | 500.000 | — | 1000 | 0 |
| TWO_PUSH | ONE_MICRO_200 | 2 | 941 | -0.288 | 211.640 | 0.992 | 0 | 0 |
| TWO_PUSH | ONE_MICRO_DIAGNOSTIC | 2 | 948 | -0.013 | 486.920 | 1.000 | 0 | 0 |
| TWO_PUSH | RISK_SIZED_200 | 2 | 17 | -0.294 | 206.340 | 0.421 | 983 | 0 |
| TWO_PUSH | RISK_SIZED_400 | 2 | 9 | -0.092 | 407.860 | 0.510 | 0 | 0 |
| TWO_PUSH | RISK_SIZED_4763 | 2 | 0 | 0.000 | 500.000 | — | 1000 | 0 |

## Operational caveats

Current Webull quote snapshot is not historical margin or account approval. The $200 primary margin is a scenario assumption; larger-margin cases are stress tests. Broker discretionary liquidation cannot be reproduced from OHLC. Stops can gap beyond $75. Missing owned minutes terminate known account paths; no made-up P&L or replenishment. No post-target or future-label information decides entries. At most one daily trade is enforced separately for each independently funded scenario. These scenarios must not be added together as a portfolio. Futures metadata, normal database and previous studies remain unchanged. No Validation or OOS outcomes accessed.

## Reproduce

Run `scripts/simple_discovery/run.py`, `report.py`, and `verify.py` with work/.venv/bin/python. Local protocol and source identities are required. Run/report/verify twice for byte equivalence. Raw local artifacts remain ignored by Git.
