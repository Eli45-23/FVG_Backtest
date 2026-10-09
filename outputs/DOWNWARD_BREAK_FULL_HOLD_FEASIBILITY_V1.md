# Controlled test result: wait for the next whole candle below the level

The confirmation test improves average net R in 27 of 32 level/stop/target cases compared with the original all-break population, but 31 of 32 remain negative after one adverse tick each side and the actual $0.73-per-side fee. This does not establish a dependable executable edge or justify selecting a final strategy.

All 4,784 causal confirmations on 889 Development dates were retained. Of these, 65 confirm exactly at session close and cannot own a subsequent RTH minute; 4,719 are executable in each cost/stop/target scenario. Five missing-ATR observations remain eligible for execution. No required owned minute was missing in these target simulations. No nonpositive-risk cases occurred.

The original 11,364 break roots reconcile to 4,784 full holds, 6,479 next candles that are not entirely below the level, and 101 breaks with no adjacent candle before session close. Thus 6,580 original roots do not yield the prescribed confirmation. This accounting is based on confirmed candles, not later returns.

Waiting selects stronger initial moves but gives up part of those moves. Across level/stop combinations, mean structural risk grows by approximately 9.22–10.70 points from the later entry while the absolute stops remain fixed. The matched-root immediate entries look favorable precisely because they are grouped using subsequent confirmation. They are not an entry filter that could have been known at the original break close. Some original trades already exit before the delayed entry; they remain in the comparison.

The only positive average-R primary case is O15H with the ORIGINAL break-candle-high stop and a 2R target: 620 completed independent diagnostics, +$1,180.30, PF 1.0405, average +0.00522R, approximately $1.90 net per diagnostic, and $2,660.24 closed-diagnostic drawdown. This is a disclosed exception, not a selected winner. Its average net R is negative in 2020 and 2023; net dollars are negative in 2021 and 2023. At two ticks per side its average becomes -0.02107R despite slightly positive dollars. Dollar and equal-risk conclusions must not be conflated.

For that case the yearly results are: 2020 +$1,120.86 / -0.05974R; 2021 -$136.12 / +0.04221R; 2022 +$1,514.36 / +0.10222R; 2023 -$1,318.80 / -0.06272R. Aggregate positivity is thin and inconsistent across years.

Five of 32 primary cases have positive dollars, but only one has positive average R. Zero-tick diagnostics retain actual fees: five cases have positive average R. At two ticks, none do. With the original break-high stop, 1R-before-stop rates range from 43.49% to 48.55%, and 2R-before-stop from 24.16% to 28.86%. The level stop gives 42.68%–51.03% and 26.83%–31.50%, respectively. These rates are stop-bounded path measurements, not a portfolio win rate; profitable session-close exits also affect fixed-target P&L.

Conclusion: do not advance this rule directly to Validation or declare a best level/target. It provides useful evidence about the trade-off between confirmation and worse entry price, but this test does not demonstrate a stable after-cost strategy. No additional entry/filter variants were tested.

All figures concern independent, potentially overlapping Development diagnostics, not an investable combined backtest. No daily position selection or sizing system was imposed. Production fills, original stops, target definitions, fees, previous artifacts, saved runs and market data were preserved. Validation and OOS outcomes were not read.

---

# Downward break → next full hold — Development v1

**DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY.** Eight fixed daily levels, immediately adjacent full-hold confirmed SHORT entry, two frozen structural stops and fixed original 1R/2R targets. Actual Webull fees; no signal filters or management. All causal 2020–2023 full-hold signals are retained, including later failures and retests.

## What was tested

Stop A (LEVEL_RECLAIM) is one tick above the broken level. Stop B (BREAK_CANDLE_HIGH) is one tick above the ORIGINAL root break candle’s high (not the confirmation candle high). Neither uses future data. The level stop can be narrower than the signal candle; pre-entry movement through it does not count as a stop-out. One micro, $2/point, $0.73/side fees. Primary one adverse entry tick and one adverse exit tick; zero/two-tick sensitivity uses the same signals.

Exact reconciliation: **4,784 raw signals on 889 dates**. 56,628 native fills/missing-data decisions were checked against an independent simulation. The production executor is unchanged.

**These are independently evaluated, often overlapping event diagnostics.** There is no single-position/day policy or capital allocation. Dollar totals, trade counts and cumulative closed-result drawdowns must not be presented as a live portfolio backtest. No aggregate across all levels is used to choose a winner.

## Population and future-data coverage

| level_type | raw_events | unique_dates | atr_unavailable | no_post_entry_minutes | complete_15m | complete_30m | complete_60m | future_gap_present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | 628 | 402 | 0 | 8 | 607 | 586 | 554 | 0 |
| O15L | 734 | 479 | 1 | 7 | 712 | 698 | 662 | 0 |
| O5H | 692 | 453 | 1 | 6 | 671 | 652 | 624 | 0 |
| O5L | 841 | 553 | 2 | 9 | 818 | 804 | 774 | 0 |
| PDH | 366 | 246 | 0 | 10 | 350 | 342 | 321 | 0 |
| PDL | 391 | 251 | 1 | 7 | 374 | 362 | 340 | 0 |
| PMH | 499 | 323 | 0 | 7 | 487 | 473 | 439 | 0 |
| PML | 633 | 404 | 0 | 11 | 614 | 595 | 565 | 0 |

ATR missingness never excludes fixed-risk execution. Causal events at the close remain in raw counts but cannot own a post-close minute. A missing future minute affects only simulations still open at that minute. Fifteen/thirty/sixty-minute descriptive denominators require complete horizons independently of early trade exits.

## Primary execution diagnostics: all levels and both stops/targets

| level_type | stop | target_r | events | valid_trades | wins | losses | win_pct | gross_usd | fees_usd | net_usd | pf | avg_net_r | positive_years | max_closed_diagnostic_dd_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | 628 | 620 | 321 | 299 | 51.774 | 994.000 | 905.200 | 88.800 | 1.004 | -0.005 | 2 | 3,312.180 |
| O15H | BREAK_CANDLE_HIGH | 2 | 628 | 620 | 233 | 387 | 37.581 | 2,085.500 | 905.200 | 1,180.300 | 1.041 | 0.005 | 2 | 2,660.240 |
| O15H | LEVEL_RECLAIM | 1 | 628 | 620 | 306 | 314 | 49.355 | -16.000 | 905.200 | -921.200 | 0.944 | -0.086 | 2 | 1,939.640 |
| O15H | LEVEL_RECLAIM | 2 | 628 | 620 | 214 | 406 | 34.516 | 587.500 | 905.200 | -317.700 | 0.985 | -0.067 | 2 | 2,186.640 |
| O15L | BREAK_CANDLE_HIGH | 1 | 734 | 727 | 369 | 358 | 50.757 | 827.500 | 1,061.420 | -233.920 | 0.993 | -0.013 | 1 | 2,796.420 |
| O15L | BREAK_CANDLE_HIGH | 2 | 734 | 727 | 273 | 454 | 37.552 | 2,258.500 | 1,061.420 | 1,197.080 | 1.031 | -0.012 | 2 | 3,318.880 |
| O15L | LEVEL_RECLAIM | 1 | 734 | 727 | 374 | 353 | 51.444 | 2,499.500 | 1,061.420 | 1,438.080 | 1.072 | -0.027 | 3 | 1,450.760 |
| O15L | LEVEL_RECLAIM | 2 | 734 | 727 | 257 | 470 | 35.351 | 3,653.000 | 1,061.420 | 2,591.580 | 1.100 | -0.039 | 3 | 1,801.480 |
| O5H | BREAK_CANDLE_HIGH | 1 | 692 | 686 | 346 | 340 | 50.437 | -1,880.500 | 1,001.560 | -2,882.060 | 0.900 | -0.020 | 0 | 4,587.620 |
| O5H | BREAK_CANDLE_HIGH | 2 | 692 | 686 | 242 | 444 | 35.277 | -2,139.000 | 1,001.560 | -3,140.560 | 0.912 | -0.062 | 0 | 5,231.360 |
| O5H | LEVEL_RECLAIM | 1 | 692 | 686 | 319 | 367 | 46.501 | -3,238.500 | 1,001.560 | -4,240.060 | 0.797 | -0.139 | 0 | 4,644.640 |
| O5H | LEVEL_RECLAIM | 2 | 692 | 686 | 233 | 453 | 33.965 | -1,264.000 | 1,001.560 | -2,265.560 | 0.910 | -0.087 | 1 | 4,100.420 |
| O5L | BREAK_CANDLE_HIGH | 1 | 841 | 832 | 411 | 421 | 49.399 | -2,264.000 | 1,214.720 | -3,478.720 | 0.910 | -0.053 | 1 | 5,342.760 |
| O5L | BREAK_CANDLE_HIGH | 2 | 841 | 832 | 299 | 533 | 35.938 | -627.500 | 1,214.720 | -1,842.220 | 0.961 | -0.067 | 1 | 5,187.080 |
| O5L | LEVEL_RECLAIM | 1 | 841 | 832 | 406 | 426 | 48.798 | -469.000 | 1,214.720 | -1,683.720 | 0.934 | -0.084 | 2 | 3,047.580 |
| O5L | LEVEL_RECLAIM | 2 | 841 | 832 | 278 | 554 | 33.413 | -1,472.000 | 1,214.720 | -2,686.720 | 0.919 | -0.099 | 2 | 4,641.080 |
| PDH | BREAK_CANDLE_HIGH | 1 | 366 | 356 | 166 | 190 | 46.629 | -4,077.500 | 519.760 | -4,597.260 | 0.717 | -0.098 | 0 | 5,087.600 |
| PDH | BREAK_CANDLE_HIGH | 2 | 366 | 356 | 118 | 238 | 33.146 | -2,737.500 | 519.760 | -3,257.260 | 0.825 | -0.126 | 0 | 3,359.680 |
| PDH | LEVEL_RECLAIM | 1 | 366 | 356 | 164 | 192 | 46.067 | -2,291.000 | 519.760 | -2,810.760 | 0.743 | -0.145 | 0 | 3,286.160 |
| PDH | LEVEL_RECLAIM | 2 | 366 | 356 | 110 | 246 | 30.899 | -2,232.500 | 519.760 | -2,752.260 | 0.793 | -0.178 | 0 | 2,952.640 |
| PDL | BREAK_CANDLE_HIGH | 1 | 391 | 384 | 195 | 189 | 50.781 | -1,982.500 | 560.640 | -2,543.140 | 0.856 | -0.042 | 0 | 3,518.880 |
| PDL | BREAK_CANDLE_HIGH | 2 | 391 | 384 | 144 | 240 | 37.500 | -2,486.500 | 560.640 | -3,047.140 | 0.860 | -0.045 | 1 | 3,894.400 |
| PDL | LEVEL_RECLAIM | 1 | 391 | 384 | 192 | 192 | 50.000 | -1,057.000 | 560.640 | -1,617.640 | 0.861 | -0.064 | 1 | 2,182.720 |
| PDL | LEVEL_RECLAIM | 2 | 391 | 384 | 130 | 254 | 33.854 | -1,342.500 | 560.640 | -1,903.140 | 0.872 | -0.104 | 1 | 2,470.080 |
| PMH | BREAK_CANDLE_HIGH | 1 | 499 | 492 | 247 | 245 | 50.203 | -1,949.000 | 718.320 | -2,667.320 | 0.870 | -0.038 | 1 | 3,507.000 |
| PMH | BREAK_CANDLE_HIGH | 2 | 499 | 492 | 178 | 314 | 36.179 | 146.500 | 718.320 | -571.820 | 0.977 | -0.022 | 2 | 3,156.600 |
| PMH | LEVEL_RECLAIM | 1 | 499 | 492 | 216 | 276 | 43.902 | -2,528.000 | 718.320 | -3,246.320 | 0.779 | -0.196 | 0 | 3,273.340 |
| PMH | LEVEL_RECLAIM | 2 | 499 | 492 | 146 | 346 | 29.675 | -2,627.500 | 718.320 | -3,345.820 | 0.816 | -0.211 | 1 | 3,345.820 |
| PML | BREAK_CANDLE_HIGH | 1 | 633 | 622 | 292 | 330 | 46.945 | -2,052.500 | 908.120 | -2,960.620 | 0.896 | -0.082 | 1 | 4,992.760 |
| PML | BREAK_CANDLE_HIGH | 2 | 633 | 622 | 210 | 412 | 33.762 | -1,074.500 | 908.120 | -1,982.620 | 0.943 | -0.093 | 1 | 4,349.640 |
| PML | LEVEL_RECLAIM | 1 | 633 | 622 | 299 | 323 | 48.071 | -904.000 | 908.120 | -1,812.120 | 0.904 | -0.091 | 2 | 2,933.400 |
| PML | LEVEL_RECLAIM | 2 | 633 | 622 | 206 | 416 | 33.119 | -767.500 | 908.120 | -1,675.620 | 0.931 | -0.085 | 1 | 4,003.480 |

