# Opening 15-minute breakout — completed Development result

The specified system does not demonstrate a profitable Development strategy under the primary actual-cost assumptions. It enters after a five-minute close beyond the frozen 09:30–09:45 opening range, stops exactly at the immediately preceding five-minute candle's opposite extreme, and targets a fixed 50 points from the executed entry. Repeated breakouts are allowed, with one position at a time across both directions.

**Primary (one adverse tick each side, $0.73/side, one micro):** 2,534 trades, 1,126 wins and 1,408 losses; 44.44% net win rate; gross -$996.00; fees $3,699.64; net **-$4,695.64**; PF **0.9562**; average **-0.05319R**; total -134.773R; average -$1.85/trade; max closed-trade drawdown **$6,571.14**. Mean risk was 45.17 points, median 38.125 and maximum 275.25; the 50-point target is therefore a varying R multiple. Mean duration was 47.53 minutes and median 26. There were 996 target exits, 1,337 stops and 201 session-close exits, with three conservative stop/target conflicts and no adverse stop gaps.

Accounting: 3,745 raw breakouts on 996 dates = 2,534 selected + 1,169 skipped while a position was open + 42 at session close. Zero unresolved owned-minute executions and zero nonpositive-risk cases. Full opening ranges reconciled to the source minutes. Of 1,006 XNYS sessions, six half-days were excluded and three dates lacked a complete opening range: March 9, 12 and 16, 2020. Those dates were unavailable because of the observed missing/incomplete bars; no cause for that absence is inferred and no range was fabricated. Of 997 valid full-session ranges, one produced no qualifying breakout.

## Strongest and weakest observed times

These are actual New York entry/confirmation times. They are descriptive subsets of the full sequential run, not reruns with time filters.

| Entry window ET | Trades | Net USD | Average net R |
|---|---:|---:|---:|
| 09:45–09:59 | 492 | +153.18 | +0.01779 |
| 10:00–10:29 | 463 | -1,897.48 | -0.02259 |
| 10:30–10:59 | 258 | +1,143.82 | -0.05564 |
| 11:00–11:59 | 332 | -1,372.22 | -0.10012 |
| 12:00–13:59 | 477 | -440.92 | -0.08275 |
| 14:00–15:59 | 512 | -2,282.02 | -0.08985 |

The 10:30–10:59 window is strongest by net dollars and mean dollars/trade (+$4.43), but its negative mean R means it is not consistently positive when expressed relative to original risk. The earliest window is the only one with positive mean R, but net dollars are barely positive (+$0.31/trade) and positive in only two years. The 14:00–15:59 window is weakest by total and average net dollars (-$4.46/trade) and is negative in every year. The 11:00–11:59 window is weakest by average R. Thus “best time” depends on the metric; no reliable optimal window is established.

All six pooled windows' date-clustered exploratory 95% intervals for mean net R and mean net dollars/trade include zero. These intervals use 5,000 seeded resamples of dates and are not adjusted for selecting the strongest among many comparisons. Separate long/short and yearly tables are retained below; no negative subgroup was hidden. Restricting entries to a window would change occupancy and requires a separate controlled rerun, not filtering this CSV.

## Stability and costs

| Year | Trades | Net USD | PF | Average net R |
|---|---:|---:|---:|---:|
| 2020 | 649 | -873.04 | 0.9643 | -0.08307 |
| 2021 | 579 | -363.84 | 0.9841 | -0.00983 |
| 2022 | 673 | -1,795.58 | 0.9477 | -0.03911 |
| 2023 | 633 | -1,663.18 | 0.9348 | -0.07717 |

Longs: 1,335 trades, -$1,750.10, PF 0.9677, mean -0.05035R. Shorts: 1,199 trades, -$2,945.54, PF 0.9443, mean -0.05634R. Neither direction is positive after costs.

| Adverse ticks each side | Trades | Net USD | PF | Average net R |
|---|---:|---:|---:|---:|
| 0 | 2,537 | -2,155.52 | 0.9796 | -0.03690 |
| 1 | 2,534 | -4,695.64 | 0.9562 | -0.05319 |
| 2 | 2,529 | -7,819.34 | 0.9283 | -0.07054 |

