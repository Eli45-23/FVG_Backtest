# Market-structure continuation · fixed 2R

**DEVELOPMENT_ONLY_NOT_VALIDATED** · 2020–2023 · Standalone 5-minute structure, no key levels.

# Standalone market-structure continuation · frozen Development experiment v1

Status: DEVELOPMENT_ONLY_NOT_VALIDATED. Dataset research_2020_2026; New York dates
2020-01-01 inclusive through 2024-01-01 exclusive. No key-level or indicator filter.

## Signal contract

Each full XNYS RTH session starts with fresh structure. Exclude holidays/half-days.
Use complete consecutive 5-minute bars. Missing/incomplete bars reset detector state;
no bridging, synthetic candles, or overnight structure. Strict pivots use two bars
left and two right from the existing Structure provider. Equal extremes are not
pivots. A pivot becomes known at the second right-hand candle's close.

Long: latest confirmed low is HL versus the previous confirmed low, its formation
follows the latest confirmed high, both are available before the trigger candle
starts, and the first confirmed close breaks strictly above that high (previous
close at/below). Short mirrors this with LH and a break below the latest low.
No requirement that the high itself be HH or the low itself LL. No additional
BOS-state filter. The existing provider consumes the first close-break of a pivot
whether or not this entry qualifies; no deferred entry or recycled broken pivot.
Only new eligible swing breaks can create further entries.

Entry at breakout close plus one adverse tick (primary); one MNQ micro.
Stop one tick below HL for long / above LH for short. Fixed original 2R target
from executed entry, existing tick rounding. Reject nonpositive risk explicitly.
One position across both directions; busy signals logged, not queued. New entries
at session close rejected. Later distinct eligible setups allowed; no daily cap.
Stop/target/session close only. No trailing, breakeven or partial exits.

## Costs and timing

Primary one adverse tick per side. Zero/two tick sensitivity uses identical raw
signals but reselection is allowed as exit times differ. Actual user-supplied fees:
commission .25 + exchange .35 + clearing .12 + NFA .01 = $.73/side, $1.46 roundtrip.
Native unchanged 1-minute executor, stop first, adverse opening gaps, no synthetic
missing minutes. Trigger candle cannot fill its own newly created trade.

## Movement measurements

Report .5R/1R/1.5R/2R reached while a position is open, stop first in conflicting
minutes. Ambiguities listed separately. Conservative maximum R caps at the 2R
exit. Native MFE/MAE includes the full exit minute and may exceed 2R; intraminute
ordering is unknown and such excess is not evidence of attainable post-target
profits. No prices after exit are used for movement statistics.

Overall, direction, yearly, monthly, time-of-day, risk, equity and cost summaries.
Time/risk groups descriptive only; no selecting a best subgroup. Date-clustered
bootstrap intervals exploratory. No Validation/OOS outcome reads; prior records,
market data and production strategy/execution code unchanged.


## Signal accounting

1,584 causal signals across 841 dates. Every scenario retains selected and skipped reasons. Missing owned minutes invalidate execution reporting, not signal eligibility.

**Execution coverage: INCOMPLETE_EXECUTION**. One primary trade has an unknown outcome because the March 18, 2020 12:58 New York source minute is absent. It entered at 12:50; the missing minute is owned by the still-open trade. It remains in the signal audit, is excluded from completed-trade performance, and conservatively blocks further entries until session close. Tables and milestone denominators describe completed trades only, not a fully observed full-period result. No data was fabricated.


## Costs and overall results

| ticks | trades | unique_dates | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r | gross_usd | fees_usd | target_exits | stop_exits | session_exits | POSITION_OPEN | AT_SESSION_CLOSE | conflicts | adverse_stop_gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1098 | 836 | 43.443 | 7,314.420 | 1.132 | 0.044 | 2,659.140 | 27.853 | 8,917.500 | 1,603.080 | 199 | 498 | 401 | 450 | 35 | 0 | 0 |
| 1 | 1098 | 836 | 42.987 | 6,121.920 | 1.109 | 0.029 | 3,068.640 | 33.959 | 7,725.000 | 1,603.080 | 192 | 499 | 407 | 450 | 35 | 0 | 0 |
| 2 | 1097 | 836 | 42.844 | 5,305.880 | 1.094 | 0.019 | 3,377.180 | 38.890 | 6,907.500 | 1,601.620 | 190 | 499 | 408 | 451 | 35 | 0 | 0 |

## Yearly