Of the 32 predeclared primary level/stop/target cases, 5 have positive diagnostic net dollars and 1 have positive average net R. These counts are descriptive, not corrected statistical evidence or selection criteria.

## Stop-bounded price paths

Paths here end at original stop or actual session close, without taking either target. They answer whether the move gets to 1R/2R before stopping. Separate fixed-target simulations above can exit earlier. Inclusive exit-minute MFE/MAE are bounds because ordering inside that minute is unknown. Same-minute favorable/stop touches count stop first.

| level_type | stop | execution_events | valid_executable_events | risk_points_median | risk_points_q25 | risk_points_q75 | risk_points_max | r1_before_stop_pct | r2_before_stop_pct | mfe_r_mean | mae_r_mean | stop_before_half_r_pct | r1_conflict_count | execution_data_unavailable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 628 | 620 | 33.250 | 21.250 | 49.750 | 310.000 | 48.548 | 28.548 | 1.736 | 0.921 | 30.484 | 0 | 0 |
| O15H | LEVEL_RECLAIM | 628 | 620 | 21.000 | 12.188 | 34.750 | 287.750 | 48.226 | 30.968 | 2.296 | 1.073 | 33.065 | 8 | 0 |
| O15L | BREAK_CANDLE_HIGH | 734 | 727 | 39.000 | 25.625 | 59.000 | 207.750 | 48.006 | 27.098 | 1.668 | 0.910 | 31.637 | 0 | 0 |
| O15L | LEVEL_RECLAIM | 734 | 727 | 23.750 | 14.000 | 39.000 | 149.000 | 51.032 | 31.499 | 2.023 | 1.104 | 33.150 | 7 | 0 |
| O5H | BREAK_CANDLE_HIGH | 692 | 686 | 36.250 | 22.250 | 56.188 | 310.000 | 46.793 | 26.385 | 1.732 | 0.934 | 29.446 | 0 | 0 |
| O5H | LEVEL_RECLAIM | 692 | 686 | 21.750 | 12.500 | 37.188 | 287.750 | 45.190 | 30.175 | 2.150 | 1.095 | 33.965 | 8 | 0 |
| O5L | BREAK_CANDLE_HIGH | 841 | 832 | 41.750 | 26.000 | 60.562 | 310.000 | 46.274 | 25.962 | 1.587 | 0.914 | 33.413 | 0 | 0 |
| O5L | LEVEL_RECLAIM | 841 | 832 | 24.750 | 14.188 | 39.812 | 196.500 | 48.317 | 30.048 | 2.175 | 1.096 | 34.255 | 12 | 0 |
| PDH | BREAK_CANDLE_HIGH | 366 | 356 | 32.625 | 20.688 | 52.250 | 310.000 | 44.382 | 24.157 | 1.605 | 0.933 | 35.112 | 0 | 0 |
| PDH | LEVEL_RECLAIM | 366 | 356 | 20.000 | 10.750 | 36.250 | 189.250 | 45.787 | 27.809 | 2.057 | 1.100 | 37.360 | 7 | 0 |
| PDL | BREAK_CANDLE_HIGH | 391 | 384 | 39.500 | 27.250 | 62.000 | 200.250 | 43.490 | 26.042 | 1.642 | 0.890 | 30.469 | 1 | 0 |
| PDL | LEVEL_RECLAIM | 391 | 384 | 23.750 | 15.750 | 37.000 | 155.500 | 47.396 | 28.906 | 2.132 | 1.078 | 29.948 | 3 | 0 |
| PMH | BREAK_CANDLE_HIGH | 499 | 492 | 34.000 | 19.938 | 54.062 | 310.000 | 46.341 | 28.862 | 1.643 | 0.947 | 32.317 | 0 | 0 |
| PMH | LEVEL_RECLAIM | 499 | 492 | 21.000 | 11.188 | 36.250 | 294.500 | 42.683 | 26.829 | 1.822 | 1.095 | 40.244 | 7 | 0 |
| PML | BREAK_CANDLE_HIGH | 633 | 622 | 40.500 | 26.062 | 59.750 | 261.000 | 43.891 | 24.598 | 1.539 | 0.893 | 34.084 | 0 | 0 |
| PML | LEVEL_RECLAIM | 633 | 622 | 24.000 | 14.500 | 39.500 | 150.750 | 47.428 | 30.225 | 2.213 | 1.057 | 32.958 | 3 | 0 |

## Every Development year