Every sensitivity case retains the actual fees. Selection changes slightly because exit times change while only one position can be open. The causal breakout set is unchanged.

**Conclusion:** this exact setup does not support advancement to Validation on current evidence. Do not adopt an allegedly best time filter from these in-sample subsets. No additional stops, targets or filters were optimized. Validation/OOS outcomes remain untouched.

## Verification and viewing

105 relevant backend/research/execution tests, 35 frontend tests and four isolated browser workflows passed (144 total). Production build passed. All 7,600 native completed fills across the three scenarios independently reconciled. The full run/report rerun took 40.43 seconds and reproduced 23 artifacts byte-for-byte; the aggregate ZIP was separately repacked and matched exactly. Local artifacts total 26,377,696 bytes; ZIP 893,388 bytes. Existing dependency and build chunk-size warnings are nonblocking.

Source hashes, prior saved records and reveal-state metadata are unchanged. No production executor changes, paid downloads or reserved outcome reads occurred. Raw artifacts and market data remain local and ignored by Git. This audit is exposed read-only in Lab Research; it does not insert new saved-strategy or run database records.

Open http://127.0.0.1:5173/api/research/opening15-breakout/files/study.html for all trades, filters, retrospective five-minute charts and downloads. The chart uses only the verified local Development artifact; later candles are visible for inspection, never for detection.

---

# Opening 15-minute breakout · 50-point target

**DEVELOPMENT_ONLY_NOT_VALIDATED.** Sequential one-position, one-micro backtest, 2020–2023 only. Opening high/low fixed at 09:45; first subsequent 5m close outside triggers. Repeated crossings permitted, no time filter. Exact preceding-candle stop with no buffer. Fifty-point target from executed entry, no management. Full XNYS sessions only.

## Primary result and costs

| ticks | raw_breakouts | POSITION_OPEN | AT_SESSION_CLOSE | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd | gross_usd | fees_usd | target_exits | stop_exits | session_exits | conflicts | adverse_stop_gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 3745 | 1166 | 42 | 2537 | 996 | 44.659 | -2,155.520 | 0.980 | -0.850 | -0.037 | 5,403.640 | 1,548.500 | 3,704.020 | 1000 | 1336 | 201 | 2 | 0 |
| 1 | 3745 | 1169 | 42 | 2534 | 996 | 44.436 | -4,695.640 | 0.956 | -1.853 | -0.053 | 6,571.140 | -996.000 | 3,699.640 | 996 | 1337 | 201 | 3 | 0 |
| 2 | 3745 | 1174 | 42 | 2529 | 996 | 44.247 | -7,819.340 | 0.928 | -3.092 | -0.071 | 8,209.980 | -4,127.000 | 3,692.340 | 989 | 1338 | 202 | 3 | 0 |

One adverse entry tick and one adverse exit tick are primary; zero/two tick runs keep the same causal signals but reselect positions as fills change. Actual user fees $0.73/side/micro, $1.46 round trip. Native 1m fills, stop-first conflicts and adverse stop gaps are unchanged. Only owned post-confirmation minutes can fill. Missing data never rejects a signal using future knowledge. Any unresolved execution prevents an unqualified full-period performance claim.

## Yearly results

| year | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 649 | 248 | 41.294 | -873.040 | 0.964 | -1.345 | -0.083 | 1,633.900 |
| 2021 | 579 | 251 | 42.660 | -363.840 | 0.984 | -0.628 | -0.010 | 3,189.760 |
| 2022 | 673 | 249 | 50.966 | -1,795.580 | 0.948 | -2.668 | -0.039 | 5,045.380 |
| 2023 | 633 | 248 | 42.338 | -1,663.180 | 0.935 | -2.627 | -0.077 | 2,254.660 |

## Long versus short

| direction | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LONG | 1335 | 720 | 43.820 | -1,750.100 | 0.968 | -1.311 | -0.050 | 4,369.840 |
| SHORT | 1199 | 669 | 45.121 | -2,945.540 | 0.944 | -2.457 | -0.056 | 3,739.180 |

## Time windows — descriptive, not an optimized entry filter