| year | trades | unique_dates | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 266 | 216 | 44.737 | 2,658.140 | 1.219 | 0.126 | 1,615.660 | 15.907 |
| 2021 | 254 | 195 | 41.732 | -481.840 | 0.959 | -0.048 | 2,383.560 | 27.782 |
| 2022 | 285 | 213 | 44.912 | 5,108.900 | 1.272 | 0.092 | 1,645.720 | 15.393 |
| 2023 | 293 | 212 | 40.614 | -1,163.280 | 0.913 | -0.053 | 2,518.440 | 27.401 |

## Direction

| direction | trades | unique_dates | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LONG | 622 | 549 | 46.463 | 6,009.380 | 1.209 | 0.096 | 1,268.320 | 13.796 |
| SHORT | 476 | 427 | 38.445 | 112.540 | 1.004 | -0.058 | 3,649.040 | 42.411 |

## Year and direction

| year | direction | trades | unique_dates | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | LONG | 164 | 148 | 48.171 | 1,214.060 | 1.175 | 0.157 | 1,237.760 | 11.573 |
| 2020 | SHORT | 102 | 94 | 39.216 | 1,444.080 | 1.278 | 0.076 | 1,215.080 | 12.558 |
| 2021 | LONG | 135 | 117 | 46.667 | 950.900 | 1.193 | 0.048 | 681.520 | 11.060 |
| 2021 | SHORT | 119 | 108 | 36.134 | -1,432.740 | 0.787 | -0.157 | 2,040.320 | 23.406 |
| 2022 | LONG | 154 | 137 | 48.052 | 3,048.160 | 1.309 | 0.145 | 1,268.320 | 7.348 |
| 2022 | SHORT | 131 | 117 | 41.221 | 2,060.740 | 1.231 | 0.031 | 1,521.380 | 13.320 |
| 2023 | LONG | 169 | 147 | 43.195 | 796.260 | 1.113 | 0.031 | 1,031.280 | 13.796 |
| 2023 | SHORT | 124 | 108 | 37.097 | -1,959.540 | 0.693 | -0.168 | 2,571.940 | 23.736 |

## How far trades get before exit

| direction | threshold_r | trades | reached | reached_pct | ambiguous |
| --- | --- | --- | --- | --- | --- |
| ALL | 0.500 | 1098 | 682 | 62.113 | 0 |
| ALL | 1 | 1098 | 462 | 42.077 | 0 |
| ALL | 1.500 | 1098 | 301 | 27.413 | 0 |
| ALL | 2 | 1098 | 192 | 17.486 | 0 |
| LONG | 0.500 | 622 | 396 | 63.666 | 0 |
| LONG | 1 | 622 | 268 | 43.087 | 0 |
| LONG | 1.500 | 622 | 179 | 28.778 | 0 |
| LONG | 2 | 622 | 115 | 18.489 | 0 |
| SHORT | 0.500 | 476 | 286 | 60.084 | 0 |
| SHORT | 1 | 476 | 194 | 40.756 | 0 |
| SHORT | 1.500 | 476 | 122 | 25.630 | 0 |
| SHORT | 2 | 476 | 77 | 16.176 | 0 |

Stop-first counts exclude threshold touches in a stop minute unless already reached earlier. Ambiguous rows are not added to successes. Native MFE includes the complete exit minute; it is not evidence of an executable fill beyond 2R. No post-exit continuation study has been performed.


## Excursions and risk

| direction | trades | mfe_points_mean | mfe_points_median | mae_points_mean | mae_points_median | mfe_r_mean | mae_r_mean | risk_points_q25 | risk_points_median | risk_points_q75 | risk_points_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | 1098 | 49.010 | 33.750 | 37.957 | 32.500 | 0.950 | 0.743 | 32.750 | 46.000 | 64.938 | 234.500 |
| LONG | 622 | 45.994 | 32.875 | 35.458 | 29.250 | 0.980 | 0.739 | 28.812 | 42.000 | 60.250 | 206.250 |
| SHORT | 476 | 52.952 | 35.875 | 41.222 | 36.250 | 0.910 | 0.748 | 37.625 | 51.000 | 69.625 | 234.500 |

## Time of day — descriptive, not filters