| level_type | stop | target_r | year | events | valid_trades | win_pct | net_usd | pf | avg_net_r | max_closed_diagnostic_dd_usd | average_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | 2020 | 159 | 159 | 50.314 | 373.360 | 1.075 | -0.037 | 1,230.200 | 35.885 |
| O15H | BREAK_CANDLE_HIGH | 1 | 2021 | 150 | 147 | 54.422 | 691.880 | 1.155 | 0.052 | 579.880 | 34.150 |
| O15H | BREAK_CANDLE_HIGH | 1 | 2022 | 161 | 159 | 52.201 | -176.140 | 0.978 | 0.011 | 2,485.920 | 53.816 |
| O15H | BREAK_CANDLE_HIGH | 1 | 2023 | 158 | 155 | 50.323 | -800.300 | 0.864 | -0.041 | 1,548.660 | 37.179 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2020 | 159 | 159 | 35.220 | 1,120.860 | 1.179 | -0.060 | 1,394.160 | 35.885 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2021 | 150 | 147 | 37.415 | -136.120 | 0.978 | 0.042 | 1,158.040 | 34.150 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2022 | 161 | 159 | 40.881 | 1,514.360 | 1.158 | 0.102 | 2,660.240 | 53.816 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2023 | 158 | 155 | 36.774 | -1,318.800 | 0.816 | -0.063 | 1,656.140 | 37.179 |
| O15H | LEVEL_RECLAIM | 1 | 2020 | 159 | 159 | 43.396 | -556.140 | 0.858 | -0.206 | 1,184.960 | 24.055 |
| O15H | LEVEL_RECLAIM | 1 | 2021 | 150 | 147 | 53.061 | 292.380 | 1.092 | -0.015 | 304.920 | 22.804 |
| O15H | LEVEL_RECLAIM | 1 | 2022 | 161 | 159 | 55.975 | 618.860 | 1.130 | 0.051 | 959.060 | 33.953 |
| O15H | LEVEL_RECLAIM | 1 | 2023 | 158 | 155 | 45.161 | -1,276.300 | 0.714 | -0.170 | 1,290.580 | 24.648 |
| O15H | LEVEL_RECLAIM | 2 | 2020 | 159 | 159 | 30.189 | -528.140 | 0.892 | -0.211 | 1,322.160 | 24.055 |
| O15H | LEVEL_RECLAIM | 2 | 2021 | 150 | 147 | 36.054 | 358.380 | 1.084 | 0.001 | 572.380 | 22.804 |
| O15H | LEVEL_RECLAIM | 2 | 2022 | 161 | 159 | 37.736 | 574.860 | 1.089 | 0.020 | 1,899.480 | 33.953 |
| O15H | LEVEL_RECLAIM | 2 | 2023 | 158 | 155 | 34.194 | -722.800 | 0.861 | -0.072 | 1,133.120 | 24.648 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2020 | 172 | 172 | 49.419 | -579.620 | 0.914 | -0.039 | 1,040.160 | 39.076 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2021 | 175 | 173 | 54.335 | 1,527.920 | 1.262 | 0.037 | 887.740 | 41.733 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2022 | 207 | 205 | 50.244 | -1,019.800 | 0.914 | -0.002 | 2,575.120 | 58.407 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2023 | 180 | 177 | 49.153 | -162.420 | 0.976 | -0.049 | 1,379.820 | 40.422 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2020 | 172 | 172 | 39.535 | 1,076.880 | 1.137 | 0.082 | 1,675.400 | 39.076 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2021 | 175 | 173 | 38.150 | 978.420 | 1.125 | -0.044 | 1,350.500 | 41.733 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2022 | 207 | 205 | 37.073 | -229.800 | 0.984 | 0.018 | 3,045.120 | 58.407 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2023 | 180 | 177 | 35.593 | -628.420 | 0.923 | -0.104 | 1,634.740 | 40.422 |
| O15L | LEVEL_RECLAIM | 1 | 2020 | 172 | 172 | 52.907 | 271.380 | 1.064 | -0.008 | 591.060 | 25.936 |
| O15L | LEVEL_RECLAIM | 1 | 2021 | 175 | 173 | 56.647 | 1,934.920 | 1.554 | 0.065 | 509.100 | 26.017 |
| O15L | LEVEL_RECLAIM | 1 | 2022 | 207 | 205 | 50.244 | 344.700 | 1.048 | -0.027 | 1,058.760 | 36.432 |
| O15L | LEVEL_RECLAIM | 1 | 2023 | 180 | 177 | 46.328 | -1,112.920 | 0.779 | -0.136 | 1,211.860 | 25.770 |
| O15L | LEVEL_RECLAIM | 2 | 2020 | 172 | 172 | 37.791 | 1,355.880 | 1.250 | 0.054 | 789.900 | 25.936 |
| O15L | LEVEL_RECLAIM | 2 | 2021 | 175 | 173 | 40.462 | 2,079.420 | 1.421 | 0.074 | 756.780 | 26.017 |
| O15L | LEVEL_RECLAIM | 2 | 2022 | 207 | 205 | 34.146 | 735.200 | 1.079 | -0.048 | 1,479.060 | 36.432 |
| O15L | LEVEL_RECLAIM | 2 | 2023 | 180 | 177 | 29.379 | -1,578.920 | 0.750 | -0.231 | 1,801.480 | 25.770 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2020 | 178 | 178 | 47.191 | -114.880 | 0.981 | -0.080 | 1,803.180 | 38.056 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2021 | 154 | 151 | 52.318 | -951.960 | 0.834 | 0.029 | 1,366.120 | 36.291 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2022 | 184 | 183 | 51.366 | -1,646.180 | 0.843 | -0.009 | 3,717.640 | 57.660 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2023 | 176 | 174 | 51.149 | -169.040 | 0.974 | -0.014 | 929.740 | 39.339 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2020 | 178 | 178 | 33.708 | -102.380 | 0.987 | -0.080 | 1,797.640 | 38.056 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2021 | 154 | 151 | 35.099 | -1,371.460 | 0.809 | -0.022 | 2,165.920 | 36.291 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2022 | 184 | 183 | 37.705 | -665.680 | 0.947 | -0.019 | 4,872.440 | 57.660 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2023 | 176 | 174 | 34.483 | -1,001.040 | 0.875 | -0.121 | 1,610.960 | 39.339 |
| O5H | LEVEL_RECLAIM | 1 | 2020 | 178 | 178 | 45.506 | -297.380 | 0.932 | -0.155 | 1,300.240 | 25.140 |
| O5H | LEVEL_RECLAIM | 1 | 2021 | 154 | 151 | 50.993 | -579.960 | 0.851 | -0.052 | 831.480 | 24.184 |
| O5H | LEVEL_RECLAIM | 1 | 2022 | 184 | 183 | 48.634 | -2,061.680 | 0.725 | -0.092 | 2,998.060 | 37.111 |
| O5H | LEVEL_RECLAIM | 1 | 2023 | 176 | 174 | 41.379 | -1,301.040 | 0.745 | -0.249 | 1,384.200 | 25.816 |
| O5H | LEVEL_RECLAIM | 2 | 2020 | 178 | 178 | 32.584 | -468.880 | 0.918 | -0.133 | 1,288.960 | 25.140 |
| O5H | LEVEL_RECLAIM | 2 | 2021 | 154 | 151 | 37.748 | 28.540 | 1.006 | 0.057 | 1,181.380 | 24.184 |
| O5H | LEVEL_RECLAIM | 2 | 2022 | 184 | 183 | 36.612 | -1,007.180 | 0.884 | -0.026 | 2,914.680 | 37.111 |
| O5H | LEVEL_RECLAIM | 2 | 2023 | 176 | 174 | 29.310 | -818.040 | 0.866 | -0.230 | 1,470.720 | 25.816 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2020 | 215 | 212 | 50.472 | 90.980 | 1.011 | -0.028 | 1,211.980 | 39.216 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2021 | 206 | 205 | 46.341 | -1,249.800 | 0.859 | -0.118 | 2,970.720 | 42.967 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2022 | 205 | 202 | 51.980 | -469.420 | 0.962 | 0.009 | 1,692.100 | 64.776 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2023 | 215 | 213 | 48.826 | -1,850.480 | 0.804 | -0.073 | 2,827.180 | 43.207 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2020 | 215 | 212 | 37.264 | 1,194.480 | 1.123 | 0.003 | 1,210.280 | 39.216 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2021 | 206 | 205 | 34.146 | -799.300 | 0.925 | -0.133 | 2,712.720 | 42.967 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2022 | 205 | 202 | 36.634 | -393.920 | 0.974 | -0.029 | 2,611.820 | 64.776 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2023 | 215 | 213 | 35.681 | -1,843.480 | 0.834 | -0.111 | 3,369.680 | 43.207 |
| O5L | LEVEL_RECLAIM | 1 | 2020 | 215 | 212 | 52.358 | 889.480 | 1.182 | -0.026 | 544.800 | 25.439 |
| O5L | LEVEL_RECLAIM | 1 | 2021 | 206 | 205 | 44.390 | -1,188.800 | 0.810 | -0.174 | 2,005.660 | 28.134 |
| O5L | LEVEL_RECLAIM | 1 | 2022 | 205 | 202 | 52.475 | 736.080 | 1.096 | 0.008 | 962.040 | 40.756 |
| O5L | LEVEL_RECLAIM | 1 | 2023 | 215 | 213 | 46.009 | -2,120.480 | 0.687 | -0.144 | 2,253.660 | 27.183 |
| O5L | LEVEL_RECLAIM | 2 | 2020 | 215 | 212 | 37.264 | 1,182.980 | 1.177 | 0.024 | 1,475.420 | 25.439 |
| O5L | LEVEL_RECLAIM | 2 | 2021 | 206 | 205 | 28.780 | -1,879.800 | 0.763 | -0.252 | 2,784.380 | 28.134 |
| O5L | LEVEL_RECLAIM | 2 | 2022 | 205 | 202 | 37.129 | 843.080 | 1.084 | 0.035 | 1,431.300 | 40.756 |
| O5L | LEVEL_RECLAIM | 2 | 2023 | 215 | 213 | 30.516 | -2,832.980 | 0.661 | -0.199 | 3,096.160 | 27.183 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2020 | 108 | 104 | 49.038 | -503.840 | 0.860 | -0.072 | 809.280 | 35.038 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2021 | 93 | 91 | 45.055 | -1,082.360 | 0.697 | -0.148 | 1,152.480 | 34.863 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2022 | 69 | 66 | 34.848 | -2,589.360 | 0.516 | -0.308 | 2,589.360 | 66.890 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2023 | 96 | 95 | 53.684 | -421.700 | 0.887 | 0.067 | 858.300 | 38.018 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2020 | 108 | 104 | 34.615 | -438.340 | 0.900 | -0.077 | 821.060 | 35.038 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2021 | 93 | 91 | 30.769 | -679.860 | 0.829 | -0.223 | 1,261.000 | 34.863 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2022 | 69 | 66 | 28.788 | -1,453.860 | 0.743 | -0.203 | 1,453.860 | 66.890 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2023 | 96 | 95 | 36.842 | -685.200 | 0.850 | -0.033 | 982.280 | 38.018 |
| PDH | LEVEL_RECLAIM | 1 | 2020 | 108 | 104 | 48.077 | -299.340 | 0.878 | -0.124 | 778.280 | 23.546 |
| PDH | LEVEL_RECLAIM | 1 | 2021 | 93 | 91 | 47.253 | -438.360 | 0.808 | -0.145 | 726.600 | 22.588 |
| PDH | LEVEL_RECLAIM | 1 | 2022 | 69 | 66 | 43.939 | -1,108.360 | 0.669 | -0.140 | 1,249.440 | 43.667 |
| PDH | LEVEL_RECLAIM | 1 | 2023 | 96 | 95 | 44.211 | -964.700 | 0.661 | -0.173 | 1,043.240 | 25.074 |
| PDH | LEVEL_RECLAIM | 2 | 2020 | 108 | 104 | 28.846 | -642.840 | 0.805 | -0.258 | 852.260 | 23.546 |
| PDH | LEVEL_RECLAIM | 2 | 2021 | 93 | 91 | 31.868 | -448.860 | 0.840 | -0.176 | 703.240 | 22.588 |
| PDH | LEVEL_RECLAIM | 2 | 2022 | 69 | 66 | 27.273 | -1,409.860 | 0.650 | -0.226 | 1,409.860 | 43.667 |
| PDH | LEVEL_RECLAIM | 2 | 2023 | 96 | 95 | 34.737 | -250.700 | 0.920 | -0.059 | 641.340 | 25.074 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2020 | 75 | 74 | 41.892 | -900.040 | 0.749 | -0.175 | 1,467.800 | 45.760 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2021 | 99 | 96 | 57.292 | -151.160 | 0.959 | 0.041 | 720.420 | 44.193 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2022 | 132 | 131 | 53.435 | -119.760 | 0.981 | 0.031 | 1,901.240 | 52.903 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2023 | 85 | 83 | 46.988 | -1,372.180 | 0.652 | -0.133 | 1,980.860 | 44.693 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2020 | 75 | 74 | 28.378 | -1,060.540 | 0.768 | -0.175 | 1,660.640 | 45.760 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2021 | 99 | 96 | 39.583 | -1,344.660 | 0.729 | -0.071 | 1,501.920 | 44.193 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2022 | 132 | 131 | 39.695 | 165.740 | 1.021 | 0.036 | 2,404.800 | 52.903 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2023 | 85 | 83 | 39.759 | -807.680 | 0.814 | -0.026 | 1,646.540 | 44.693 |
| PDL | LEVEL_RECLAIM | 1 | 2020 | 75 | 74 | 45.946 | -960.540 | 0.625 | -0.133 | 1,126.760 | 29.226 |
| PDL | LEVEL_RECLAIM | 1 | 2021 | 99 | 96 | 53.125 | 190.840 | 1.078 | -0.020 | 488.080 | 26.917 |
| PDL | LEVEL_RECLAIM | 1 | 2022 | 132 | 131 | 51.145 | -351.260 | 0.916 | -0.024 | 1,393.420 | 32.235 |
| PDL | LEVEL_RECLAIM | 1 | 2023 | 85 | 83 | 48.193 | -496.680 | 0.799 | -0.116 | 1,034.900 | 28.440 |
| PDL | LEVEL_RECLAIM | 2 | 2020 | 75 | 74 | 28.378 | -627.540 | 0.793 | -0.214 | 1,280.740 | 29.226 |
| PDL | LEVEL_RECLAIM | 2 | 2021 | 99 | 96 | 35.417 | -385.660 | 0.886 | -0.122 | 781.960 | 26.917 |
| PDL | LEVEL_RECLAIM | 2 | 2022 | 132 | 131 | 37.405 | 303.740 | 1.059 | 0.040 | 1,510.520 | 32.235 |
| PDL | LEVEL_RECLAIM | 2 | 2023 | 85 | 83 | 31.325 | -1,193.680 | 0.631 | -0.212 | 1,760.620 | 28.440 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2020 | 113 | 113 | 54.867 | 370.020 | 1.114 | 0.039 | 601.400 | 32.883 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2021 | 132 | 128 | 48.438 | -1,167.880 | 0.750 | -0.086 | 1,608.220 | 34.154 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2022 | 117 | 116 | 50.862 | -199.860 | 0.970 | -0.005 | 1,791.200 | 61.213 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2023 | 137 | 135 | 47.407 | -1,669.600 | 0.721 | -0.085 | 1,765.680 | 41.622 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2020 | 113 | 113 | 39.823 | 1,473.020 | 1.374 | 0.058 | 656.400 | 32.883 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2021 | 132 | 128 | 37.500 | -1,176.380 | 0.788 | -0.016 | 1,431.280 | 34.154 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2022 | 117 | 116 | 37.931 | 1,709.140 | 1.215 | 0.073 | 1,576.400 | 61.213 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2023 | 137 | 135 | 30.370 | -2,577.600 | 0.653 | -0.175 | 2,577.600 | 41.622 |
| PMH | LEVEL_RECLAIM | 1 | 2020 | 113 | 113 | 41.593 | -790.480 | 0.710 | -0.264 | 1,170.300 | 21.518 |
| PMH | LEVEL_RECLAIM | 1 | 2021 | 132 | 128 | 43.750 | -283.880 | 0.903 | -0.218 | 567.100 | 22.072 |
| PMH | LEVEL_RECLAIM | 1 | 2022 | 117 | 116 | 48.276 | -622.860 | 0.866 | -0.083 | 1,351.340 | 40.164 |
| PMH | LEVEL_RECLAIM | 1 | 2023 | 137 | 135 | 42.222 | -1,549.100 | 0.650 | -0.216 | 1,622.640 | 27.848 |
| PMH | LEVEL_RECLAIM | 2 | 2020 | 113 | 113 | 29.204 | -707.980 | 0.784 | -0.268 | 1,156.740 | 21.518 |
| PMH | LEVEL_RECLAIM | 2 | 2021 | 132 | 128 | 27.344 | -1,216.880 | 0.696 | -0.296 | 1,386.960 | 22.072 |
| PMH | LEVEL_RECLAIM | 2 | 2022 | 117 | 116 | 34.483 | 401.140 | 1.072 | -0.032 | 1,334.700 | 40.164 |
| PMH | LEVEL_RECLAIM | 2 | 2023 | 137 | 135 | 28.148 | -1,822.100 | 0.662 | -0.237 | 1,822.100 | 27.848 |
| PML | BREAK_CANDLE_HIGH | 1 | 2020 | 126 | 120 | 45.000 | -1,954.200 | 0.662 | -0.132 | 2,426.020 | 41.169 |
| PML | BREAK_CANDLE_HIGH | 1 | 2021 | 144 | 143 | 44.755 | -665.780 | 0.891 | -0.135 | 2,079.980 | 45.301 |
| PML | BREAK_CANDLE_HIGH | 1 | 2022 | 202 | 200 | 49.500 | -603.000 | 0.946 | -0.008 | 2,113.700 | 58.481 |
| PML | BREAK_CANDLE_HIGH | 1 | 2023 | 161 | 159 | 47.170 | 262.360 | 1.047 | -0.088 | 1,448.580 | 38.851 |
| PML | BREAK_CANDLE_HIGH | 2 | 2020 | 126 | 120 | 33.333 | -857.700 | 0.869 | -0.059 | 1,415.960 | 41.169 |
| PML | BREAK_CANDLE_HIGH | 2 | 2021 | 144 | 143 | 32.168 | -628.280 | 0.916 | -0.175 | 2,013.000 | 45.301 |
| PML | BREAK_CANDLE_HIGH | 2 | 2022 | 202 | 200 | 37.500 | 40.500 | 1.003 | 0.031 | 3,111.200 | 58.481 |
| PML | BREAK_CANDLE_HIGH | 2 | 2023 | 161 | 159 | 30.818 | -537.140 | 0.926 | -0.200 | 2,346.200 | 38.851 |
| PML | LEVEL_RECLAIM | 1 | 2020 | 126 | 120 | 45.833 | -1,371.200 | 0.650 | -0.151 | 1,578.960 | 26.863 |
| PML | LEVEL_RECLAIM | 1 | 2021 | 144 | 143 | 46.154 | 35.220 | 1.009 | -0.121 | 1,028.440 | 29.652 |
| PML | LEVEL_RECLAIM | 1 | 2022 | 202 | 200 | 50.000 | -759.500 | 0.898 | -0.038 | 1,404.740 | 35.627 |
| PML | LEVEL_RECLAIM | 1 | 2023 | 161 | 159 | 49.057 | 283.360 | 1.079 | -0.085 | 540.160 | 24.387 |
| PML | LEVEL_RECLAIM | 2 | 2020 | 126 | 120 | 33.333 | -747.700 | 0.837 | -0.075 | 1,723.460 | 26.863 |
| PML | LEVEL_RECLAIM | 2 | 2021 | 144 | 143 | 32.867 | -325.280 | 0.938 | -0.123 | 1,848.800 | 29.652 |
| PML | LEVEL_RECLAIM | 2 | 2022 | 202 | 200 | 34.500 | -887.500 | 0.907 | -0.007 | 2,122.180 | 35.627 |
| PML | LEVEL_RECLAIM | 2 | 2023 | 161 | 159 | 31.447 | 284.860 | 1.060 | -0.157 | 660.500 | 24.387 |