Bins use the actual confirmed entry time in New York, not the start of the trigger candle. The first possible entry is 09:50. Every defined window remains in the report. Bootstrap 95% intervals resample trading dates, 5,000 repetitions with seed 1729; they are exploratory and not adjusted for selecting the best of multiple windows. Subset drawdowns do not represent a rerun restricted to that window.

| direction | time_bucket | raw_breakouts | position_open_skips | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd | mean_r_ci_low | mean_r_ci_high | mean_usd_ci_low | mean_usd_ci_high | positive_dollar_years | positive_r_years | years_present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | 09:45–09:59 | 492 | 0 | 492 | 492 | 51.829 | 153.180 | 1.006 | 0.311 | 0.018 | 2,182.600 | -0.081 | 0.111 | -9.448 | 9.689 | 2 | 3 | 4 |
| ALL | 10:00–10:29 | 627 | 164 | 463 | 441 | 48.596 | -1,897.480 | 0.920 | -4.098 | -0.023 | 3,651.860 | -0.120 | 0.079 | -13.825 | 5.769 | 1 | 1 | 4 |
| ALL | 10:30–10:59 | 437 | 179 | 258 | 248 | 47.287 | 1,143.820 | 1.111 | 4.433 | -0.056 | 1,043.660 | -0.188 | 0.079 | -6.468 | 15.308 | 3 | 2 | 4 |
| ALL | 11:00–11:59 | 577 | 245 | 332 | 296 | 38.253 | -1,372.220 | 0.900 | -4.133 | -0.100 | 3,237.700 | -0.238 | 0.042 | -13.316 | 5.060 | 1 | 1 | 4 |
| ALL | 12:00–13:59 | 778 | 301 | 477 | 357 | 36.897 | -440.920 | 0.974 | -0.924 | -0.083 | 1,589.720 | -0.207 | 0.052 | -7.955 | 6.118 | 2 | 3 | 4 |
| ALL | 14:00–15:59 | 792 | 280 | 512 | 349 | 43.164 | -2,282.020 | 0.876 | -4.457 | -0.090 | 2,876.840 | -0.180 | 0.007 | -11.144 | 2.658 | 0 | 0 | 4 |
| LONG | 09:45–09:59 | 260 | 0 | 260 | 260 | 50.000 | -195.600 | 0.984 | -0.752 | 0.020 | 2,244.580 | -0.117 | 0.164 | -13.389 | 12.239 | 2 | 2 | 4 |
| LONG | 10:00–10:29 | 325 | 80 | 245 | 238 | 46.531 | -1,750.700 | 0.862 | -7.146 | -0.046 | 2,210.680 | -0.187 | 0.099 | -21.137 | 5.945 | 1 | 2 | 4 |
| LONG | 10:30–10:59 | 212 | 85 | 127 | 126 | 47.244 | 1,085.080 | 1.237 | 8.544 | -0.020 | 703.680 | -0.214 | 0.190 | -6.635 | 23.588 | 2 | 2 | 4 |
| LONG | 11:00–11:59 | 302 | 125 | 177 | 158 | 36.723 | -878.420 | 0.876 | -4.963 | -0.161 | 1,757.200 | -0.335 | 0.033 | -16.976 | 7.704 | 2 | 0 | 4 |
| LONG | 12:00–13:59 | 419 | 158 | 261 | 203 | 37.165 | 254.940 | 1.030 | 0.977 | -0.043 | 970.380 | -0.215 | 0.141 | -8.033 | 10.534 | 3 | 3 | 4 |
| LONG | 14:00–15:59 | 394 | 129 | 265 | 207 | 44.906 | -265.400 | 0.970 | -1.002 | -0.072 | 1,564.260 | -0.198 | 0.062 | -10.289 | 8.123 | 2 | 1 | 4 |
| SHORT | 09:45–09:59 | 232 | 0 | 232 | 232 | 53.879 | 348.780 | 1.030 | 1.503 | 0.015 | 1,992.960 | -0.112 | 0.144 | -12.586 | 15.374 | 3 | 2 | 4 |
| SHORT | 10:00–10:29 | 302 | 84 | 218 | 210 | 50.917 | -146.780 | 0.987 | -0.673 | 0.003 | 2,545.620 | -0.129 | 0.141 | -14.499 | 13.320 | 1 | 2 | 4 |
| SHORT | 10:30–10:59 | 225 | 94 | 131 | 125 | 47.328 | 58.740 | 1.010 | 0.448 | -0.090 | 1,986.040 | -0.276 | 0.088 | -16.180 | 16.624 | 2 | 2 | 4 |
| SHORT | 11:00–11:59 | 275 | 120 | 155 | 146 | 40.000 | -493.800 | 0.925 | -3.186 | -0.031 | 1,818.020 | -0.228 | 0.175 | -16.479 | 10.428 | 1 | 2 | 4 |
| SHORT | 12:00–13:59 | 359 | 143 | 216 | 173 | 36.574 | -695.860 | 0.914 | -3.222 | -0.131 | 1,103.980 | -0.301 | 0.055 | -13.704 | 7.619 | 2 | 2 | 4 |
| SHORT | 14:00–15:59 | 398 | 151 | 247 | 192 | 41.296 | -2,016.620 | 0.790 | -8.164 | -0.109 | 2,227.160 | -0.245 | 0.039 | -18.198 | 2.223 | 0 | 0 | 4 |