| direction | time_bucket | trades | unique_dates | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | 09:30–09:59 | 0 | 0 | — | 0.000 | — | — | 0.000 | 0.000 |
| ALL | 10:00–10:29 | 6 | 6 | 50.000 | 95.240 | 1.179 | 0.128 | 531.380 | 3.037 |
| ALL | 10:30–10:59 | 70 | 70 | 44.286 | -33.700 | 0.994 | 0.051 | 1,871.560 | 10.282 |
| ALL | 11:00–11:59 | 278 | 278 | 41.367 | 2,425.620 | 1.140 | 0.057 | 1,906.040 | 14.806 |
| ALL | 12:00–13:59 | 396 | 382 | 43.182 | 3,747.840 | 1.195 | 0.061 | 1,661.540 | 20.552 |
| ALL | 14:00–15:59 | 348 | 331 | 43.678 | -113.080 | 0.992 | -0.035 | 1,789.420 | 17.027 |
| LONG | 09:30–09:59 | 0 | 0 | — | 0.000 | — | — | 0.000 | 0.000 |
| LONG | 10:00–10:29 | 5 | 5 | 60.000 | 204.200 | 1.483 | 0.358 | 422.420 | 2.019 |
| LONG | 10:30–10:59 | 38 | 38 | 44.737 | -114.480 | 0.959 | 0.025 | 1,443.100 | 8.668 |
| LONG | 11:00–11:59 | 143 | 143 | 46.154 | 2,942.220 | 1.383 | 0.127 | 708.040 | 6.849 |
| LONG | 12:00–13:59 | 237 | 235 | 47.257 | 2,375.480 | 1.229 | 0.140 | 1,222.840 | 15.157 |
| LONG | 14:00–15:59 | 199 | 197 | 45.729 | 601.960 | 1.080 | 0.028 | 903.040 | 8.123 |
| SHORT | 09:30–09:59 | 0 | 0 | — | 0.000 | — | — | 0.000 | 0.000 |
| SHORT | 10:00–10:29 | 1 | 1 | 0.000 | -108.960 | 0.000 | -1.018 | 108.960 | 1.018 |
| SHORT | 10:30–10:59 | 32 | 32 | 43.750 | 80.780 | 1.032 | 0.082 | 844.080 | 5.010 |
| SHORT | 11:00–11:59 | 135 | 135 | 36.296 | -516.600 | 0.946 | -0.017 | 1,655.120 | 15.230 |
| SHORT | 12:00–13:59 | 159 | 159 | 37.107 | 1,372.360 | 1.155 | -0.059 | 1,127.220 | 16.552 |
| SHORT | 14:00–15:59 | 149 | 148 | 40.940 | -715.040 | 0.884 | -0.119 | 1,366.280 | 17.884 |

## Monthly