## Actual costs and sensitivity

| level_type | stop | target_r | ticks | valid_trades | gross_usd | fees_usd | net_usd | pf | avg_net_r | break_even_fee_per_side |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | 0 | 620 | 1,858.000 | 905.200 | 952.800 | 1.042 | 0.015 | 1.498 |
| O15H | BREAK_CANDLE_HIGH | 2 | 0 | 620 | 2,596.500 | 905.200 | 1,691.300 | 1.059 | 0.018 | 2.094 |
| O15H | BREAK_CANDLE_HIGH | 1 | 1 | 620 | 994.000 | 905.200 | 88.800 | 1.004 | -0.005 | 0.802 |
| O15H | BREAK_CANDLE_HIGH | 2 | 1 | 620 | 2,085.500 | 905.200 | 1,180.300 | 1.041 | 0.005 | 1.682 |
| O15H | BREAK_CANDLE_HIGH | 1 | 2 | 620 | 228.000 | 905.200 | -677.200 | 0.972 | -0.030 | 0.184 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2 | 620 | 1,235.000 | 905.200 | 329.800 | 1.011 | -0.021 | 0.996 |
| O15H | LEVEL_RECLAIM | 1 | 0 | 620 | 712.000 | 905.200 | -193.200 | 0.988 | -0.054 | 0.574 |
| O15H | LEVEL_RECLAIM | 2 | 0 | 620 | 954.000 | 905.200 | 48.800 | 1.002 | -0.046 | 0.769 |
| O15H | LEVEL_RECLAIM | 1 | 1 | 620 | -16.000 | 905.200 | -921.200 | 0.944 | -0.086 | -0.013 |
| O15H | LEVEL_RECLAIM | 2 | 1 | 620 | 587.500 | 905.200 | -317.700 | 0.985 | -0.067 | 0.474 |
| O15H | LEVEL_RECLAIM | 1 | 2 | 620 | -594.000 | 905.200 | -1,499.200 | 0.911 | -0.117 | -0.479 |
| O15H | LEVEL_RECLAIM | 2 | 2 | 620 | -361.000 | 905.200 | -1,266.200 | 0.941 | -0.111 | -0.291 |
| O15L | BREAK_CANDLE_HIGH | 1 | 0 | 727 | 1,352.500 | 1,061.420 | 291.080 | 1.009 | 0.000 | 0.930 |
| O15L | BREAK_CANDLE_HIGH | 2 | 0 | 727 | 2,930.000 | 1,061.420 | 1,868.580 | 1.049 | 0.010 | 2.015 |
| O15L | BREAK_CANDLE_HIGH | 1 | 1 | 727 | 827.500 | 1,061.420 | -233.920 | 0.993 | -0.013 | 0.569 |
| O15L | BREAK_CANDLE_HIGH | 2 | 1 | 727 | 2,258.500 | 1,061.420 | 1,197.080 | 1.031 | -0.012 | 1.553 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2 | 727 | 148.500 | 1,061.420 | -912.920 | 0.971 | -0.029 | 0.102 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2 | 727 | 1,533.000 | 1,061.420 | 471.580 | 1.012 | -0.029 | 1.054 |
| O15L | LEVEL_RECLAIM | 1 | 0 | 727 | 3,330.500 | 1,061.420 | 2,269.080 | 1.117 | 0.001 | 2.291 |
| O15L | LEVEL_RECLAIM | 2 | 0 | 727 | 4,378.000 | 1,061.420 | 3,316.580 | 1.131 | -0.008 | 3.011 |
| O15L | LEVEL_RECLAIM | 1 | 1 | 727 | 2,499.500 | 1,061.420 | 1,438.080 | 1.072 | -0.027 | 1.719 |
| O15L | LEVEL_RECLAIM | 2 | 1 | 727 | 3,653.000 | 1,061.420 | 2,591.580 | 1.100 | -0.039 | 2.512 |
| O15L | LEVEL_RECLAIM | 1 | 2 | 727 | 1,768.500 | 1,061.420 | 707.080 | 1.035 | -0.057 | 1.216 |
| O15L | LEVEL_RECLAIM | 2 | 2 | 727 | 3,004.500 | 1,061.420 | 1,943.080 | 1.073 | -0.066 | 2.066 |
| O5H | BREAK_CANDLE_HIGH | 1 | 0 | 686 | -1,039.000 | 1,001.560 | -2,040.560 | 0.928 | -0.004 | -0.757 |
| O5H | BREAK_CANDLE_HIGH | 2 | 0 | 686 | -1,427.000 | 1,001.560 | -2,428.560 | 0.931 | -0.045 | -1.040 |
| O5H | BREAK_CANDLE_HIGH | 1 | 1 | 686 | -1,880.500 | 1,001.560 | -2,882.060 | 0.900 | -0.020 | -1.371 |
| O5H | BREAK_CANDLE_HIGH | 2 | 1 | 686 | -2,139.000 | 1,001.560 | -3,140.560 | 0.912 | -0.062 | -1.559 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2 | 686 | -2,918.500 | 1,001.560 | -3,920.060 | 0.867 | -0.050 | -2.127 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2 | 686 | -2,870.000 | 1,001.560 | -3,871.560 | 0.893 | -0.081 | -2.092 |
| O5H | LEVEL_RECLAIM | 1 | 0 | 686 | -2,343.500 | 1,001.560 | -3,345.060 | 0.835 | -0.109 | -1.708 |
| O5H | LEVEL_RECLAIM | 2 | 0 | 686 | -687.500 | 1,001.560 | -1,689.060 | 0.932 | -0.054 | -0.501 |
| O5H | LEVEL_RECLAIM | 1 | 1 | 686 | -3,238.500 | 1,001.560 | -4,240.060 | 0.797 | -0.139 | -2.360 |
| O5H | LEVEL_RECLAIM | 2 | 1 | 686 | -1,264.000 | 1,001.560 | -2,265.560 | 0.910 | -0.087 | -0.921 |
| O5H | LEVEL_RECLAIM | 1 | 2 | 686 | -3,808.000 | 1,001.560 | -4,809.560 | 0.775 | -0.167 | -2.776 |
| O5H | LEVEL_RECLAIM | 2 | 2 | 686 | -2,160.000 | 1,001.560 | -3,161.560 | 0.878 | -0.128 | -1.574 |
| O5L | BREAK_CANDLE_HIGH | 1 | 0 | 832 | -1,711.000 | 1,214.720 | -2,925.720 | 0.924 | -0.042 | -1.028 |
| O5L | BREAK_CANDLE_HIGH | 2 | 0 | 832 | 95.000 | 1,214.720 | -1,119.720 | 0.976 | -0.048 | 0.057 |
| O5L | BREAK_CANDLE_HIGH | 1 | 1 | 832 | -2,264.000 | 1,214.720 | -3,478.720 | 0.910 | -0.053 | -1.361 |
| O5L | BREAK_CANDLE_HIGH | 2 | 1 | 832 | -627.500 | 1,214.720 | -1,842.220 | 0.961 | -0.067 | -0.377 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2 | 832 | -3,041.000 | 1,214.720 | -4,255.720 | 0.892 | -0.068 | -1.828 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2 | 832 | -1,494.000 | 1,214.720 | -2,708.720 | 0.943 | -0.084 | -0.898 |
| O5L | LEVEL_RECLAIM | 1 | 0 | 832 | 938.000 | 1,214.720 | -276.720 | 0.989 | -0.054 | 0.564 |
| O5L | LEVEL_RECLAIM | 2 | 0 | 832 | -705.500 | 1,214.720 | -1,920.220 | 0.941 | -0.068 | -0.424 |
| O5L | LEVEL_RECLAIM | 1 | 1 | 832 | -469.000 | 1,214.720 | -1,683.720 | 0.934 | -0.084 | -0.282 |
| O5L | LEVEL_RECLAIM | 2 | 1 | 832 | -1,472.000 | 1,214.720 | -2,686.720 | 0.919 | -0.099 | -0.885 |
| O5L | LEVEL_RECLAIM | 1 | 2 | 832 | -1,203.000 | 1,214.720 | -2,417.720 | 0.908 | -0.108 | -0.723 |
| O5L | LEVEL_RECLAIM | 2 | 2 | 832 | -2,625.000 | 1,214.720 | -3,839.720 | 0.886 | -0.137 | -1.578 |
| PDH | BREAK_CANDLE_HIGH | 1 | 0 | 356 | -3,653.500 | 519.760 | -4,173.260 | 0.738 | -0.075 | -5.131 |
| PDH | BREAK_CANDLE_HIGH | 2 | 0 | 356 | -2,510.500 | 519.760 | -3,030.260 | 0.835 | -0.115 | -3.526 |
| PDH | BREAK_CANDLE_HIGH | 1 | 1 | 356 | -4,077.500 | 519.760 | -4,597.260 | 0.717 | -0.098 | -5.727 |
| PDH | BREAK_CANDLE_HIGH | 2 | 1 | 356 | -2,737.500 | 519.760 | -3,257.260 | 0.825 | -0.126 | -3.845 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2 | 356 | -4,743.500 | 519.760 | -5,263.260 | 0.684 | -0.124 | -6.662 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2 | 356 | -3,207.500 | 519.760 | -3,727.260 | 0.803 | -0.155 | -4.505 |
| PDH | LEVEL_RECLAIM | 1 | 0 | 356 | -2,024.000 | 519.760 | -2,543.760 | 0.762 | -0.123 | -2.843 |
| PDH | LEVEL_RECLAIM | 2 | 0 | 356 | -1,977.000 | 519.760 | -2,496.760 | 0.808 | -0.152 | -2.777 |
| PDH | LEVEL_RECLAIM | 1 | 1 | 356 | -2,291.000 | 519.760 | -2,810.760 | 0.743 | -0.145 | -3.218 |
| PDH | LEVEL_RECLAIM | 2 | 1 | 356 | -2,232.500 | 519.760 | -2,752.260 | 0.793 | -0.178 | -3.136 |
| PDH | LEVEL_RECLAIM | 1 | 2 | 356 | -2,627.000 | 519.760 | -3,146.760 | 0.719 | -0.172 | -3.690 |
| PDH | LEVEL_RECLAIM | 2 | 2 | 356 | -2,507.500 | 519.760 | -3,027.260 | 0.776 | -0.203 | -3.522 |
| PDL | BREAK_CANDLE_HIGH | 1 | 0 | 384 | -1,641.500 | 560.640 | -2,202.140 | 0.874 | -0.029 | -2.137 |
| PDL | BREAK_CANDLE_HIGH | 2 | 0 | 384 | -2,194.500 | 560.640 | -2,755.140 | 0.872 | -0.035 | -2.857 |
| PDL | BREAK_CANDLE_HIGH | 1 | 1 | 384 | -1,982.500 | 560.640 | -2,543.140 | 0.856 | -0.042 | -2.581 |
| PDL | BREAK_CANDLE_HIGH | 2 | 1 | 384 | -2,486.500 | 560.640 | -3,047.140 | 0.860 | -0.045 | -3.238 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2 | 384 | -2,296.500 | 560.640 | -2,857.140 | 0.840 | -0.055 | -2.990 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2 | 384 | -2,852.500 | 560.640 | -3,413.140 | 0.846 | -0.061 | -3.714 |
| PDL | LEVEL_RECLAIM | 1 | 0 | 384 | -419.000 | 560.640 | -979.640 | 0.913 | -0.035 | -0.546 |
| PDL | LEVEL_RECLAIM | 2 | 0 | 384 | -919.500 | 560.640 | -1,480.140 | 0.898 | -0.075 | -1.197 |
| PDL | LEVEL_RECLAIM | 1 | 1 | 384 | -1,057.000 | 560.640 | -1,617.640 | 0.861 | -0.064 | -1.376 |
| PDL | LEVEL_RECLAIM | 2 | 1 | 384 | -1,342.500 | 560.640 | -1,903.140 | 0.872 | -0.104 | -1.748 |
| PDL | LEVEL_RECLAIM | 1 | 2 | 384 | -1,288.000 | 560.640 | -1,848.640 | 0.844 | -0.082 | -1.677 |
| PDL | LEVEL_RECLAIM | 2 | 2 | 384 | -2,522.000 | 560.640 | -3,082.640 | 0.799 | -0.139 | -3.284 |
| PMH | BREAK_CANDLE_HIGH | 1 | 0 | 492 | -1,424.000 | 718.320 | -2,142.320 | 0.894 | -0.018 | -1.447 |
| PMH | BREAK_CANDLE_HIGH | 2 | 0 | 492 | 601.500 | 718.320 | -116.820 | 0.995 | -0.003 | 0.611 |
| PMH | BREAK_CANDLE_HIGH | 1 | 1 | 492 | -1,949.000 | 718.320 | -2,667.320 | 0.870 | -0.038 | -1.981 |
| PMH | BREAK_CANDLE_HIGH | 2 | 1 | 492 | 146.500 | 718.320 | -571.820 | 0.977 | -0.022 | 0.149 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2 | 492 | -2,375.000 | 718.320 | -3,093.320 | 0.852 | -0.064 | -2.414 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2 | 492 | -132.500 | 718.320 | -850.820 | 0.966 | -0.032 | -0.135 |
| PMH | LEVEL_RECLAIM | 1 | 0 | 492 | -2,222.000 | 718.320 | -2,940.320 | 0.796 | -0.171 | -2.258 |
| PMH | LEVEL_RECLAIM | 2 | 0 | 492 | -2,087.500 | 718.320 | -2,805.820 | 0.842 | -0.176 | -2.121 |
| PMH | LEVEL_RECLAIM | 1 | 1 | 492 | -2,528.000 | 718.320 | -3,246.320 | 0.779 | -0.196 | -2.569 |
| PMH | LEVEL_RECLAIM | 2 | 1 | 492 | -2,627.500 | 718.320 | -3,345.820 | 0.816 | -0.211 | -2.670 |
| PMH | LEVEL_RECLAIM | 1 | 2 | 492 | -3,058.000 | 718.320 | -3,776.320 | 0.750 | -0.224 | -3.108 |
| PMH | LEVEL_RECLAIM | 2 | 2 | 492 | -2,975.000 | 718.320 | -3,693.320 | 0.801 | -0.230 | -3.023 |
| PML | BREAK_CANDLE_HIGH | 1 | 0 | 622 | -1,562.500 | 908.120 | -2,470.620 | 0.912 | -0.069 | -1.256 |
| PML | BREAK_CANDLE_HIGH | 2 | 0 | 622 | -173.500 | 908.120 | -1,081.620 | 0.968 | -0.070 | -0.139 |
| PML | BREAK_CANDLE_HIGH | 1 | 1 | 622 | -2,052.500 | 908.120 | -2,960.620 | 0.896 | -0.082 | -1.650 |
| PML | BREAK_CANDLE_HIGH | 2 | 1 | 622 | -1,074.500 | 908.120 | -1,982.620 | 0.943 | -0.093 | -0.864 |
| PML | BREAK_CANDLE_HIGH | 1 | 2 | 622 | -2,874.500 | 908.120 | -3,782.620 | 0.870 | -0.099 | -2.311 |
| PML | BREAK_CANDLE_HIGH | 2 | 2 | 622 | -1,601.500 | 908.120 | -2,509.620 | 0.929 | -0.103 | -1.287 |
| PML | LEVEL_RECLAIM | 1 | 0 | 622 | -267.000 | 908.120 | -1,175.120 | 0.936 | -0.058 | -0.215 |
| PML | LEVEL_RECLAIM | 2 | 0 | 622 | -298.500 | 908.120 | -1,206.620 | 0.949 | -0.062 | -0.240 |
| PML | LEVEL_RECLAIM | 1 | 1 | 622 | -904.000 | 908.120 | -1,812.120 | 0.904 | -0.091 | -0.727 |
| PML | LEVEL_RECLAIM | 2 | 1 | 622 | -767.500 | 908.120 | -1,675.620 | 0.931 | -0.085 | -0.617 |
| PML | LEVEL_RECLAIM | 1 | 2 | 622 | -1,745.000 | 908.120 | -2,653.120 | 0.864 | -0.123 | -1.403 |
| PML | LEVEL_RECLAIM | 2 | 2 | 622 | -1,157.500 | 908.120 | -2,065.620 | 0.916 | -0.105 | -0.930 |

