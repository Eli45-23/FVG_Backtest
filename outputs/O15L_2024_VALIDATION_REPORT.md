# O15L clearance-and-hold: 2024 Validation

**VALIDATION_GATE_FAILED**

Unchanged full-session setup. Root O15L upward break, frozen nearby-level clearance then full hold. Original root low minus one tick stop, fixed 1R target, one micro, one position at a time. No 10:30 filter and no stop management. Includes actual XNYS early closes. All-in fees $0.73 per side; primary one adverse tick each side.

## Results

| ticks | trades | unique_dates | wins | losses | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r | gross_usd | fees_usd | POSITION_OPEN | AT_SESSION_CLOSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 69 | 63 | 28 | 41 | 40.580 | -1,502.240 | 0.686 | -0.205 | 2,221.780 | 15.674 | -1,401.500 | 100.740 | — | 2 |
| 1 | 69 | 63 | 28 | 41 | 40.580 | -1,552.240 | 0.678 | -0.210 | 2,253.780 | 15.873 | -1,451.500 | 100.740 | — | 2 |
| 2 | 69 | 63 | 28 | 41 | 40.580 | -1,602.240 | 0.670 | -0.215 | 2,285.780 | 16.068 | -1,501.500 | 100.740 | — | 2 |

Raw upward roots: 378; obstacle opportunities: 216; causal hold confirmations: 71. Unresolved execution rows: 0.

## Preregistered decision

| criterion | passed |
| --- | --- |
| integrity | True |
| sample | True |
| net_usd_positive | False |
| mean_net_r_positive | False |
| net_pf_above_one | False |
| r_drawdown | False |
| mean_r_lower_ci_positive | False |

Minimum 30 trades / 30 dates; net USD > 0, mean net R > 0, PF > 1, max closed R drawdown <= 7.031524868463503. Positive lower 95% date-cluster mean-R bound is required for full support; otherwise positive economics alone are conditional. Sensitivity cases cannot rescue a failing primary. These thresholds were committed before this task read 2024 bars.

{"mean_r_ci_high": -0.004329640522665328, "mean_r_ci_low": -0.4231825873249316, "mean_usd_ci_high": 10.964298128342238, "mean_usd_ci_low": -57.30064764492756}

The percentile bootstrap resamples NY dates 5,000 times, seed 1729. This single frozen candidate was selected using Development; Validation outcomes cannot now be used to adjust rules while retaining the same validation claim. 2024 was previously inspected by unrelated project research, so it is not universally untouched market history.

## Quarterly

| quarter | trades | unique_dates | wins | losses | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024Q1 | 21 | 19 | 5 | 16 | 23.810 | -1,213.660 | 0.279 | -0.521 | 1,238.240 | 10.932 |
| 2024Q2 | 18 | 15 | 8 | 10 | 44.444 | -666.280 | 0.527 | -0.206 | 1,162.520 | 7.889 |
| 2024Q3 | 17 | 16 | 12 | 5 | 70.588 | 1,046.180 | 2.349 | 0.285 | 523.420 | 2.039 |
| 2024Q4 | 13 | 13 | 3 | 10 | 23.077 | -718.480 | 0.247 | -0.363 | 729.100 | 5.335 |

## Monthly

| month | trades | unique_dates | wins | losses | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-01 | 6 | 5 | 1 | 5 | 16.667 | -595.760 | 0.136 | -0.686 | 595.760 | 4.119 |
| 2024-02 | 8 | 7 | 3 | 5 | 37.500 | -126.180 | 0.675 | -0.207 | 236.840 | 2.174 |
| 2024-03 | 7 | 7 | 1 | 6 | 14.286 | -491.720 | 0.188 | -0.736 | 516.300 | 5.154 |
| 2024-04 | 3 | 3 | 3 | 0 | 100.000 | 391.620 | — | 0.983 | 0.000 | 0.000 |
| 2024-05 | 12 | 9 | 3 | 9 | 25.000 | -1,162.520 | 0.142 | -0.657 | 1,162.520 | 7.889 |
| 2024-06 | 3 | 3 | 2 | 1 | 66.667 | 104.620 | 2.957 | 0.408 | 53.460 | 0.727 |
| 2024-07 | 5 | 4 | 3 | 2 | 60.000 | -152.300 | 0.709 | 0.049 | 523.420 | 2.017 |
| 2024-08 | 4 | 4 | 3 | 1 | 75.000 | 419.160 | 14.761 | 0.571 | 30.460 | 0.119 |
| 2024-09 | 8 | 8 | 6 | 2 | 75.000 | 779.320 | 4.520 | 0.289 | 221.420 | 2.039 |
| 2024-10 | 5 | 5 | 1 | 4 | 20.000 | -377.300 | 0.204 | -0.563 | 377.300 | 2.813 |
| 2024-11 | 3 | 3 | 1 | 2 | 33.333 | -135.380 | 0.109 | -0.446 | 151.920 | 1.438 |
| 2024-12 | 5 | 5 | 1 | 4 | 20.000 | -205.800 | 0.372 | -0.113 | 216.420 | 1.183 |

## Entry time — descriptive, no selected time filter

| time_bucket | trades | unique_dates | wins | losses | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10:00–10:29 | 8 | 8 | 3 | 5 | 37.500 | -34.680 | 0.941 | -0.130 | 212.840 | 1.175 |
| 10:30–10:59 | 13 | 13 | 4 | 9 | 30.769 | -611.480 | 0.475 | -0.387 | 705.520 | 6.015 |
| 11:00–11:59 | 12 | 12 | 7 | 5 | 58.333 | 41.480 | 1.063 | 0.162 | 357.840 | 1.015 |
| 12:00–13:59 | 25 | 25 | 12 | 13 | 48.000 | 139.500 | 1.124 | -0.165 | 429.640 | 5.759 |
| 14:00–15:59 | 11 | 11 | 2 | 9 | 18.182 | -1,087.060 | 0.153 | -0.569 | 1,210.180 | 7.049 |

## Risk and execution

{"risk_quantiles": {"0.0": 23.75, "0.25": 42.5, "0.5": 63.5, "0.75": 88.0, "1.0": 271.75}, "top5_risk_net": -376.3000000000001}

Risk concentration is descriptive; no trades removed. One-minute stop-first ordering, adverse gaps and strict missing owned minutes use the existing executor. Full exit-minute extrema enter MFE/MAE; intraminute order is unknown. Closed drawdown excludes unrealized exposure and is not a future maximum-loss guarantee.

## Preservation and evidence

Portable detector exactly reproduced 280 Development confirmations and 865 waiting opportunities. All three Development scenarios reproduced the same 273 sequential trades and exact serialized economic fields before Validation access. OOS (2025+) was not decoded or revealed. Old study artifacts and normal database records were not modified. Complete trades, audits, code/source hashes, access ledger and deterministic checks are retained locally. No automatic OOS run or live deployment.