| month | trades | unique_dates | win_pct | net_usd | profit_factor | avg_net_r | max_dd_usd | max_dd_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-01 | 16 | 16 | 56.250 | 300.640 | 2.417 | 0.415 | 73.420 | 2.177 |
| 2020-02 | 21 | 18 | 52.381 | 725.340 | 1.983 | 0.391 | 364.420 | 2.140 |
| 2020-03 | 27 | 20 | 40.741 | 184.580 | 1.063 | 0.025 | 1,144.360 | 6.759 |
| 2020-04 | 20 | 17 | 25.000 | -736.200 | 0.405 | -0.400 | 941.520 | 9.530 |
| 2020-05 | 23 | 16 | 30.435 | -118.080 | 0.886 | -0.190 | 344.220 | 5.488 |
| 2020-06 | 28 | 21 | 50.000 | 718.120 | 1.866 | 0.274 | 283.180 | 4.633 |
| 2020-07 | 27 | 21 | 48.148 | 507.080 | 1.460 | 0.234 | 573.640 | 5.128 |
| 2020-08 | 20 | 18 | 45.000 | 179.300 | 1.259 | 0.356 | 239.920 | 2.033 |
| 2020-09 | 17 | 16 | 29.412 | -128.320 | 0.883 | -0.108 | 475.680 | 4.306 |
| 2020-10 | 24 | 16 | 41.667 | -172.540 | 0.848 | -0.076 | 375.640 | 6.253 |
| 2020-11 | 22 | 19 | 68.182 | 1,107.380 | 3.073 | 0.495 | 231.380 | 2.465 |
| 2020-12 | 21 | 18 | 47.619 | 90.840 | 1.151 | 0.092 | 264.840 | 3.320 |
| 2021-01 | 17 | 15 | 52.941 | 30.680 | 1.046 | 0.076 | 284.880 | 3.067 |
| 2021-02 | 17 | 15 | 47.059 | 474.180 | 1.524 | 0.174 | 571.260 | 6.185 |
| 2021-03 | 23 | 17 | 43.478 | -693.080 | 0.621 | -0.120 | 724.300 | 4.711 |
| 2021-04 | 21 | 16 | 33.333 | -314.660 | 0.575 | -0.281 | 314.660 | 5.897 |
| 2021-05 | 27 | 17 | 33.333 | -336.920 | 0.706 | -0.285 | 683.680 | 10.627 |
| 2021-06 | 17 | 15 | 41.176 | -183.320 | 0.757 | -0.065 | 408.760 | 4.445 |
| 2021-07 | 19 | 15 | 52.632 | 27.260 | 1.040 | 0.240 | 173.920 | 2.114 |
| 2021-08 | 22 | 17 | 27.273 | -439.120 | 0.363 | -0.363 | 439.120 | 7.995 |
| 2021-09 | 22 | 19 | 50.000 | 612.380 | 1.890 | 0.204 | 273.260 | 4.940 |
| 2021-10 | 21 | 15 | 47.619 | -167.160 | 0.811 | 0.138 | 336.920 | 3.146 |
| 2021-11 | 21 | 15 | 33.333 | -267.660 | 0.753 | -0.271 | 473.220 | 5.692 |
| 2021-12 | 27 | 19 | 44.444 | 775.580 | 1.487 | 0.104 | 440.020 | 3.788 |
| 2022-01 | 23 | 18 | 56.522 | 2,654.920 | 2.805 | 0.441 | 392.880 | 4.638 |
| 2022-02 | 29 | 17 | 34.483 | -232.340 | 0.915 | -0.203 | 847.320 | 8.292 |
| 2022-03 | 21 | 17 | 57.143 | 1,458.340 | 2.383 | 0.408 | 384.420 | 3.090 |
| 2022-04 | 24 | 17 | 50.000 | 416.460 | 1.254 | 0.176 | 687.880 | 4.305 |
| 2022-05 | 20 | 18 | 55.000 | 594.800 | 1.310 | 0.247 | 1,645.720 | 6.188 |
| 2022-06 | 24 | 17 | 29.167 | -623.040 | 0.709 | -0.111 | 1,174.820 | 5.893 |
| 2022-07 | 23 | 19 | 56.522 | 1,429.920 | 2.632 | 0.554 | 403.380 | 3.489 |
| 2022-08 | 24 | 19 | 37.500 | -358.040 | 0.744 | -0.104 | 666.680 | 6.254 |
| 2022-09 | 21 | 16 | 47.619 | -60.160 | 0.958 | 0.046 | 499.340 | 3.767 |
| 2022-10 | 21 | 18 | 61.905 | 1,200.340 | 2.503 | 0.374 | 251.340 | 2.507 |
| 2022-11 | 27 | 17 | 40.741 | -243.420 | 0.850 | -0.002 | 545.440 | 4.436 |
| 2022-12 | 28 | 20 | 25.000 | -1,128.880 | 0.339 | -0.429 | 1,199.420 | 12.729 |
| 2023-01 | 27 | 18 | 51.852 | 572.080 | 1.697 | 0.224 | 321.300 | 3.188 |
| 2023-02 | 20 | 16 | 30.000 | -236.700 | 0.790 | -0.249 | 470.980 | 6.067 |
| 2023-03 | 27 | 19 | 51.852 | 493.080 | 1.500 | 0.081 | 594.260 | 5.238 |
| 2023-04 | 16 | 15 | 43.750 | -145.860 | 0.806 | -0.142 | 556.180 | 6.142 |
| 2023-05 | 24 | 20 | 37.500 | -114.540 | 0.871 | -0.016 | 383.600 | 5.234 |
| 2023-06 | 30 | 17 | 40.000 | -263.800 | 0.826 | -0.087 | 571.480 | 7.339 |
| 2023-07 | 23 | 17 | 30.435 | -294.080 | 0.724 | -0.187 | 629.980 | 6.728 |
| 2023-08 | 28 | 20 | 42.857 | 49.120 | 1.044 | 0.177 | 646.640 | 6.491 |
| 2023-09 | 20 | 16 | 40.000 | -293.200 | 0.728 | -0.122 | 462.240 | 3.606 |
| 2023-10 | 34 | 20 | 26.471 | -1,192.140 | 0.541 | -0.354 | 1,940.540 | 17.434 |
| 2023-11 | 21 | 16 | 47.619 | 261.840 | 1.376 | 0.009 | 301.800 | 4.965 |
| 2023-12 | 23 | 18 | 47.826 | 0.920 | 1.001 | 0.006 | 360.860 | 3.990 |

## Uncertainty and limitations

{"mean_r_ci_high": 0.09911721743951933, "mean_r_ci_low": -0.03971249734685396, "mean_usd_ci_high": 14.157053148862373, "mean_usd_ci_low": -2.5920904251577026}

95% exploratory confidence intervals resample NY trading dates (5,000 draws, seed 1729). No target/stop/swing settings optimized. No starting-equity or margin model. Drawdown is closed-trade drawdown. Sensitivity can change selected trades through position occupancy. This is an isolated Lab research adapter using the unchanged production executor, not a saved strategy version or normal database run. Existing records remain untouched. Validation and OOS have not been read for this experiment. All subgroup findings remain Development-only.
