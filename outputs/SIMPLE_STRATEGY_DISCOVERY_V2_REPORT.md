# Simple strategy search — second batch

DEVELOPMENT_ONLY_NOT_VALIDATED. No tuning after results.

No new strategy passed the frozen evidence/account gate.


## ONE_MICRO_DIAGNOSTIC

| hypothesis | trades | known_net_usd | avg_daily_net | net_pf | avg_net_r | ending_balance | max_closed_dd | lockout_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PULLBACK_RESUME | 750 | -2,684.500 | -2.684 | 0.885 | -0.084 | -2,184.500 | 3,531.620 | 0 |
| RANGE_FAILURE | 1000 | -2,860.500 | -2.860 | 0.888 | -0.126 | -2,360.500 | 4,018.320 | 0 |
| THREE_BAR_BREAK | 890 | 1,019.600 | 1.020 | 1.029 | 0.012 | 1,519.600 | 2,616.300 | 0 |


## ONE_MICRO_200

| hypothesis | trades | known_net_usd | avg_daily_net | net_pf | avg_net_r | ending_balance | max_closed_dd | lockout_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PULLBACK_RESUME | 71 | -299.160 | -0.299 | 0.856 | -0.019 | 200.840 | 464.360 | 906 |
| RANGE_FAILURE | 291 | -297.360 | -0.297 | 0.955 | -0.118 | 202.640 | 1,327.500 | 709 |
| THREE_BAR_BREAK | 15 | -293.400 | -0.293 | 0.454 | -0.582 | 206.600 | 322.560 | 0 |


## RISK_SIZED_200

| hypothesis | trades | known_net_usd | avg_daily_net | net_pf | avg_net_r | ending_balance | max_closed_dd | lockout_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PULLBACK_RESUME | 15 | -292.740 | -0.293 | 0.307 | -0.563 | 207.260 | 340.820 | 0 |
| RANGE_FAILURE | 36 | -299.320 | -0.299 | 0.456 | -0.420 | 200.680 | 327.400 | 962 |
| THREE_BAR_BREAK | 14 | -294.900 | -0.295 | 0.452 | -0.548 | 205.100 | 324.060 | 986 |


## Every diagnostic year

| hypothesis | year | trades | known_net_usd | net_pf | avg_net_r |
| --- | --- | --- | --- | --- | --- |
| PULLBACK_RESUME | 2020 | 207 | -1,875.720 | 0.713 | -0.149 |
| PULLBACK_RESUME | 2021 | 191 | -662.860 | 0.879 | -0.129 |
| PULLBACK_RESUME | 2022 | 167 | -658.320 | 0.893 | -0.099 |
| PULLBACK_RESUME | 2023 | 185 | 512.400 | 1.097 | 0.047 |
| RANGE_FAILURE | 2020 | 251 | 119.040 | 1.022 | -0.084 |
| RANGE_FAILURE | 2021 | 251 | -1,424.960 | 0.773 | -0.172 |
| RANGE_FAILURE | 2022 | 250 | -576.500 | 0.923 | -0.120 |
| RANGE_FAILURE | 2023 | 248 | -978.080 | 0.847 | -0.127 |
| THREE_BAR_BREAK | 2020 | 221 | 1,271.840 | 1.154 | 0.075 |
| THREE_BAR_BREAK | 2021 | 235 | 745.400 | 1.085 | 0.045 |
| THREE_BAR_BREAK | 2022 | 190 | -1,443.900 | 0.825 | -0.128 |
| THREE_BAR_BREAK | 2023 | 244 | 446.260 | 1.047 | 0.033 |


## Combined evidence across both batches

| hypothesis | ci_low | ci_high | p_value | holm_p_six |
| --- | --- | --- | --- | --- |
| TWO_PUSH | -3.498 | 5.983 | 0.302 | 1 |
| OUTSIDE_REVERSAL | -7.271 | -1.148 | 0.996 | 1 |
| INSIDE_BREAK | -7.563 | 0.277 | 0.968 | 1 |
| PULLBACK_RESUME | -5.742 | 0.389 | 0.955 | 1 |
| RANGE_FAILURE | -6.693 | 1.112 | 0.925 | 1 |
| THREE_BAR_BREAK | -3.887 | 5.987 | 0.345 | 1 |


Month-block bootstrap: mean net per all full sessions, 5,000 draws, seed1729. Six-hypothesis Holm correction. This does not correct for every historical research decision in this repository or make inspected Development data independent.


