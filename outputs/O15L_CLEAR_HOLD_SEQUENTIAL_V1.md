# O15L upward clearance-and-hold: sequential Development test

**DEVELOPMENT_ONLY_NOT_VALIDATED.** Selected after prior Development research. This is not independent validation.

The original root break is above the opening fifteen-minute LOW. Other known levels within one causal ATR are frozen at that break. A later clearance close followed by a full candle above the barrier triggers entry. Stop: original root break low minus one tick. Fixed 1R, one micro, one position at a time. Actual XNYS session close, including early closes. No new filters.

## Reconciliation and costs

280 causal confirmations reproduce exactly; 279 were executable independent diagnostics. One at session close cannot enter. Position-open confirmations are discarded, never queued. All selected fills and excursions reconcile to their previous independent diagnostics. Zero/one/two adverse ticks each side; $0.73 per side actual fees.

| ticks | raw_breakouts | POSITION_OPEN | AT_SESSION_CLOSE | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd | gross_usd | fees_usd | max_dd_r | target_exits | stop_exits | session_exits | conflicts | adverse_stop_gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 280 | 6 | 1 | 273 | 242 | 56.777 | 3,856.920 | 1.284 | 14.128 | 0.080 | 1,195.680 | 4,255.500 | 398.580 | 6.857 | 109 | 92 | 72 | 0 | 0 |
| 1 | 280 | 6 | 1 | 273 | 242 | 56.410 | 3,671.920 | 1.268 | 13.450 | 0.073 | 1,202.680 | 4,070.500 | 398.580 | 7.032 | 108 | 92 | 73 | 0 | 0 |
| 2 | 280 | 6 | 1 | 273 | 242 | 55.678 | 3,459.920 | 1.250 | 12.674 | 0.060 | 1,209.680 | 3,858.500 | 398.580 | 7.204 | 106 | 93 | 74 | 0 | 0 |

## Yearly

| year | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 70 | 61 | 57.143 | 1,545.300 | 1.630 | 22.076 | 0.136 | 442.060 |
| 2021 | 65 | 59 | 55.385 | 1,101.600 | 1.346 | 16.948 | 0.034 | 503.220 |
| 2022 | 68 | 59 | 57.353 | 776.220 | 1.146 | 11.415 | 0.070 | 1,202.680 |
| 2023 | 70 | 63 | 55.714 | 248.800 | 1.090 | 3.554 | 0.049 | 737.260 |

## Comparison with previous independent diagnostics

The prior overlapping 1-tick diagnostics had 279 trades, +$3,362.16, PF 1.237624 and average net R +0.066450. The only new constraint is chronological one-position selection; this is not a historical CSV filter selected by outcomes.

## Uncertainty and risk

{"mean_r_ci_high": 0.17781931760348038, "mean_r_ci_low": -0.03197948731593146, "mean_usd_ci_high": 30.267996794871774, "mean_usd_ci_low": -2.881580339136531}

Date-cluster bootstrap: 5,000 resamples, seed 1729. Intervals are descriptive and do not correct prior candidate selection. A positive dollar sum is not sufficient evidence of a repeatable edge.

{"quantiles": {"0.0": 10.5, "0.25": 39.75, "0.5": 57.75, "0.75": 92.5, "1.0": 325.75}, "top5_net": 571.1999999999999}

{"bottom_date": "2022-04-18 15:51:00-04:00", "max_dd_usd": 1202.6800000000003, "peak_date": "2022-03-29 15:09:00-04:00", "recovery_date": "2022-07-21 12:07:00-04:00", "top5_net_during_drawdown": 0.0}

Top-five risk trades and their individual outcomes are exported. Closed-trade drawdown excludes unrealized loss. Exit-minute MFE/MAE includes the full minute; intraminute ordering is unknown.

## Interpretation

All four Development years are positive after costs, but 2023 contributes only $248.80. The date-cluster mean-R interval includes zero. Selection occurred after inspecting prior Development results; this does not establish a validated edge. Review the entry charts and freeze any future Validation protocol before accessing reserved data. No additional filters are suggested by this test.

## Monthly