Entry slippage changes executed entry, original risk and the target mechanically. Exit slippage is adverse even on targets, matching the existing executor. Costs therefore are not simply a constant subtraction between slippage scenarios. Break-even fee per side is gross diagnostic P&L divided by twice completed diagnostics, and may be negative.

## Concentration and interpretation

| level_type | stop | target_r | net_usd | avg_net_r | positive_years | net_2022 | share_2022_of_net_pct | risk_points_max | risk_points_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | 88.800 | -0.005 | 2 | -176.140 | -198.356 | 310.000 | 33.250 |
| O15H | BREAK_CANDLE_HIGH | 2 | 1,180.300 | 0.005 | 2 | 1,514.360 | 128.303 | 310.000 | 33.250 |
| O15H | LEVEL_RECLAIM | 1 | -921.200 | -0.086 | 2 | 618.860 | — | 287.750 | 21.000 |
| O15H | LEVEL_RECLAIM | 2 | -317.700 | -0.067 | 2 | 574.860 | — | 287.750 | 21.000 |
| O15L | BREAK_CANDLE_HIGH | 1 | -233.920 | -0.013 | 1 | -1,019.800 | — | 207.750 | 39.000 |
| O15L | BREAK_CANDLE_HIGH | 2 | 1,197.080 | -0.012 | 2 | -229.800 | -19.197 | 207.750 | 39.000 |
| O15L | LEVEL_RECLAIM | 1 | 1,438.080 | -0.027 | 3 | 344.700 | 23.969 | 149.000 | 23.750 |
| O15L | LEVEL_RECLAIM | 2 | 2,591.580 | -0.039 | 3 | 735.200 | 28.369 | 149.000 | 23.750 |
| O5H | BREAK_CANDLE_HIGH | 1 | -2,882.060 | -0.020 | 0 | -1,646.180 | — | 310.000 | 36.250 |
| O5H | BREAK_CANDLE_HIGH | 2 | -3,140.560 | -0.062 | 0 | -665.680 | — | 310.000 | 36.250 |
| O5H | LEVEL_RECLAIM | 1 | -4,240.060 | -0.139 | 0 | -2,061.680 | — | 287.750 | 21.750 |
| O5H | LEVEL_RECLAIM | 2 | -2,265.560 | -0.087 | 1 | -1,007.180 | — | 287.750 | 21.750 |
| O5L | BREAK_CANDLE_HIGH | 1 | -3,478.720 | -0.053 | 1 | -469.420 | — | 310.000 | 41.750 |
| O5L | BREAK_CANDLE_HIGH | 2 | -1,842.220 | -0.067 | 1 | -393.920 | — | 310.000 | 41.750 |
| O5L | LEVEL_RECLAIM | 1 | -1,683.720 | -0.084 | 2 | 736.080 | — | 196.500 | 24.750 |
| O5L | LEVEL_RECLAIM | 2 | -2,686.720 | -0.099 | 2 | 843.080 | — | 196.500 | 24.750 |
| PDH | BREAK_CANDLE_HIGH | 1 | -4,597.260 | -0.098 | 0 | -2,589.360 | — | 310.000 | 32.625 |
| PDH | BREAK_CANDLE_HIGH | 2 | -3,257.260 | -0.126 | 0 | -1,453.860 | — | 310.000 | 32.625 |
| PDH | LEVEL_RECLAIM | 1 | -2,810.760 | -0.145 | 0 | -1,108.360 | — | 189.250 | 20.000 |
| PDH | LEVEL_RECLAIM | 2 | -2,752.260 | -0.178 | 0 | -1,409.860 | — | 189.250 | 20.000 |
| PDL | BREAK_CANDLE_HIGH | 1 | -2,543.140 | -0.042 | 0 | -119.760 | — | 200.250 | 39.500 |
| PDL | BREAK_CANDLE_HIGH | 2 | -3,047.140 | -0.045 | 1 | 165.740 | — | 200.250 | 39.500 |
| PDL | LEVEL_RECLAIM | 1 | -1,617.640 | -0.064 | 1 | -351.260 | — | 155.500 | 23.750 |
| PDL | LEVEL_RECLAIM | 2 | -1,903.140 | -0.104 | 1 | 303.740 | — | 155.500 | 23.750 |
| PMH | BREAK_CANDLE_HIGH | 1 | -2,667.320 | -0.038 | 1 | -199.860 | — | 310.000 | 34.000 |
| PMH | BREAK_CANDLE_HIGH | 2 | -571.820 | -0.022 | 2 | 1,709.140 | — | 310.000 | 34.000 |
| PMH | LEVEL_RECLAIM | 1 | -3,246.320 | -0.196 | 0 | -622.860 | — | 294.500 | 21.000 |
| PMH | LEVEL_RECLAIM | 2 | -3,345.820 | -0.211 | 1 | 401.140 | — | 294.500 | 21.000 |
| PML | BREAK_CANDLE_HIGH | 1 | -2,960.620 | -0.082 | 1 | -603.000 | — | 261.000 | 40.500 |
| PML | BREAK_CANDLE_HIGH | 2 | -1,982.620 | -0.093 | 1 | 40.500 | — | 261.000 | 40.500 |
| PML | LEVEL_RECLAIM | 1 | -1,812.120 | -0.091 | 2 | -759.500 | — | 150.750 | 24.000 |
| PML | LEVEL_RECLAIM | 2 | -1,675.620 | -0.085 | 1 | -887.500 | — | 150.750 | 24.000 |