## All cost and margin scenarios

| hypothesis | mode | ticks | trades | known_net_usd | avg_daily_net | net_pf | lockout_days | unknown_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PULLBACK_RESUME | ONE_MICRO_200 | 0 | 20 | -299.200 | -0.299 | 0.382 | 976 | 0 |
| PULLBACK_RESUME | ONE_MICRO_DIAGNOSTIC | 0 | 755 | -1,737.300 | -1.737 | 0.925 | 0 | 0 |
| PULLBACK_RESUME | RISK_SIZED_200 | 0 | 16 | -297.700 | -0.298 | 0.303 | 982 | 0 |
| PULLBACK_RESUME | RISK_SIZED_400 | 0 | 7 | -99.720 | -0.100 | 0.266 | 983 | 0 |
| PULLBACK_RESUME | RISK_SIZED_4763 | 0 | 0 | 0.000 | 0.000 | — | 1000 | 0 |
| PULLBACK_RESUME | ONE_MICRO_200 | 1 | 71 | -299.160 | -0.299 | 0.856 | 906 | 0 |
| PULLBACK_RESUME | ONE_MICRO_DIAGNOSTIC | 1 | 750 | -2,684.500 | -2.684 | 0.885 | 0 | 0 |
| PULLBACK_RESUME | RISK_SIZED_200 | 1 | 15 | -292.740 | -0.293 | 0.307 | 0 | 0 |
| PULLBACK_RESUME | RISK_SIZED_400 | 1 | 5 | -94.800 | -0.095 | 0.202 | 994 | 0 |
| PULLBACK_RESUME | RISK_SIZED_4763 | 1 | 0 | 0.000 | 0.000 | — | 1000 | 0 |
| PULLBACK_RESUME | ONE_MICRO_200 | 2 | 18 | -295.280 | -0.295 | 0.346 | 980 | 0 |
| PULLBACK_RESUME | ONE_MICRO_DIAGNOSTIC | 2 | 740 | -3,352.400 | -3.352 | 0.857 | 0 | 0 |
| PULLBACK_RESUME | RISK_SIZED_200 | 2 | 16 | -298.240 | -0.298 | 0.304 | 982 | 0 |
| PULLBACK_RESUME | RISK_SIZED_400 | 2 | 5 | -98.300 | -0.098 | 0.200 | 994 | 0 |
| PULLBACK_RESUME | RISK_SIZED_4763 | 2 | 0 | 0.000 | 0.000 | — | 1000 | 0 |
| RANGE_FAILURE | ONE_MICRO_200 | 0 | 305 | -296.800 | -0.297 | 0.956 | 695 | 0 |
| RANGE_FAILURE | ONE_MICRO_DIAGNOSTIC | 0 | 1000 | -1,664.500 | -1.664 | 0.933 | 0 | 0 |
| RANGE_FAILURE | RISK_SIZED_200 | 0 | 38 | -299.740 | -0.300 | 0.456 | 946 | 0 |
| RANGE_FAILURE | RISK_SIZED_400 | 0 | 18 | -98.280 | -0.098 | 0.530 | 982 | 0 |
| RANGE_FAILURE | RISK_SIZED_4763 | 0 | 0 | 0.000 | 0.000 | — | 1000 | 0 |
| RANGE_FAILURE | ONE_MICRO_200 | 1 | 291 | -297.360 | -0.297 | 0.955 | 709 | 0 |
| RANGE_FAILURE | ONE_MICRO_DIAGNOSTIC | 1 | 1000 | -2,860.500 | -2.860 | 0.888 | 0 | 0 |
| RANGE_FAILURE | RISK_SIZED_200 | 1 | 36 | -299.320 | -0.299 | 0.456 | 962 | 0 |
| RANGE_FAILURE | RISK_SIZED_400 | 1 | 10 | -94.100 | -0.094 | 0.409 | 990 | 0 |
| RANGE_FAILURE | RISK_SIZED_4763 | 1 | 0 | 0.000 | 0.000 | — | 1000 | 0 |
| RANGE_FAILURE | ONE_MICRO_200 | 2 | 36 | -299.560 | -0.300 | 0.429 | 964 | 0 |
| RANGE_FAILURE | ONE_MICRO_DIAGNOSTIC | 2 | 1000 | -3,434.000 | -3.434 | 0.869 | 0 | 0 |
| RANGE_FAILURE | RISK_SIZED_200 | 2 | 32 | -299.520 | -0.300 | 0.445 | 967 | 0 |
| RANGE_FAILURE | RISK_SIZED_400 | 2 | 16 | -98.360 | -0.098 | 0.513 | 984 | 0 |
| RANGE_FAILURE | RISK_SIZED_4763 | 2 | 0 | 0.000 | 0.000 | — | 1000 | 0 |
| THREE_BAR_BREAK | ONE_MICRO_200 | 0 | 16 | -299.860 | -0.300 | 0.450 | 982 | 0 |
| THREE_BAR_BREAK | ONE_MICRO_DIAGNOSTIC | 0 | 894 | 1,586.260 | 1.586 | 1.046 | 0 | 0 |
| THREE_BAR_BREAK | RISK_SIZED_200 | 0 | 894 | 1,158.660 | 1.159 | 1.033 | 0 | 0 |
| THREE_BAR_BREAK | RISK_SIZED_400 | 0 | 6 | -97.260 | -0.097 | 0.309 | 994 | 0 |
| THREE_BAR_BREAK | RISK_SIZED_4763 | 0 | 0 | 0.000 | 0.000 | — | 1000 | 0 |
| THREE_BAR_BREAK | ONE_MICRO_200 | 1 | 15 | -293.400 | -0.293 | 0.454 | 0 | 0 |
| THREE_BAR_BREAK | ONE_MICRO_DIAGNOSTIC | 1 | 890 | 1,019.600 | 1.020 | 1.029 | 0 | 0 |
| THREE_BAR_BREAK | RISK_SIZED_200 | 1 | 14 | -294.900 | -0.295 | 0.452 | 986 | 0 |
| THREE_BAR_BREAK | RISK_SIZED_400 | 1 | 3 | -98.880 | -0.099 | 0.000 | 996 | 0 |
| THREE_BAR_BREAK | RISK_SIZED_4763 | 1 | 0 | 0.000 | 0.000 | — | 1000 | 0 |
| THREE_BAR_BREAK | ONE_MICRO_200 | 2 | 36 | -296.560 | -0.297 | 0.755 | 911 | 0 |
| THREE_BAR_BREAK | ONE_MICRO_DIAGNOSTIC | 2 | 882 | 2,651.280 | 2.651 | 1.078 | 0 | 0 |
| THREE_BAR_BREAK | RISK_SIZED_200 | 2 | 14 | -295.900 | -0.296 | 0.450 | 986 | 0 |
| THREE_BAR_BREAK | RISK_SIZED_400 | 2 | 3 | -96.880 | -0.097 | 0.000 | 996 | 0 |
| THREE_BAR_BREAK | RISK_SIZED_4763 | 2 | 0 | 0.000 | 0.000 | — | 1000 | 0 |


