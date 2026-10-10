# Separate timing follow-up

DEVELOPMENT_ONLY_NOT_VALIDATED. Native fixed-stop/session-close exits; one micro.

| hypothesis | ticks | trades | net_usd | pf | avg_net_r | max_dd | unknown_days |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LAST30_OVERNIGHT | 0 | 996 | -4,221.160 | 0.836 | -0.208 | 5,985.160 | 0 |
| LAST30_OVERNIGHT | 1 | 996 | -5,217.160 | 0.802 | -0.240 | 6,806.160 | 0 |
| LAST30_OVERNIGHT | 2 | 996 | -6,213.160 | 0.770 | -0.271 | 7,627.160 | 0 |
| LAST30_RTH | 0 | 994 | -1,141.240 | 0.951 | -0.135 | 2,287.080 | 0 |
| LAST30_RTH | 1 | 994 | -2,135.240 | 0.912 | -0.171 | 3,093.240 | 0 |
| LAST30_RTH | 2 | 994 | -3,129.240 | 0.874 | -0.205 | 4,012.240 | 0 |

| hypothesis | year | trades | net_usd | pf | avg_net_r |
| --- | --- | --- | --- | --- | --- |
| LAST30_OVERNIGHT | 2020 | 247 | -160.120 | 0.976 | 0.001 |
| LAST30_OVERNIGHT | 2021 | 251 | -1,715.960 | 0.663 | -0.467 |
| LAST30_OVERNIGHT | 2022 | 250 | -1,586.500 | 0.816 | -0.283 |
| LAST30_OVERNIGHT | 2023 | 248 | -1,754.580 | 0.708 | -0.208 |
| LAST30_RTH | 2020 | 246 | 272.340 | 1.047 | -0.015 |
| LAST30_RTH | 2021 | 251 | -1,531.460 | 0.717 | -0.329 |
| LAST30_RTH | 2022 | 250 | 462.000 | 1.063 | -0.165 |
| LAST30_RTH | 2023 | 247 | -1,338.120 | 0.764 | -0.172 |

| policy | ci_low | ci_high | p_value | holm_p_20 |
| --- | --- | --- | --- | --- |
| LAST30_RTH | -5.921 | 1.896 | 0.855 | 1 |
| LAST30_OVERNIGHT | -9.381 | -0.944 | 0.993 | 1 |

```json
[
  {
    "hypothesis": "LAST30_RTH",
    "status": "DOES_NOT_QUALIFY",
    "checks": {
      "complete": true,
      "positive_net": false,
      "positive_r": false,
      "pf": false,
      "sample": true,
      "years": false,
      "concentration": false,
      "top5": false,
      "stress": false,
      "ci": false,
      "adjusted_p": false
    }
  },
  {
    "hypothesis": "LAST30_OVERNIGHT",
    "status": "DOES_NOT_QUALIFY",
    "checks": {
      "complete": true,
      "positive_net": false,
      "positive_r": false,
      "pf": false,
      "sample": true,
      "years": false,
      "concentration": false,
      "top5": false,
      "stress": false,
      "ci": false,
      "adjusted_p": false
    }
  }
]
```

# Separately registered timing follow-up

DEVELOPMENT_ONLY_NOT_VALIDATED. This is a later exploratory family, not part of
or an amendment to the frozen twelve-policy study. Rationale is external to its
results: Gao, Han, Li and Zhou, Market Intraday Momentum,
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866 (accessed2026-10-10),
studied S&P500ETF morning-to-final-half-hour predictability. Their overnight-
inclusive return definition differs from simply measuring from today's open.
This is an MNQ adaptation with a structuralstop, not an exact paper replication.
No evidence of ETF results is assumed to transfer to MNQ.

Two definitions only:
1. LAST30_RTH: direction is sign of today's09:55bar close minus09:30bar open.
2. LAST30_OVERNIGHT: direction is sign of today's09:55bar close minus the immediately
   prior XNYSsession's final5m close. Missing previoussession close => no signal.

Require all6opening5mbars complete and contiguous. Enter at15:30 on the confirmed
15:25candle close, long forpositive signal, short fornegative, no trade forzero.
The6complete15:00–15:30bars set stop: their lowestlow−.25 long, highesthigh+.25 short.
No profit target. Exit at stop or16:00, via existing no-target PositionPlan.
No management. No timeframe, entrytime, stopwidth or target optimization.
Full XNYSsessions only; one micro; actual.73fees/side;1adversetick/side primary,
0/2coststress. No account or dollar-risk cap. Development2020–2023 only.
All1000fullsessions count in averages. No future missingness entry filter.

Same evidence gates as the unrestricted search, adjusted over ALL20policies:
6previouscapped+12unrestricted+2timing. Calendar-monthbootstrap5000draws seed1729.
No later period accessed. Everyfailedhypothesis retained. No automatic additional
family after this follow-up. A pass remains only PROMISING_DEVELOPMENT_ONLY.