A positive dollar result with negative average R may reflect large-risk observations rather than consistent opportunity. Shares above 100% mean other years offset the profitable year; a missing share means aggregate net was not positive. The top-five-risk observations and their signed contributions are retained in largest_risk_diagnostics.csv without exclusions.

The previous favorable-50-point associations do not automatically imply a useful risk path. This audit does not select a best level, stop or target by in-sample profit. Review yearly consistency, stop logic, adverse paths and fee sensitivity before deciding whether to freeze one controlled strategy. Validation and OOS remain unqueried.

## Reproducibility and complete exports

frozen protocol.json; exact_raw_events.csv; source_reconciliation.csv; all_event_paths.csv; all_target_executions.csv; population_and_quality.csv; stop_path_comparison.csv; fixed_target_diagnostics.csv; yearly_stability.csv; fee_slippage_sensitivity.csv; descriptive_context.csv; largest_risk_diagnostics.csv; ambiguity_audit.csv; recommendation.json; execution_verification.json. All observations are retained locally. The bundle includes aggregate reports and an index linking full raw artifacts by hash; no sampling is used.

The report’s standalone viewer is available from the Lab Research page. Production strategies, stored runs, source studies and market-data files are unchanged.

## What waiting changes

Original break entries: 11,364. Immediate full-hold confirmations: 4,784. Original roots without confirmation: 6,580. The unconfirmed roots were not discarded from the opportunity audit. Both entry versions use exactly the same absolute stops; Stop B remains the original break candle high. Risk and targets change with the later entry price.

MATCHED_IMMEDIATE conditions the old results on a subsequently observed full hold. It is an explanatory comparison, not a tradable filter at the original break close and not causal proof of improvement. OMITTED_IMMEDIATE shows the original outcomes on roots that did not confirm. Original trades can already have exited during the confirmation candle; their results remain in the comparison.

| level_type | status | events |
| --- | --- | --- |
| O15H | FULL_HOLD | 628 |
| O15H | NEXT_BAR_NOT_FULLY_BELOW | 832 |
| O15H | NO_ADJACENT_SESSION_BAR | 10 |
| O15L | FULL_HOLD | 734 |
| O15L | NEXT_BAR_NOT_FULLY_BELOW | 1046 |
| O15L | NO_ADJACENT_SESSION_BAR | 18 |
| O5H | FULL_HOLD | 692 |
| O5H | NEXT_BAR_NOT_FULLY_BELOW | 935 |
| O5H | NO_ADJACENT_SESSION_BAR | 9 |
| O5L | FULL_HOLD | 841 |
| O5L | NEXT_BAR_NOT_FULLY_BELOW | 1152 |
| O5L | NO_ADJACENT_SESSION_BAR | 17 |
| PDH | FULL_HOLD | 366 |
| PDH | NEXT_BAR_NOT_FULLY_BELOW | 512 |
| PDH | NO_ADJACENT_SESSION_BAR | 8 |
| PDL | FULL_HOLD | 391 |
| PDL | NEXT_BAR_NOT_FULLY_BELOW | 517 |
| PDL | NO_ADJACENT_SESSION_BAR | 9 |
| PMH | FULL_HOLD | 499 |
| PMH | NEXT_BAR_NOT_FULLY_BELOW | 648 |
| PMH | NO_ADJACENT_SESSION_BAR | 15 |
| PML | FULL_HOLD | 633 |
| PML | NEXT_BAR_NOT_FULLY_BELOW | 837 |
| PML | NO_ADJACENT_SESSION_BAR | 15 |