## Time windows by year and direction

| time_bucket | year | direction | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 09:45–09:59 | 2020 | LONG | 62 | 62 | 53.226 | 1,024.980 | 1.536 | 16.532 | 0.207 | 409.760 |
| 09:45–09:59 | 2020 | SHORT | 49 | 49 | 40.816 | -1,203.540 | 0.611 | -24.562 | -0.179 | 1,622.060 |
| 09:45–09:59 | 2021 | LONG | 69 | 69 | 49.275 | 17.760 | 1.006 | 0.257 | 0.043 | 597.080 |
| 09:45–09:59 | 2021 | SHORT | 60 | 60 | 53.333 | 315.400 | 1.115 | 5.257 | 0.016 | 731.720 |
| 09:45–09:59 | 2022 | LONG | 62 | 62 | 53.226 | -1,149.520 | 0.738 | -18.541 | -0.071 | 1,745.540 |
| 09:45–09:59 | 2022 | SHORT | 72 | 72 | 65.278 | 1,111.380 | 1.318 | 15.436 | 0.174 | 1,080.940 |
| 09:45–09:59 | 2023 | LONG | 67 | 67 | 44.776 | -88.820 | 0.970 | -1.326 | -0.091 | 602.180 |
| 09:45–09:59 | 2023 | SHORT | 51 | 51 | 50.980 | 125.540 | 1.052 | 2.462 | -0.025 | 507.020 |
| 10:00–10:29 | 2020 | LONG | 65 | 64 | 43.077 | -684.400 | 0.799 | -10.529 | -0.040 | 958.680 |
| 10:00–10:29 | 2020 | SHORT | 50 | 49 | 44.000 | -151.000 | 0.935 | -3.020 | -0.132 | 894.080 |
| 10:00–10:29 | 2021 | LONG | 54 | 53 | 50.000 | 380.160 | 1.173 | 7.040 | 0.096 | 670.960 |
| 10:00–10:29 | 2021 | SHORT | 54 | 52 | 50.000 | -43.840 | 0.984 | -0.812 | 0.102 | 623.180 |
| 10:00–10:29 | 2022 | LONG | 55 | 54 | 58.182 | -429.800 | 0.880 | -7.815 | 0.012 | 1,153.540 |
| 10:00–10:29 | 2022 | SHORT | 57 | 54 | 56.140 | -620.720 | 0.835 | -10.890 | -0.023 | 1,774.320 |
| 10:00–10:29 | 2023 | LONG | 71 | 67 | 38.028 | -1,016.660 | 0.715 | -14.319 | -0.204 | 1,202.360 |
| 10:00–10:29 | 2023 | SHORT | 57 | 55 | 52.632 | 668.780 | 1.294 | 11.733 | 0.055 | 442.980 |
| 10:30–10:59 | 2020 | LONG | 30 | 30 | 36.667 | -9.800 | 0.991 | -0.327 | -0.079 | 304.940 |
| 10:30–10:59 | 2020 | SHORT | 21 | 20 | 66.667 | 700.340 | 2.264 | 33.350 | 0.344 | 140.840 |
| 10:30–10:59 | 2021 | LONG | 37 | 37 | 37.838 | -158.020 | 0.897 | -4.271 | -0.137 | 603.760 |
| 10:30–10:59 | 2021 | SHORT | 27 | 27 | 59.259 | 616.580 | 1.699 | 22.836 | 0.230 | 336.800 |
| 10:30–10:59 | 2022 | LONG | 36 | 36 | 61.111 | 764.940 | 1.550 | 21.248 | 0.085 | 208.920 |
| 10:30–10:59 | 2022 | SHORT | 42 | 38 | 42.857 | -509.320 | 0.776 | -12.127 | -0.237 | 1,073.380 |
| 10:30–10:59 | 2023 | LONG | 24 | 23 | 54.167 | 487.960 | 1.802 | 20.332 | 0.075 | 178.420 |
| 10:30–10:59 | 2023 | SHORT | 41 | 40 | 34.146 | -748.860 | 0.637 | -18.265 | -0.374 | 1,296.300 |
| 11:00–11:59 | 2020 | LONG | 38 | 32 | 36.842 | 25.020 | 1.020 | 0.658 | -0.138 | 402.640 |
| 11:00–11:59 | 2020 | SHORT | 45 | 42 | 48.889 | 703.300 | 1.484 | 15.629 | 0.241 | 541.020 |
| 11:00–11:59 | 2021 | LONG | 39 | 34 | 28.205 | -676.940 | 0.603 | -17.357 | -0.306 | 971.060 |
| 11:00–11:59 | 2021 | SHORT | 30 | 29 | 40.000 | -86.800 | 0.931 | -2.893 | 0.024 | 526.740 |
| 11:00–11:59 | 2022 | LONG | 41 | 39 | 46.341 | 94.640 | 1.054 | 2.308 | -0.049 | 600.760 |
| 11:00–11:59 | 2022 | SHORT | 41 | 39 | 39.024 | -574.860 | 0.732 | -14.021 | -0.234 | 707.060 |
| 11:00–11:59 | 2023 | LONG | 59 | 53 | 35.593 | -321.140 | 0.865 | -5.443 | -0.157 | 953.660 |
| 11:00–11:59 | 2023 | SHORT | 39 | 36 | 30.769 | -535.440 | 0.687 | -13.729 | -0.174 | 768.960 |
| 12:00–13:59 | 2020 | LONG | 80 | 63 | 30.000 | -424.800 | 0.837 | -5.310 | -0.266 | 745.340 |
| 12:00–13:59 | 2020 | SHORT | 49 | 42 | 24.490 | -680.540 | 0.634 | -13.889 | -0.546 | 937.300 |
| 12:00–13:59 | 2021 | LONG | 55 | 43 | 32.727 | 0.200 | 1.000 | 0.004 | 0.039 | 673.040 |
| 12:00–13:59 | 2021 | SHORT | 47 | 36 | 36.170 | 15.880 | 1.010 | 0.338 | 0.014 | 402.140 |
| 12:00–13:59 | 2022 | LONG | 68 | 51 | 44.118 | 390.220 | 1.155 | 5.739 | 0.016 | 501.320 |
| 12:00–13:59 | 2022 | SHORT | 68 | 54 | 45.588 | 335.220 | 1.134 | 4.930 | 0.012 | 350.720 |
| 12:00–13:59 | 2023 | LONG | 58 | 46 | 43.103 | 289.320 | 1.156 | 4.988 | 0.119 | 373.960 |
| 12:00–13:59 | 2023 | SHORT | 52 | 41 | 36.538 | -366.420 | 0.831 | -7.047 | -0.057 | 501.100 |
| 14:00–15:59 | 2020 | LONG | 93 | 68 | 41.935 | 142.720 | 1.055 | 1.535 | -0.064 | 394.260 |
| 14:00–15:59 | 2020 | SHORT | 67 | 54 | 43.284 | -315.320 | 0.868 | -4.706 | -0.079 | 826.160 |
| 14:00–15:59 | 2021 | LONG | 54 | 38 | 35.185 | -601.840 | 0.676 | -11.145 | -0.202 | 880.240 |
| 14:00–15:59 | 2021 | SHORT | 53 | 42 | 37.736 | -142.380 | 0.909 | -2.686 | -0.041 | 541.540 |
| 14:00–15:59 | 2022 | LONG | 64 | 55 | 50.000 | -304.440 | 0.898 | -4.757 | -0.097 | 776.660 |
| 14:00–15:59 | 2022 | SHORT | 67 | 47 | 46.269 | -903.320 | 0.744 | -13.482 | -0.163 | 1,509.720 |
| 14:00–15:59 | 2023 | LONG | 54 | 46 | 53.704 | 498.160 | 1.366 | 9.225 | 0.073 | 344.020 |
| 14:00–15:59 | 2023 | SHORT | 60 | 49 | 36.667 | -655.600 | 0.694 | -10.927 | -0.141 | 855.560 |