| month | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-01 | 7 | 5 | 14.286 | -287.220 | 0.087 | -41.031 | -0.765 | 287.220 |
| 2020-02 | 4 | 3 | 75.000 | -154.840 | 0.372 | -38.710 | 0.250 | 246.460 |
| 2020-03 | 5 | 5 | 100.000 | 915.200 | — | 183.040 | 0.799 | 0.000 |
| 2020-04 | 9 | 8 | 66.667 | 478.860 | 3.723 | 53.207 | 0.417 | 90.960 |
| 2020-05 | 6 | 5 | 66.667 | 326.240 | 3.665 | 54.373 | 0.459 | 122.420 |
| 2020-06 | 4 | 3 | 50.000 | -47.840 | 0.679 | -11.960 | -0.033 | 148.920 |
| 2020-07 | 8 | 7 | 62.500 | 369.820 | 2.656 | 46.227 | 0.226 | 112.460 |
| 2020-08 | 6 | 5 | 33.333 | -230.260 | 0.381 | -38.377 | -0.306 | 321.380 |
| 2020-09 | 4 | 4 | 50.000 | 71.660 | 1.431 | 17.915 | -0.172 | 121.460 |
| 2020-10 | 7 | 6 | 42.857 | -44.220 | 0.839 | -6.317 | 0.076 | 254.880 |
| 2020-11 | 5 | 5 | 60.000 | -2.800 | 0.991 | -0.560 | 0.179 | 328.420 |
| 2020-12 | 5 | 5 | 80.000 | 150.700 | 2.897 | 30.140 | 0.566 | 79.460 |
| 2021-01 | 2 | 2 | 0.000 | -327.420 | 0.000 | -163.710 | -1.012 | 327.420 |
| 2021-02 | 11 | 10 | 63.636 | 224.440 | 1.432 | 20.404 | 0.203 | 240.760 |
| 2021-03 | 11 | 11 | 63.636 | 525.940 | 2.077 | 47.813 | 0.243 | 262.460 |
| 2021-04 | 2 | 2 | 50.000 | 74.080 | 26.027 | 37.040 | 0.469 | 2.960 |
| 2021-05 | 4 | 3 | 50.000 | -127.840 | 0.583 | -31.960 | -0.235 | 306.920 |
| 2021-06 | 4 | 4 | 50.000 | 17.660 | 1.167 | 4.415 | -0.022 | 105.920 |
| 2021-07 | 6 | 5 | 50.000 | -96.760 | 0.680 | -16.127 | -0.112 | 302.380 |
| 2021-08 | 4 | 4 | 75.000 | -15.840 | 0.911 | -3.960 | 0.138 | 178.960 |
| 2021-09 | 5 | 4 | 60.000 | 145.200 | 1.556 | 29.040 | 0.226 | 260.920 |
| 2021-10 | 4 | 4 | 25.000 | -14.840 | 0.937 | -3.710 | -0.524 | 233.880 |
| 2021-11 | 6 | 5 | 50.000 | -56.760 | 0.799 | -9.460 | -0.116 | 182.920 |
| 2021-12 | 6 | 5 | 66.667 | 753.740 | 5.410 | 125.623 | 0.201 | 110.460 |
| 2022-01 | 6 | 5 | 33.333 | -489.760 | 0.442 | -81.627 | -0.344 | 629.380 |
| 2022-02 | 7 | 7 | 71.429 | 616.780 | 5.766 | 88.111 | 0.328 | 122.960 |
| 2022-03 | 8 | 7 | 50.000 | 146.320 | 1.236 | 18.290 | -0.100 | 374.880 |
| 2022-04 | 6 | 5 | 33.333 | -627.260 | 0.344 | -104.543 | -0.343 | 827.800 |
| 2022-05 | 9 | 8 | 66.667 | 808.360 | 2.547 | 89.818 | 0.285 | 268.460 |
| 2022-06 | 5 | 4 | 40.000 | -378.300 | 0.532 | -75.660 | -0.208 | 638.840 |
| 2022-07 | 4 | 4 | 100.000 | 613.160 | — | 153.290 | 0.786 | 0.000 |
| 2022-08 | 5 | 4 | 80.000 | 118.700 | 1.694 | 23.740 | 0.288 | 170.960 |
| 2022-09 | 4 | 3 | 25.000 | -592.840 | 0.130 | -148.210 | -0.289 | 592.840 |
| 2022-10 | 5 | 5 | 60.000 | 47.700 | 1.138 | 9.540 | -0.066 | 280.960 |
| 2022-11 | 3 | 3 | 100.000 | 367.620 | — | 122.540 | 0.984 | 0.000 |
| 2022-12 | 6 | 4 | 50.000 | 145.740 | 1.677 | 24.290 | -0.025 | 173.420 |
| 2023-01 | 1 | 1 | 100.000 | 152.540 | — | 152.540 | 0.869 | 0.000 |
| 2023-02 | 8 | 5 | 25.000 | 11.820 | 1.026 | 1.478 | -0.249 | 462.760 |
| 2023-03 | 8 | 8 | 87.500 | 445.320 | 3.015 | 55.665 | 0.588 | 220.960 |
| 2023-04 | 2 | 2 | 50.000 | 30.080 | 4.357 | 15.040 | 0.336 | 8.960 |
| 2023-05 | 10 | 9 | 50.000 | 100.400 | 1.368 | 10.040 | 0.094 | 131.920 |
| 2023-06 | 7 | 7 | 42.857 | 46.780 | 1.155 | 6.683 | -0.126 | 125.960 |
| 2023-07 | 8 | 6 | 62.500 | -172.180 | 0.543 | -21.523 | 0.099 | 375.840 |
| 2023-08 | 6 | 6 | 66.667 | 15.240 | 1.081 | 2.540 | 0.193 | 187.420 |
| 2023-09 | 6 | 6 | 83.333 | 209.740 | 86.260 | 34.957 | 0.384 | 2.460 |
| 2023-10 | 3 | 3 | 33.333 | -380.380 | 0.216 | -126.793 | -0.535 | 484.920 |
| 2023-11 | 5 | 5 | 60.000 | -7.300 | 0.964 | -1.460 | 0.049 | 205.420 |
| 2023-12 | 6 | 5 | 33.333 | -203.260 | 0.140 | -33.877 | -0.627 | 203.260 |