| level_type | stop | target_r | cohort | events | valid_trades | net_usd | pf | avg_net_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | ALL_IMMEDIATE | 1470 | 1460 | -75.100 | 0.998 | -0.051 |
| O15H | BREAK_CANDLE_HIGH | 2 | ALL_IMMEDIATE | 1470 | 1460 | 1,715.400 | 1.036 | -0.023 |
| O15H | LEVEL_RECLAIM | 1 | ALL_IMMEDIATE | 1470 | 1460 | -3,002.600 | 0.833 | -0.404 |
| O15H | LEVEL_RECLAIM | 2 | ALL_IMMEDIATE | 1470 | 1460 | -3,135.100 | 0.867 | -0.338 |
| O15L | BREAK_CANDLE_HIGH | 1 | ALL_IMMEDIATE | 1798 | 1780 | -4,783.800 | 0.914 | -0.051 |
| O15L | BREAK_CANDLE_HIGH | 2 | ALL_IMMEDIATE | 1798 | 1780 | -7,530.300 | 0.895 | -0.080 |
| O15L | LEVEL_RECLAIM | 1 | ALL_IMMEDIATE | 1798 | 1780 | -5,275.800 | 0.792 | -0.399 |
| O15L | LEVEL_RECLAIM | 2 | ALL_IMMEDIATE | 1798 | 1780 | -4,405.800 | 0.863 | -0.338 |
| O5H | BREAK_CANDLE_HIGH | 1 | ALL_IMMEDIATE | 1636 | 1627 | -4,110.920 | 0.912 | -0.080 |
| O5H | BREAK_CANDLE_HIGH | 2 | ALL_IMMEDIATE | 1636 | 1627 | -4,054.920 | 0.933 | -0.073 |
| O5H | LEVEL_RECLAIM | 1 | ALL_IMMEDIATE | 1636 | 1627 | -3,636.920 | 0.833 | -0.426 |
| O5H | LEVEL_RECLAIM | 2 | ALL_IMMEDIATE | 1636 | 1627 | -6,371.420 | 0.783 | -0.397 |
| O5L | BREAK_CANDLE_HIGH | 1 | ALL_IMMEDIATE | 2010 | 1993 | -8,420.780 | 0.872 | -0.066 |
| O5L | BREAK_CANDLE_HIGH | 2 | ALL_IMMEDIATE | 2010 | 1993 | -12,025.280 | 0.859 | -0.107 |
| O5L | LEVEL_RECLAIM | 1 | ALL_IMMEDIATE | 2010 | 1993 | -5,653.780 | 0.804 | -0.384 |
| O5L | LEVEL_RECLAIM | 2 | ALL_IMMEDIATE | 2010 | 1993 | -4,431.780 | 0.879 | -0.325 |
| PDH | BREAK_CANDLE_HIGH | 1 | ALL_IMMEDIATE | 886 | 878 | -1,284.880 | 0.945 | -0.053 |
| PDH | BREAK_CANDLE_HIGH | 2 | ALL_IMMEDIATE | 886 | 878 | -2,429.880 | 0.922 | -0.064 |
| PDH | LEVEL_RECLAIM | 1 | ALL_IMMEDIATE | 886 | 878 | -2,050.380 | 0.817 | -0.441 |
| PDH | LEVEL_RECLAIM | 2 | ALL_IMMEDIATE | 886 | 878 | -3,396.880 | 0.773 | -0.439 |
| PDL | BREAK_CANDLE_HIGH | 1 | ALL_IMMEDIATE | 917 | 908 | -4,382.180 | 0.862 | -0.074 |
| PDL | BREAK_CANDLE_HIGH | 2 | ALL_IMMEDIATE | 917 | 908 | -3,629.180 | 0.908 | -0.047 |
| PDL | LEVEL_RECLAIM | 1 | ALL_IMMEDIATE | 917 | 908 | -3,589.180 | 0.743 | -0.371 |
| PDL | LEVEL_RECLAIM | 2 | ALL_IMMEDIATE | 917 | 908 | -2,997.680 | 0.828 | -0.301 |
| PMH | BREAK_CANDLE_HIGH | 1 | ALL_IMMEDIATE | 1162 | 1147 | 1,493.880 | 1.051 | -0.022 |
| PMH | BREAK_CANDLE_HIGH | 2 | ALL_IMMEDIATE | 1162 | 1147 | -1,913.620 | 0.952 | -0.078 |
| PMH | LEVEL_RECLAIM | 1 | ALL_IMMEDIATE | 1162 | 1147 | -2,765.120 | 0.817 | -0.436 |
| PMH | LEVEL_RECLAIM | 2 | ALL_IMMEDIATE | 1162 | 1147 | -4,093.120 | 0.796 | -0.429 |
| PML | BREAK_CANDLE_HIGH | 1 | ALL_IMMEDIATE | 1485 | 1470 | -6,226.700 | 0.875 | -0.063 |
| PML | BREAK_CANDLE_HIGH | 2 | ALL_IMMEDIATE | 1485 | 1470 | -4,916.200 | 0.921 | -0.059 |
| PML | LEVEL_RECLAIM | 1 | ALL_IMMEDIATE | 1485 | 1470 | -4,992.200 | 0.770 | -0.379 |
| PML | LEVEL_RECLAIM | 2 | ALL_IMMEDIATE | 1485 | 1470 | -2,447.200 | 0.909 | -0.304 |
| O15H | BREAK_CANDLE_HIGH | 1 | MATCHED_IMMEDIATE | 628 | 628 | 10,508.120 | 1.790 | 0.365 |
| O15H | BREAK_CANDLE_HIGH | 2 | MATCHED_IMMEDIATE | 628 | 628 | 11,674.120 | 1.569 | 0.405 |
| O15H | LEVEL_RECLAIM | 1 | MATCHED_IMMEDIATE | 628 | 628 | 7,718.120 | 2.225 | 0.482 |
| O15H | LEVEL_RECLAIM | 2 | MATCHED_IMMEDIATE | 628 | 628 | 8,816.120 | 1.801 | 0.750 |
| O15L | BREAK_CANDLE_HIGH | 1 | MATCHED_IMMEDIATE | 734 | 734 | 11,318.360 | 1.567 | 0.277 |
| O15L | BREAK_CANDLE_HIGH | 2 | MATCHED_IMMEDIATE | 734 | 734 | 10,548.360 | 1.361 | 0.283 |
| O15L | LEVEL_RECLAIM | 1 | MATCHED_IMMEDIATE | 734 | 734 | 10,045.360 | 2.160 | 0.448 |
| O15L | LEVEL_RECLAIM | 2 | MATCHED_IMMEDIATE | 734 | 734 | 11,950.860 | 1.826 | 0.643 |
| O5H | BREAK_CANDLE_HIGH | 1 | MATCHED_IMMEDIATE | 692 | 692 | 9,541.680 | 1.541 | 0.311 |
| O5H | BREAK_CANDLE_HIGH | 2 | MATCHED_IMMEDIATE | 692 | 692 | 8,938.180 | 1.338 | 0.324 |
| O5H | LEVEL_RECLAIM | 1 | MATCHED_IMMEDIATE | 692 | 692 | 8,576.680 | 2.056 | 0.452 |
| O5H | LEVEL_RECLAIM | 2 | MATCHED_IMMEDIATE | 692 | 692 | 7,613.680 | 1.524 | 0.635 |
| O5L | BREAK_CANDLE_HIGH | 1 | MATCHED_IMMEDIATE | 841 | 841 | 13,869.140 | 1.602 | 0.283 |
| O5L | BREAK_CANDLE_HIGH | 2 | MATCHED_IMMEDIATE | 841 | 841 | 13,075.140 | 1.379 | 0.261 |
| O5L | LEVEL_RECLAIM | 1 | MATCHED_IMMEDIATE | 841 | 841 | 11,308.640 | 2.112 | 0.465 |
| O5L | LEVEL_RECLAIM | 2 | MATCHED_IMMEDIATE | 841 | 841 | 14,401.140 | 1.871 | 0.692 |
| PDH | BREAK_CANDLE_HIGH | 1 | MATCHED_IMMEDIATE | 366 | 366 | 5,163.640 | 1.590 | 0.266 |
| PDH | BREAK_CANDLE_HIGH | 2 | MATCHED_IMMEDIATE | 366 | 366 | 4,095.640 | 1.304 | 0.272 |
| PDH | LEVEL_RECLAIM | 1 | MATCHED_IMMEDIATE | 366 | 366 | 4,217.140 | 2.009 | 0.395 |
| PDH | LEVEL_RECLAIM | 2 | MATCHED_IMMEDIATE | 366 | 366 | 3,897.140 | 1.538 | 0.565 |
| PDL | BREAK_CANDLE_HIGH | 1 | MATCHED_IMMEDIATE | 391 | 391 | 6,100.640 | 1.541 | 0.293 |
| PDL | BREAK_CANDLE_HIGH | 2 | MATCHED_IMMEDIATE | 391 | 391 | 6,465.640 | 1.405 | 0.356 |
| PDL | LEVEL_RECLAIM | 1 | MATCHED_IMMEDIATE | 391 | 391 | 3,981.640 | 1.716 | 0.459 |
| PDL | LEVEL_RECLAIM | 2 | MATCHED_IMMEDIATE | 391 | 391 | 5,167.140 | 1.613 | 0.682 |
| PMH | BREAK_CANDLE_HIGH | 1 | MATCHED_IMMEDIATE | 499 | 499 | 7,874.460 | 1.662 | 0.258 |
| PMH | BREAK_CANDLE_HIGH | 2 | MATCHED_IMMEDIATE | 499 | 499 | 5,769.460 | 1.308 | 0.225 |
| PMH | LEVEL_RECLAIM | 1 | MATCHED_IMMEDIATE | 499 | 499 | 5,119.460 | 1.806 | 0.371 |
| PMH | LEVEL_RECLAIM | 2 | MATCHED_IMMEDIATE | 499 | 499 | 4,668.460 | 1.442 | 0.484 |
| PML | BREAK_CANDLE_HIGH | 1 | MATCHED_IMMEDIATE | 633 | 633 | 9,385.820 | 1.518 | 0.269 |
| PML | BREAK_CANDLE_HIGH | 2 | MATCHED_IMMEDIATE | 633 | 633 | 11,822.320 | 1.469 | 0.308 |
| PML | LEVEL_RECLAIM | 1 | MATCHED_IMMEDIATE | 633 | 633 | 6,381.820 | 1.703 | 0.413 |
| PML | LEVEL_RECLAIM | 2 | MATCHED_IMMEDIATE | 633 | 633 | 10,189.320 | 1.773 | 0.679 |
| O15H | BREAK_CANDLE_HIGH | 1 | OMITTED_IMMEDIATE | 842 | 832 | -10,583.220 | 0.552 | -0.365 |
| O15H | BREAK_CANDLE_HIGH | 2 | OMITTED_IMMEDIATE | 842 | 832 | -9,958.720 | 0.641 | -0.347 |
| O15H | LEVEL_RECLAIM | 1 | OMITTED_IMMEDIATE | 842 | 832 | -10,720.720 | 0.085 | -1.072 |
| O15H | LEVEL_RECLAIM | 2 | OMITTED_IMMEDIATE | 842 | 832 | -11,951.220 | 0.055 | -1.158 |
| O15L | BREAK_CANDLE_HIGH | 1 | OMITTED_IMMEDIATE | 1064 | 1046 | -16,102.160 | 0.550 | -0.281 |
| O15L | BREAK_CANDLE_HIGH | 2 | OMITTED_IMMEDIATE | 1064 | 1046 | -18,078.660 | 0.578 | -0.335 |
| O15L | LEVEL_RECLAIM | 1 | OMITTED_IMMEDIATE | 1064 | 1046 | -15,321.160 | 0.086 | -0.993 |
| O15L | LEVEL_RECLAIM | 2 | OMITTED_IMMEDIATE | 1064 | 1046 | -16,356.660 | 0.081 | -1.027 |
| O5H | BREAK_CANDLE_HIGH | 1 | OMITTED_IMMEDIATE | 944 | 935 | -13,652.600 | 0.531 | -0.370 |
| O5H | BREAK_CANDLE_HIGH | 2 | OMITTED_IMMEDIATE | 944 | 935 | -12,993.100 | 0.620 | -0.368 |
| O5H | LEVEL_RECLAIM | 1 | OMITTED_IMMEDIATE | 944 | 935 | -12,213.600 | 0.102 | -1.075 |
| O5H | LEVEL_RECLAIM | 2 | OMITTED_IMMEDIATE | 944 | 935 | -13,985.100 | 0.059 | -1.161 |
| O5L | BREAK_CANDLE_HIGH | 1 | OMITTED_IMMEDIATE | 1169 | 1152 | -22,289.920 | 0.480 | -0.320 |
| O5L | BREAK_CANDLE_HIGH | 2 | OMITTED_IMMEDIATE | 1169 | 1152 | -25,100.420 | 0.504 | -0.376 |
| O5L | LEVEL_RECLAIM | 1 | OMITTED_IMMEDIATE | 1169 | 1152 | -16,962.420 | 0.092 | -1.004 |
| O5L | LEVEL_RECLAIM | 2 | OMITTED_IMMEDIATE | 1169 | 1152 | -18,832.920 | 0.065 | -1.067 |
| PDH | BREAK_CANDLE_HIGH | 1 | OMITTED_IMMEDIATE | 520 | 512 | -6,448.520 | 0.561 | -0.281 |
| PDH | BREAK_CANDLE_HIGH | 2 | OMITTED_IMMEDIATE | 520 | 512 | -6,525.520 | 0.629 | -0.305 |
| PDH | LEVEL_RECLAIM | 1 | OMITTED_IMMEDIATE | 520 | 512 | -6,267.520 | 0.107 | -1.039 |
| PDH | LEVEL_RECLAIM | 2 | OMITTED_IMMEDIATE | 520 | 512 | -7,294.020 | 0.058 | -1.156 |
| PDL | BREAK_CANDLE_HIGH | 1 | OMITTED_IMMEDIATE | 526 | 517 | -10,482.820 | 0.488 | -0.352 |
| PDL | BREAK_CANDLE_HIGH | 2 | OMITTED_IMMEDIATE | 526 | 517 | -10,094.820 | 0.566 | -0.352 |
| PDL | LEVEL_RECLAIM | 1 | OMITTED_IMMEDIATE | 526 | 517 | -7,570.820 | 0.096 | -0.998 |
| PDL | LEVEL_RECLAIM | 2 | OMITTED_IMMEDIATE | 526 | 517 | -8,164.820 | 0.089 | -1.045 |
| PMH | BREAK_CANDLE_HIGH | 1 | OMITTED_IMMEDIATE | 663 | 648 | -6,380.580 | 0.630 | -0.239 |
| PMH | BREAK_CANDLE_HIGH | 2 | OMITTED_IMMEDIATE | 663 | 648 | -7,683.080 | 0.640 | -0.311 |
| PMH | LEVEL_RECLAIM | 1 | OMITTED_IMMEDIATE | 663 | 648 | -7,884.580 | 0.102 | -1.058 |
| PMH | LEVEL_RECLAIM | 2 | OMITTED_IMMEDIATE | 663 | 648 | -8,761.580 | 0.079 | -1.133 |
| PML | BREAK_CANDLE_HIGH | 1 | OMITTED_IMMEDIATE | 852 | 837 | -15,612.520 | 0.508 | -0.315 |
| PML | BREAK_CANDLE_HIGH | 2 | OMITTED_IMMEDIATE | 852 | 837 | -16,738.520 | 0.552 | -0.337 |
| PML | LEVEL_RECLAIM | 1 | OMITTED_IMMEDIATE | 852 | 837 | -11,374.020 | 0.101 | -0.979 |
| PML | LEVEL_RECLAIM | 2 | OMITTED_IMMEDIATE | 852 | 837 | -12,636.520 | 0.078 | -1.047 |
| O15H | BREAK_CANDLE_HIGH | 1 | CONFIRMED | 628 | 620 | 88.800 | 1.004 | -0.005 |
| O15H | BREAK_CANDLE_HIGH | 2 | CONFIRMED | 628 | 620 | 1,180.300 | 1.041 | 0.005 |
| O15H | LEVEL_RECLAIM | 1 | CONFIRMED | 628 | 620 | -921.200 | 0.944 | -0.086 |
| O15H | LEVEL_RECLAIM | 2 | CONFIRMED | 628 | 620 | -317.700 | 0.985 | -0.067 |
| O15L | BREAK_CANDLE_HIGH | 1 | CONFIRMED | 734 | 727 | -233.920 | 0.993 | -0.013 |
| O15L | BREAK_CANDLE_HIGH | 2 | CONFIRMED | 734 | 727 | 1,197.080 | 1.031 | -0.012 |
| O15L | LEVEL_RECLAIM | 1 | CONFIRMED | 734 | 727 | 1,438.080 | 1.072 | -0.027 |
| O15L | LEVEL_RECLAIM | 2 | CONFIRMED | 734 | 727 | 2,591.580 | 1.100 | -0.039 |
| O5H | BREAK_CANDLE_HIGH | 1 | CONFIRMED | 692 | 686 | -2,882.060 | 0.900 | -0.020 |
| O5H | BREAK_CANDLE_HIGH | 2 | CONFIRMED | 692 | 686 | -3,140.560 | 0.912 | -0.062 |
| O5H | LEVEL_RECLAIM | 1 | CONFIRMED | 692 | 686 | -4,240.060 | 0.797 | -0.139 |
| O5H | LEVEL_RECLAIM | 2 | CONFIRMED | 692 | 686 | -2,265.560 | 0.910 | -0.087 |
| O5L | BREAK_CANDLE_HIGH | 1 | CONFIRMED | 841 | 832 | -3,478.720 | 0.910 | -0.053 |
| O5L | BREAK_CANDLE_HIGH | 2 | CONFIRMED | 841 | 832 | -1,842.220 | 0.961 | -0.067 |
| O5L | LEVEL_RECLAIM | 1 | CONFIRMED | 841 | 832 | -1,683.720 | 0.934 | -0.084 |
| O5L | LEVEL_RECLAIM | 2 | CONFIRMED | 841 | 832 | -2,686.720 | 0.919 | -0.099 |
| PDH | BREAK_CANDLE_HIGH | 1 | CONFIRMED | 366 | 356 | -4,597.260 | 0.717 | -0.098 |
| PDH | BREAK_CANDLE_HIGH | 2 | CONFIRMED | 366 | 356 | -3,257.260 | 0.825 | -0.126 |
| PDH | LEVEL_RECLAIM | 1 | CONFIRMED | 366 | 356 | -2,810.760 | 0.743 | -0.145 |
| PDH | LEVEL_RECLAIM | 2 | CONFIRMED | 366 | 356 | -2,752.260 | 0.793 | -0.178 |
| PDL | BREAK_CANDLE_HIGH | 1 | CONFIRMED | 391 | 384 | -2,543.140 | 0.856 | -0.042 |
| PDL | BREAK_CANDLE_HIGH | 2 | CONFIRMED | 391 | 384 | -3,047.140 | 0.860 | -0.045 |
| PDL | LEVEL_RECLAIM | 1 | CONFIRMED | 391 | 384 | -1,617.640 | 0.861 | -0.064 |
| PDL | LEVEL_RECLAIM | 2 | CONFIRMED | 391 | 384 | -1,903.140 | 0.872 | -0.104 |
| PMH | BREAK_CANDLE_HIGH | 1 | CONFIRMED | 499 | 492 | -2,667.320 | 0.870 | -0.038 |
| PMH | BREAK_CANDLE_HIGH | 2 | CONFIRMED | 499 | 492 | -571.820 | 0.977 | -0.022 |
| PMH | LEVEL_RECLAIM | 1 | CONFIRMED | 499 | 492 | -3,246.320 | 0.779 | -0.196 |
| PMH | LEVEL_RECLAIM | 2 | CONFIRMED | 499 | 492 | -3,345.820 | 0.816 | -0.211 |
| PML | BREAK_CANDLE_HIGH | 1 | CONFIRMED | 633 | 622 | -2,960.620 | 0.896 | -0.082 |
| PML | BREAK_CANDLE_HIGH | 2 | CONFIRMED | 633 | 622 | -1,982.620 | 0.943 | -0.093 |
| PML | LEVEL_RECLAIM | 1 | CONFIRMED | 633 | 622 | -1,812.120 | 0.904 | -0.091 |
| PML | LEVEL_RECLAIM | 2 | CONFIRMED | 633 | 622 | -1,675.620 | 0.931 | -0.085 |