## Monthly

| month | trades | unique_dates | win_pct | net_usd | profit_factor | average_trade | avg_net_r | max_dd_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-01 | 51 | 21 | 23.529 | -435.960 | 0.640 | -8.548 | -0.218 | 591.520 |
| 2020-02 | 50 | 19 | 42.000 | 99.000 | 1.062 | 1.980 | -0.109 | 402.600 |
| 2020-03 | 60 | 19 | 53.333 | -1,027.600 | 0.753 | -17.127 | -0.058 | 1,300.320 |
| 2020-04 | 53 | 21 | 45.283 | 472.120 | 1.261 | 8.908 | 0.116 | 420.540 |
| 2020-05 | 47 | 20 | 44.681 | 313.880 | 1.204 | 6.678 | -0.013 | 516.020 |
| 2020-06 | 62 | 22 | 40.323 | 412.480 | 1.227 | 6.653 | -0.073 | 461.520 |
| 2020-07 | 64 | 22 | 40.625 | -136.940 | 0.945 | -2.140 | -0.019 | 713.860 |
| 2020-08 | 49 | 21 | 42.857 | 285.460 | 1.191 | 5.826 | -0.049 | 453.900 |
| 2020-09 | 55 | 21 | 52.727 | 303.700 | 1.132 | 5.522 | -0.023 | 738.540 |
| 2020-10 | 57 | 22 | 33.333 | -823.720 | 0.693 | -14.451 | -0.267 | 1,224.960 |
| 2020-11 | 52 | 19 | 44.231 | -85.920 | 0.955 | -1.652 | -0.099 | 525.580 |
| 2020-12 | 49 | 21 | 30.612 | -249.540 | 0.828 | -5.093 | -0.197 | 500.400 |
| 2021-01 | 47 | 19 | 38.298 | -489.120 | 0.765 | -10.407 | -0.101 | 708.020 |
| 2021-02 | 61 | 19 | 32.787 | -1,226.060 | 0.610 | -20.099 | -0.234 | 1,255.380 |
| 2021-03 | 65 | 23 | 44.615 | -484.400 | 0.854 | -7.452 | -0.103 | 1,331.160 |
| 2021-04 | 50 | 21 | 34.000 | -268.000 | 0.856 | -5.360 | -0.192 | 457.560 |
| 2021-05 | 44 | 20 | 45.455 | 407.260 | 1.279 | 9.256 | 0.002 | 378.980 |
| 2021-06 | 43 | 22 | 37.209 | -177.280 | 0.880 | -4.123 | -0.033 | 509.680 |
| 2021-07 | 53 | 21 | 35.849 | -518.880 | 0.751 | -9.790 | -0.088 | 844.880 |
| 2021-08 | 40 | 22 | 47.500 | 833.600 | 1.955 | 20.840 | 0.301 | 371.600 |
| 2021-09 | 40 | 21 | 52.500 | 388.600 | 1.257 | 9.715 | 0.285 | 498.840 |
| 2021-10 | 41 | 21 | 53.659 | 553.640 | 1.409 | 13.503 | 0.451 | 250.060 |
| 2021-11 | 51 | 20 | 37.255 | -177.460 | 0.907 | -3.480 | -0.181 | 566.980 |
| 2021-12 | 44 | 22 | 61.364 | 794.260 | 1.450 | 18.051 | 0.066 | 507.680 |
| 2022-01 | 69 | 20 | 47.826 | -873.740 | 0.787 | -12.663 | -0.154 | 1,402.100 |
| 2022-02 | 56 | 19 | 44.643 | -1,515.260 | 0.618 | -27.058 | -0.232 | 1,613.300 |
| 2022-03 | 62 | 23 | 58.065 | 760.980 | 1.282 | 12.274 | 0.064 | 584.000 |
| 2022-04 | 54 | 20 | 53.704 | -579.840 | 0.818 | -10.738 | -0.041 | 1,140.860 |
| 2022-05 | 70 | 21 | 52.857 | -1,430.700 | 0.709 | -20.439 | -0.116 | 2,199.380 |
| 2022-06 | 53 | 21 | 43.396 | -862.380 | 0.716 | -16.271 | -0.222 | 1,276.840 |
| 2022-07 | 40 | 20 | 55.000 | 510.600 | 1.310 | 12.765 | 0.115 | 719.480 |
| 2022-08 | 63 | 23 | 42.857 | -595.480 | 0.809 | -9.452 | -0.048 | 880.340 |
| 2022-09 | 60 | 21 | 53.333 | 258.400 | 1.093 | 4.307 | 0.089 | 716.320 |
| 2022-10 | 50 | 20 | 58.000 | 1,401.500 | 2.076 | 28.030 | 0.040 | 376.560 |
| 2022-11 | 50 | 20 | 50.000 | 327.500 | 1.160 | 6.550 | 0.027 | 710.320 |
| 2022-12 | 46 | 21 | 54.348 | 802.840 | 1.523 | 17.453 | 0.112 | 416.360 |
| 2023-01 | 47 | 20 | 48.936 | -62.120 | 0.969 | -1.322 | -0.070 | 802.000 |
| 2023-02 | 49 | 19 | 38.776 | -963.040 | 0.652 | -19.654 | -0.174 | 1,112.760 |
| 2023-03 | 61 | 23 | 50.820 | 291.440 | 1.117 | 4.778 | 0.142 | 875.780 |
| 2023-04 | 41 | 19 | 46.341 | 87.140 | 1.059 | 2.125 | 0.026 | 373.520 |
| 2023-05 | 59 | 22 | 32.203 | -460.140 | 0.788 | -7.799 | -0.174 | 879.020 |
| 2023-06 | 43 | 21 | 51.163 | 367.220 | 1.230 | 8.540 | 0.093 | 319.800 |
| 2023-07 | 60 | 19 | 35.000 | -844.100 | 0.678 | -14.068 | -0.253 | 848.540 |
| 2023-08 | 58 | 23 | 48.276 | 513.820 | 1.249 | 8.859 | 0.059 | 315.180 |
| 2023-09 | 47 | 20 | 40.426 | -118.120 | 0.935 | -2.513 | -0.127 | 738.680 |
| 2023-10 | 56 | 22 | 44.643 | -679.260 | 0.772 | -12.130 | -0.065 | 1,118.340 |
| 2023-11 | 58 | 20 | 37.931 | 21.320 | 1.012 | 0.368 | -0.183 | 366.520 |
| 2023-12 | 54 | 20 | 37.037 | 182.660 | 1.110 | 3.383 | -0.159 | 543.380 |

## Coverage, accounting and limitations

{"FULL_SESSION": 997, "HALF_DAY": 6, "OPENING_RANGE_UNAVAILABLE": 3}

All 3,745 breakouts and their selected/skipped reasons are retained for every cost scenario. Full opening ranges reconcile exactly to fifteen source minutes. Independent vector and stateful detectors agree. No missing or incomplete candles are bridged. Source hashes and source studies remain unchanged.

This tests one specified target and stop, not their optimality. There is no starting-equity, margin or return-percentage model. Dollar results assume one MNQ micro. Intraminute excursion ordering is unknown; exit-minute MFE/MAE include the full exit minute. Closed-equity drawdown excludes unrealized movement. Results are in-sample Development evidence, not Validation. A strongest observed time window is not automatically the best future trading window.

The complete trade list, all breakouts, audit reasons, coverage, costs, yearly/monthly/time tables and chronological equity are exported locally. Chart inspections show Development candles only. No Validation/OOS outcomes, data download or production-executor change.