## Entry time: descriptive only

| direction | time_bucket | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | 09:45–09:59 | 0 | 0 | — | 0.000 | — | — | — | 0.000 |
| ALL | 10:00–10:29 | 20 | 20 | 55.000 | -397.200 | 0.732 | -19.860 | 0.082 | 663.520 |
| ALL | 10:30–10:59 | 40 | 40 | 67.500 | 1,769.600 | 2.390 | 44.240 | 0.258 | 320.840 |
| ALL | 11:00–11:59 | 65 | 65 | 60.000 | 1,732.600 | 1.460 | 26.655 | 0.160 | 894.180 |
| ALL | 12:00–13:59 | 68 | 68 | 52.941 | -44.280 | 0.986 | -0.651 | -0.042 | 1,300.180 |
| ALL | 14:00–15:59 | 80 | 78 | 51.250 | 611.200 | 1.155 | 7.640 | 0.007 | 1,041.520 |
| LONG | 09:45–09:59 | 0 | 0 | — | 0.000 | — | — | — | 0.000 |
| LONG | 10:00–10:29 | 20 | 20 | 55.000 | -397.200 | 0.732 | -19.860 | 0.082 | 663.520 |
| LONG | 10:30–10:59 | 40 | 40 | 67.500 | 1,769.600 | 2.390 | 44.240 | 0.258 | 320.840 |
| LONG | 11:00–11:59 | 65 | 65 | 60.000 | 1,732.600 | 1.460 | 26.655 | 0.160 | 894.180 |
| LONG | 12:00–13:59 | 68 | 68 | 52.941 | -44.280 | 0.986 | -0.651 | -0.042 | 1,300.180 |
| LONG | 14:00–15:59 | 80 | 78 | 51.250 | 611.200 | 1.155 | 7.640 | 0.007 | 1,041.520 |

No Validation or OOS outcomes read. No strategy optimization, no production execution changes. Charts show Development trades retrospectively. Source artifacts and market data remain unchanged.