## Frozen qualification checks

```json
[
  {
    "hypothesis": "PULLBACK_RESUME",
    "checks": {
      "complete": true,
      "positive_net": false,
      "positive_r": false,
      "pf_above_one": false,
      "three_positive_years": false,
      "no_year_dominance": false,
      "positive_ci": false,
      "adjusted_evidence": false,
      "no_margin_breach": true,
      "no_lockout": true
    },
    "status": "DOES_NOT_QUALIFY",
    "objective_met": false
  },
  {
    "hypothesis": "RANGE_FAILURE",
    "checks": {
      "complete": true,
      "positive_net": false,
      "positive_r": false,
      "pf_above_one": false,
      "three_positive_years": false,
      "no_year_dominance": false,
      "positive_ci": false,
      "adjusted_evidence": false,
      "no_margin_breach": true,
      "no_lockout": false
    },
    "status": "DOES_NOT_QUALIFY",
    "objective_met": false
  },
  {
    "hypothesis": "THREE_BAR_BREAK",
    "checks": {
      "complete": true,
      "positive_net": false,
      "positive_r": false,
      "pf_above_one": false,
      "three_positive_years": false,
      "no_year_dominance": false,
      "positive_ci": false,
      "adjusted_evidence": false,
      "no_margin_breach": true,
      "no_lockout": false
    },
    "status": "DOES_NOT_QUALIFY",
    "objective_met": false
  }
]
```


## Method and limits

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



The diagnostic ignores capital restrictions and is not a feasible account result. Scenario profits must not be summed. $200 margin is an assumption, not broker approval. Actual losses can exceed planned stop losses. These three additional tests do not exhaust simple strategies. No Validation/OOS outcomes were queried; native engine unchanged. All raw outputs remain local and preserved separately from v1.