| level_type | stop | target_r | roots | complete_pairs | original_closed_by_delayed_entry | mean_risk_change | net_change_on_complete_pairs | average_r_change_on_complete_pairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | 628 | 620 | 188 | 9.658 | -10,191.500 | -0.370 |
| O15H | BREAK_CANDLE_HIGH | 2 | 628 | 620 | 48 | 9.658 | -10,278.500 | -0.401 |
| O15H | LEVEL_RECLAIM | 1 | 628 | 620 | 376 | 9.658 | -8,408.000 | -0.566 |
| O15H | LEVEL_RECLAIM | 2 | 628 | 620 | 225 | 9.658 | -8,919.500 | -0.818 |
| O15L | BREAK_CANDLE_HIGH | 1 | 734 | 727 | 152 | 9.541 | -11,476.000 | -0.289 |
| O15L | BREAK_CANDLE_HIGH | 2 | 734 | 727 | 32 | 9.541 | -9,275.000 | -0.293 |
| O15L | LEVEL_RECLAIM | 1 | 734 | 727 | 396 | 9.541 | -8,602.000 | -0.476 |
| O15L | LEVEL_RECLAIM | 2 | 734 | 727 | 199 | 9.541 | -9,325.000 | -0.682 |
| O5H | BREAK_CANDLE_HIGH | 1 | 692 | 686 | 192 | 9.715 | -12,305.000 | -0.332 |
| O5H | BREAK_CANDLE_HIGH | 2 | 692 | 686 | 44 | 9.715 | -11,983.000 | -0.389 |
| O5H | LEVEL_RECLAIM | 1 | 692 | 686 | 394 | 9.715 | -12,730.500 | -0.591 |
| O5H | LEVEL_RECLAIM | 2 | 692 | 686 | 221 | 9.715 | -9,761.500 | -0.723 |
| O5L | BREAK_CANDLE_HIGH | 1 | 841 | 832 | 193 | 10.698 | -17,251.000 | -0.338 |
| O5L | BREAK_CANDLE_HIGH | 2 | 841 | 832 | 40 | 10.698 | -14,830.000 | -0.330 |
| O5L | LEVEL_RECLAIM | 1 | 841 | 832 | 486 | 10.698 | -12,942.000 | -0.551 |
| O5L | LEVEL_RECLAIM | 2 | 841 | 832 | 250 | 10.698 | -16,992.500 | -0.793 |
| PDH | BREAK_CANDLE_HIGH | 1 | 366 | 356 | 98 | 9.489 | -9,542.000 | -0.367 |
| PDH | BREAK_CANDLE_HIGH | 2 | 366 | 356 | 32 | 9.489 | -7,113.000 | -0.400 |
| PDH | LEVEL_RECLAIM | 1 | 366 | 356 | 198 | 9.489 | -6,886.000 | -0.543 |
| PDH | LEVEL_RECLAIM | 2 | 366 | 356 | 117 | 9.489 | -6,473.500 | -0.747 |
| PDL | BREAK_CANDLE_HIGH | 1 | 391 | 384 | 88 | 9.359 | -8,423.000 | -0.335 |
| PDL | BREAK_CANDLE_HIGH | 2 | 391 | 384 | 23 | 9.359 | -9,316.500 | -0.402 |
| PDL | LEVEL_RECLAIM | 1 | 391 | 384 | 212 | 9.359 | -5,472.500 | -0.524 |
| PDL | LEVEL_RECLAIM | 2 | 391 | 384 | 125 | 9.359 | -6,953.000 | -0.787 |
| PMH | BREAK_CANDLE_HIGH | 1 | 499 | 492 | 133 | 9.222 | -10,357.000 | -0.297 |
| PMH | BREAK_CANDLE_HIGH | 2 | 499 | 492 | 31 | 9.222 | -6,156.500 | -0.246 |
| PMH | LEVEL_RECLAIM | 1 | 499 | 492 | 265 | 9.222 | -8,272.500 | -0.567 |
| PMH | LEVEL_RECLAIM | 2 | 499 | 492 | 149 | 9.222 | -7,849.000 | -0.694 |
| PML | BREAK_CANDLE_HIGH | 1 | 633 | 622 | 150 | 9.511 | -12,079.500 | -0.350 |
| PML | BREAK_CANDLE_HIGH | 2 | 633 | 622 | 33 | 9.511 | -13,547.500 | -0.401 |
| PML | LEVEL_RECLAIM | 1 | 633 | 622 | 335 | 9.511 | -7,952.500 | -0.503 |
| PML | LEVEL_RECLAIM | 2 | 633 | 622 | 199 | 9.511 | -11,611.500 | -0.767 |

## Final verification

- 119 relevant backend/research/execution tests passed; 33 frontend tests passed; 3 isolated browser workflows passed (155 total).
- Production frontend build passed. Existing dependency/chunk-size warnings remain nonblocking.
- All 23 deterministic artifacts were byte-identical on a full native rerun. The aggregate ZIP also reproduced byte-for-byte.
- 56,628 executable diagnostics independently reconciled on each run. No production execution code changed.
- Repeat runtime: 147.651 seconds execution and 7.653 seconds reporting; 155.568 seconds total verification.
- Local artifacts: 146,786,071 bytes; aggregate ZIP: 929,166 bytes. Raw observations are unsampled and retained locally by indexed hash.
- Every original immediate-break artifact and original study/data identity was preserved. Saved-run, strategy, study and reveal-state metadata matched before/after.
- Validation and OOS outcomes were not accessed. No paid data was downloaded.

Open the Lab Research page → Next-candle full-hold feasibility, or `/api/research/full-hold-feasibility/files/study.html` on the local Lab. The previous immediate-break report remains separately available.
