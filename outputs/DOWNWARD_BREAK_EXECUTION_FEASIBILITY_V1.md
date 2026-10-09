# Downward-break execution feasibility — Development v1

**DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY.** Eight fixed daily levels, immediate confirmed downward-break SHORT entry, two frozen structural stops and fixed original 1R/2R targets. Actual Webull fees; no signal filters or management. All 2020–2023 signals are retained, including later failures and retests.

## What was tested

Stop A (LEVEL_RECLAIM) is one tick above the broken level. Stop B (BREAK_CANDLE_HIGH) is one tick above the break candle’s high. Neither uses future data. The level stop can be narrower than the signal candle; pre-entry movement through it does not count as a stop-out. One micro, $2/point, $0.73/side fees. Primary one adverse entry tick and one adverse exit tick; zero/two-tick sensitivity uses the same signals.

Exact reconciliation: **11,364 raw signals on 970 dates**. 135,156 native fills/missing-data decisions were checked against an independent simulation. The production executor is unchanged.

**These are independently evaluated, often overlapping event diagnostics.** There is no single-position/day policy or capital allocation. Dollar totals, trade counts and cumulative closed-result drawdowns must not be presented as a live portfolio backtest. No aggregate across all levels is used to choose a winner.

## Population and future-data coverage

| level_type | raw_events | unique_dates | atr_unavailable | no_post_entry_minutes | complete_15m | complete_30m | complete_60m | future_gap_present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | 1470 | 570 | 0 | 10 | 1418 | 1370 | 1283 | 1 |
| O15L | 1798 | 672 | 3 | 18 | 1740 | 1697 | 1607 | 0 |
| O5H | 1636 | 626 | 1 | 9 | 1588 | 1539 | 1457 | 1 |
| O5L | 2010 | 751 | 3 | 17 | 1952 | 1903 | 1818 | 0 |
| PDH | 886 | 357 | 0 | 8 | 853 | 820 | 774 | 0 |
| PDL | 917 | 352 | 3 | 9 | 876 | 836 | 771 | 0 |
| PMH | 1162 | 466 | 0 | 15 | 1122 | 1096 | 1022 | 0 |
| PML | 1485 | 562 | 0 | 15 | 1434 | 1401 | 1329 | 0 |

ATR missingness never excludes fixed-risk execution. Causal events at the close remain in raw counts but cannot own a post-close minute. A missing future minute affects only simulations still open at that minute. Fifteen/thirty/sixty-minute descriptive denominators require complete horizons independently of early trade exits.

## Primary execution diagnostics: all levels and both stops/targets

| level_type | stop | target_r | events | valid_trades | wins | losses | win_pct | gross_usd | fees_usd | net_usd | pf | avg_net_r | positive_years | max_closed_diagnostic_dd_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | 1470 | 1460 | 739 | 721 | 50.616 | 2,056.500 | 2,131.600 | -75.100 | 0.998 | -0.051 | 1 | 1,999.840 |
| O15H | BREAK_CANDLE_HIGH | 2 | 1470 | 1460 | 524 | 936 | 35.890 | 3,847.000 | 2,131.600 | 1,715.400 | 1.036 | -0.023 | 2 | 4,544.180 |
| O15H | LEVEL_RECLAIM | 1 | 1470 | 1460 | 610 | 850 | 41.781 | -871.000 | 2,131.600 | -3,002.600 | 0.833 | -0.404 | 0 | 3,144.080 |
| O15H | LEVEL_RECLAIM | 2 | 1470 | 1460 | 445 | 1015 | 30.479 | -1,003.500 | 2,131.600 | -3,135.100 | 0.867 | -0.338 | 0 | 3,645.200 |
| O15L | BREAK_CANDLE_HIGH | 1 | 1798 | 1780 | 886 | 894 | 49.775 | -2,185.000 | 2,598.800 | -4,783.800 | 0.914 | -0.051 | 1 | 7,035.540 |
| O15L | BREAK_CANDLE_HIGH | 2 | 1798 | 1780 | 594 | 1186 | 33.371 | -4,931.500 | 2,598.800 | -7,530.300 | 0.895 | -0.080 | 0 | 9,172.840 |
| O15L | LEVEL_RECLAIM | 1 | 1798 | 1780 | 718 | 1062 | 40.337 | -2,677.000 | 2,598.800 | -5,275.800 | 0.792 | -0.399 | 0 | 5,297.840 |
| O15L | LEVEL_RECLAIM | 2 | 1798 | 1780 | 518 | 1262 | 29.101 | -1,807.000 | 2,598.800 | -4,405.800 | 0.863 | -0.338 | 1 | 4,451.840 |
| O5H | BREAK_CANDLE_HIGH | 1 | 1636 | 1627 | 794 | 833 | 48.801 | -1,735.500 | 2,375.420 | -4,110.920 | 0.912 | -0.080 | 1 | 5,517.980 |
| O5H | BREAK_CANDLE_HIGH | 2 | 1636 | 1627 | 551 | 1076 | 33.866 | -1,679.500 | 2,375.420 | -4,054.920 | 0.933 | -0.073 | 1 | 7,742.360 |
| O5H | LEVEL_RECLAIM | 1 | 1636 | 1627 | 659 | 968 | 40.504 | -1,261.500 | 2,375.420 | -3,636.920 | 0.833 | -0.426 | 1 | 3,697.320 |
| O5H | LEVEL_RECLAIM | 2 | 1636 | 1627 | 459 | 1168 | 28.211 | -3,996.000 | 2,375.420 | -6,371.420 | 0.783 | -0.397 | 0 | 6,641.700 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2010 | 1993 | 976 | 1017 | 48.971 | -5,511.000 | 2,909.780 | -8,420.780 | 0.872 | -0.066 | 1 | 11,640.140 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2010 | 1993 | 644 | 1349 | 32.313 | -9,115.500 | 2,909.780 | -12,025.280 | 0.859 | -0.107 | 0 | 14,965.100 |
| O5L | LEVEL_RECLAIM | 1 | 2010 | 1993 | 823 | 1170 | 41.295 | -2,744.000 | 2,909.780 | -5,653.780 | 0.804 | -0.384 | 0 | 6,988.180 |
| O5L | LEVEL_RECLAIM | 2 | 2010 | 1993 | 594 | 1399 | 29.804 | -1,522.000 | 2,909.780 | -4,431.780 | 0.879 | -0.325 | 0 | 5,620.240 |
| PDH | BREAK_CANDLE_HIGH | 1 | 886 | 878 | 438 | 440 | 49.886 | -3.000 | 1,281.880 | -1,284.880 | 0.945 | -0.053 | 2 | 3,243.500 |
| PDH | BREAK_CANDLE_HIGH | 2 | 886 | 878 | 296 | 582 | 33.713 | -1,148.000 | 1,281.880 | -2,429.880 | 0.922 | -0.064 | 1 | 3,880.580 |
| PDH | LEVEL_RECLAIM | 1 | 886 | 878 | 344 | 534 | 39.180 | -768.500 | 1,281.880 | -2,050.380 | 0.817 | -0.441 | 1 | 2,551.000 |
| PDH | LEVEL_RECLAIM | 2 | 886 | 878 | 234 | 644 | 26.651 | -2,115.000 | 1,281.880 | -3,396.880 | 0.773 | -0.439 | 0 | 3,901.500 |
| PDL | BREAK_CANDLE_HIGH | 1 | 917 | 908 | 442 | 466 | 48.678 | -3,056.500 | 1,325.680 | -4,382.180 | 0.862 | -0.074 | 1 | 5,313.640 |
| PDL | BREAK_CANDLE_HIGH | 2 | 917 | 908 | 323 | 585 | 35.573 | -2,303.500 | 1,325.680 | -3,629.180 | 0.908 | -0.047 | 1 | 4,875.700 |
| PDL | LEVEL_RECLAIM | 1 | 917 | 908 | 382 | 526 | 42.070 | -2,263.500 | 1,325.680 | -3,589.180 | 0.743 | -0.371 | 0 | 3,823.960 |
| PDL | LEVEL_RECLAIM | 2 | 917 | 908 | 280 | 628 | 30.837 | -1,672.000 | 1,325.680 | -2,997.680 | 0.828 | -0.301 | 1 | 3,602.960 |
| PMH | BREAK_CANDLE_HIGH | 1 | 1162 | 1147 | 593 | 554 | 51.700 | 3,168.500 | 1,674.620 | 1,493.880 | 1.051 | -0.022 | 2 | 2,117.400 |
| PMH | BREAK_CANDLE_HIGH | 2 | 1162 | 1147 | 387 | 760 | 33.740 | -239.000 | 1,674.620 | -1,913.620 | 0.952 | -0.078 | 1 | 3,195.900 |
| PMH | LEVEL_RECLAIM | 1 | 1162 | 1147 | 459 | 688 | 40.017 | -1,090.500 | 1,674.620 | -2,765.120 | 0.817 | -0.436 | 0 | 2,797.600 |
| PMH | LEVEL_RECLAIM | 2 | 1162 | 1147 | 310 | 837 | 27.027 | -2,418.500 | 1,674.620 | -4,093.120 | 0.796 | -0.429 | 1 | 4,127.200 |
| PML | BREAK_CANDLE_HIGH | 1 | 1485 | 1470 | 720 | 750 | 48.980 | -4,080.500 | 2,146.200 | -6,226.700 | 0.875 | -0.063 | 0 | 7,026.500 |
| PML | BREAK_CANDLE_HIGH | 2 | 1485 | 1470 | 505 | 965 | 34.354 | -2,770.000 | 2,146.200 | -4,916.200 | 0.921 | -0.059 | 0 | 8,397.400 |
| PML | LEVEL_RECLAIM | 1 | 1485 | 1470 | 610 | 860 | 41.497 | -2,846.000 | 2,146.200 | -4,992.200 | 0.770 | -0.379 | 0 | 5,259.660 |
| PML | LEVEL_RECLAIM | 2 | 1485 | 1470 | 450 | 1020 | 30.612 | -301.000 | 2,146.200 | -2,447.200 | 0.909 | -0.304 | 0 | 3,542.040 |

Of the 32 predeclared primary level/stop/target cases, 2 have positive diagnostic net dollars and 0 have positive average net R. These counts are descriptive, not corrected statistical evidence or selection criteria.

## Stop-bounded price paths

Paths here end at original stop or actual session close, without taking either target. They answer whether the move gets to 1R/2R before stopping. Separate fixed-target simulations above can exit earlier. Inclusive exit-minute MFE/MAE are bounds because ordering inside that minute is unknown. Same-minute favorable/stop touches count stop first.

| level_type | stop | execution_events | valid_executable_events | risk_points_median | risk_points_q25 | risk_points_q75 | risk_points_max | r1_before_stop_pct | r2_before_stop_pct | mfe_r_mean | mae_r_mean | stop_before_half_r_pct | r1_conflict_count | execution_data_unavailable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1470 | 1460 | 20.500 | 13.250 | 31.000 | 277.250 | 49.178 | 32.192 | 2.167 | 1.048 | 32.419 | 7 | 1 |
| O15H | LEVEL_RECLAIM | 1470 | 1460 | 7.250 | 3.250 | 14.250 | 186.500 | 41.849 | 29.863 | 3.882 | 1.827 | 48.699 | 221 | 0 |
| O15L | BREAK_CANDLE_HIGH | 1798 | 1780 | 25.500 | 16.500 | 39.000 | 277.250 | 48.820 | 29.551 | 2.018 | 1.027 | 32.978 | 2 | 0 |
| O15L | LEVEL_RECLAIM | 1798 | 1780 | 8.750 | 4.000 | 17.000 | 147.750 | 40.393 | 28.596 | 3.217 | 1.936 | 48.596 | 258 | 0 |
| O5H | BREAK_CANDLE_HIGH | 1636 | 1627 | 22.250 | 14.500 | 35.000 | 277.250 | 47.695 | 30.547 | 2.068 | 1.055 | 32.718 | 6 | 1 |
| O5H | LEVEL_RECLAIM | 1636 | 1627 | 8.000 | 3.750 | 15.500 | 186.500 | 40.504 | 27.720 | 3.645 | 1.926 | 50.338 | 269 | 0 |
| O5L | BREAK_CANDLE_HIGH | 2010 | 1993 | 26.250 | 17.000 | 40.750 | 277.250 | 47.918 | 29.002 | 1.970 | 1.033 | 32.363 | 3 | 0 |
| O5L | LEVEL_RECLAIM | 2010 | 1993 | 9.000 | 4.000 | 17.500 | 149.750 | 41.345 | 29.202 | 3.408 | 2.012 | 48.369 | 313 | 0 |
| PDH | BREAK_CANDLE_HIGH | 886 | 878 | 21.375 | 13.500 | 34.000 | 277.250 | 48.747 | 31.093 | 1.967 | 1.017 | 35.308 | 2 | 0 |
| PDH | LEVEL_RECLAIM | 886 | 878 | 7.500 | 3.500 | 15.250 | 232.500 | 39.522 | 26.082 | 3.121 | 1.830 | 50.228 | 133 | 0 |
| PDL | BREAK_CANDLE_HIGH | 917 | 908 | 29.125 | 18.188 | 43.062 | 277.250 | 46.145 | 28.965 | 1.801 | 1.010 | 32.819 | 3 | 0 |
| PDL | LEVEL_RECLAIM | 917 | 908 | 9.000 | 4.250 | 17.750 | 182.500 | 41.740 | 29.515 | 3.556 | 2.113 | 49.780 | 143 | 0 |
| PMH | BREAK_CANDLE_HIGH | 1162 | 1147 | 21.250 | 13.500 | 32.750 | 277.250 | 50.305 | 30.253 | 2.229 | 1.053 | 30.776 | 4 | 0 |
| PMH | LEVEL_RECLAIM | 1162 | 1147 | 7.750 | 3.500 | 15.000 | 198.750 | 39.843 | 26.504 | 2.999 | 1.851 | 48.649 | 183 | 0 |
| PML | BREAK_CANDLE_HIGH | 1485 | 1470 | 27.500 | 17.500 | 41.688 | 277.250 | 47.891 | 29.864 | 1.940 | 1.013 | 31.837 | 1 | 0 |
| PML | LEVEL_RECLAIM | 1485 | 1470 | 9.125 | 4.000 | 17.188 | 118.500 | 41.293 | 29.728 | 3.553 | 1.988 | 47.619 | 245 | 0 |

## Every Development year

| level_type | stop | target_r | year | events | valid_trades | win_pct | net_usd | pf | avg_net_r | max_closed_diagnostic_dd_usd | average_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | 2020 | 418 | 414 | 49.758 | 847.560 | 1.106 | -0.085 | 923.400 | 20.571 |
| O15H | BREAK_CANDLE_HIGH | 1 | 2021 | 334 | 332 | 50.000 | -27.720 | 0.996 | -0.066 | 997.240 | 22.814 |
| O15H | BREAK_CANDLE_HIGH | 1 | 2022 | 359 | 357 | 51.261 | -233.720 | 0.982 | -0.016 | 1,938.140 | 36.975 |
| O15H | BREAK_CANDLE_HIGH | 1 | 2023 | 359 | 357 | 51.541 | -661.220 | 0.922 | -0.032 | 1,146.500 | 23.373 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2020 | 418 | 414 | 34.541 | 2,092.560 | 1.199 | -0.074 | 1,285.860 | 20.571 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2021 | 334 | 332 | 36.145 | -597.220 | 0.939 | -0.046 | 2,504.580 | 22.814 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2022 | 359 | 357 | 35.014 | -159.720 | 0.991 | -0.015 | 4,261.960 | 36.975 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2023 | 359 | 357 | 38.095 | 379.780 | 1.036 | 0.048 | 1,296.740 | 23.373 |
| O15H | LEVEL_RECLAIM | 1 | 2020 | 418 | 414 | 37.440 | -1,124.440 | 0.734 | -0.525 | 1,171.260 | 8.610 |
| O15H | LEVEL_RECLAIM | 1 | 2021 | 334 | 332 | 41.566 | -422.220 | 0.885 | -0.417 | 647.960 | 10.331 |
| O15H | LEVEL_RECLAIM | 1 | 2022 | 359 | 357 | 45.098 | -950.220 | 0.848 | -0.265 | 974.040 | 16.056 |
| O15H | LEVEL_RECLAIM | 1 | 2023 | 359 | 357 | 43.697 | -505.720 | 0.869 | -0.389 | 645.980 | 10.080 |
| O15H | LEVEL_RECLAIM | 2 | 2020 | 418 | 414 | 25.604 | -1,496.440 | 0.732 | -0.516 | 1,524.680 | 8.610 |
| O15H | LEVEL_RECLAIM | 2 | 2021 | 334 | 332 | 29.819 | -60.220 | 0.987 | -0.367 | 608.160 | 10.331 |
| O15H | LEVEL_RECLAIM | 2 | 2022 | 359 | 357 | 30.812 | -1,457.220 | 0.826 | -0.250 | 2,235.920 | 16.056 |
| O15H | LEVEL_RECLAIM | 2 | 2023 | 359 | 357 | 36.415 | -121.220 | 0.976 | -0.192 | 711.400 | 10.080 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2020 | 447 | 441 | 50.113 | -1,663.860 | 0.867 | -0.049 | 2,610.840 | 27.640 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2021 | 435 | 428 | 48.598 | -1,443.380 | 0.882 | -0.079 | 1,996.420 | 27.094 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2022 | 483 | 480 | 47.708 | -2,880.800 | 0.858 | -0.079 | 4,261.920 | 40.089 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2023 | 433 | 431 | 52.900 | 1,204.240 | 1.114 | 0.007 | 927.720 | 26.632 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2020 | 447 | 441 | 33.787 | -2,789.360 | 0.829 | -0.078 | 3,247.800 | 27.640 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2021 | 435 | 428 | 35.047 | -630.880 | 0.959 | -0.031 | 2,100.240 | 27.094 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2022 | 483 | 480 | 33.542 | -2,415.800 | 0.905 | -0.065 | 4,057.300 | 40.089 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2023 | 433 | 431 | 31.090 | -1,694.260 | 0.887 | -0.150 | 3,504.600 | 26.632 |
| O15L | LEVEL_RECLAIM | 1 | 2020 | 447 | 441 | 38.322 | -2,191.360 | 0.665 | -0.446 | 2,471.180 | 12.194 |
| O15L | LEVEL_RECLAIM | 1 | 2021 | 435 | 428 | 38.084 | -1,564.380 | 0.722 | -0.467 | 1,801.860 | 11.089 |
| O15L | LEVEL_RECLAIM | 1 | 2022 | 483 | 480 | 42.292 | -604.800 | 0.925 | -0.309 | 1,744.680 | 16.182 |
| O15L | LEVEL_RECLAIM | 1 | 2023 | 433 | 431 | 42.459 | -915.260 | 0.823 | -0.383 | 1,022.420 | 10.825 |
| O15L | LEVEL_RECLAIM | 2 | 2020 | 447 | 441 | 26.984 | -2,013.860 | 0.748 | -0.405 | 2,204.280 | 12.194 |
| O15L | LEVEL_RECLAIM | 2 | 2021 | 435 | 428 | 31.542 | 861.120 | 1.137 | -0.288 | 692.960 | 11.089 |
| O15L | LEVEL_RECLAIM | 2 | 2022 | 483 | 480 | 29.583 | -1,384.300 | 0.873 | -0.278 | 3,043.680 | 16.182 |
| O15L | LEVEL_RECLAIM | 2 | 2023 | 433 | 431 | 28.306 | -1,868.760 | 0.736 | -0.387 | 1,914.800 | 10.825 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2020 | 462 | 460 | 49.348 | 162.900 | 1.016 | -0.081 | 1,437.260 | 22.987 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2021 | 372 | 369 | 48.780 | -481.740 | 0.946 | -0.085 | 1,755.600 | 24.132 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2022 | 404 | 403 | 49.380 | -1,562.380 | 0.906 | -0.054 | 3,711.400 | 39.763 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2023 | 398 | 395 | 47.595 | -2,229.700 | 0.795 | -0.103 | 2,560.840 | 25.085 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2020 | 462 | 460 | 33.043 | 43.400 | 1.003 | -0.098 | 2,631.160 | 22.987 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2021 | 372 | 369 | 34.959 | -219.240 | 0.981 | -0.052 | 2,233.660 | 24.132 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2022 | 404 | 403 | 32.506 | -3,358.880 | 0.847 | -0.110 | 7,742.360 | 39.763 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2023 | 398 | 395 | 35.190 | -520.200 | 0.960 | -0.027 | 2,100.480 | 25.085 |
| O5H | LEVEL_RECLAIM | 1 | 2020 | 462 | 460 | 36.522 | -1,610.100 | 0.701 | -0.551 | 1,631.300 | 9.700 |
| O5H | LEVEL_RECLAIM | 1 | 2021 | 372 | 369 | 38.211 | -772.740 | 0.822 | -0.468 | 877.880 | 10.538 |
| O5H | LEVEL_RECLAIM | 1 | 2022 | 404 | 403 | 46.898 | 4.620 | 1.001 | -0.230 | 998.340 | 17.247 |
| O5H | LEVEL_RECLAIM | 1 | 2023 | 398 | 395 | 40.759 | -1,258.700 | 0.751 | -0.439 | 1,315.100 | 11.037 |
| O5H | LEVEL_RECLAIM | 2 | 2020 | 462 | 460 | 24.783 | -2,396.600 | 0.663 | -0.540 | 2,587.860 | 9.700 |
| O5H | LEVEL_RECLAIM | 2 | 2021 | 372 | 369 | 27.371 | -938.240 | 0.836 | -0.421 | 1,202.560 | 10.538 |
| O5H | LEVEL_RECLAIM | 2 | 2022 | 404 | 403 | 31.514 | -962.880 | 0.901 | -0.234 | 2,502.060 | 17.247 |
| O5H | LEVEL_RECLAIM | 2 | 2023 | 398 | 395 | 29.620 | -2,073.700 | 0.694 | -0.374 | 2,248.220 | 11.037 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2020 | 519 | 512 | 48.047 | -3,044.520 | 0.803 | -0.092 | 4,234.080 | 27.905 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2021 | 501 | 494 | 43.927 | -4,518.240 | 0.720 | -0.169 | 4,954.560 | 28.231 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2022 | 510 | 508 | 49.803 | -2,068.180 | 0.906 | -0.032 | 3,053.340 | 42.374 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2023 | 480 | 479 | 54.280 | 1,210.160 | 1.099 | 0.034 | 1,654.460 | 27.468 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2020 | 519 | 512 | 33.008 | -4,020.520 | 0.796 | -0.100 | 4,906.200 | 27.905 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2021 | 501 | 494 | 29.960 | -4,330.740 | 0.783 | -0.167 | 5,345.000 | 28.231 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2022 | 510 | 508 | 35.433 | -752.180 | 0.973 | -0.006 | 3,317.020 | 42.374 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2023 | 480 | 479 | 30.689 | -2,921.840 | 0.834 | -0.160 | 5,775.420 | 27.468 |
| O5L | LEVEL_RECLAIM | 1 | 2020 | 519 | 512 | 38.477 | -1,538.520 | 0.782 | -0.464 | 2,116.460 | 12.271 |
| O5L | LEVEL_RECLAIM | 1 | 2021 | 501 | 494 | 38.462 | -3,004.240 | 0.608 | -0.451 | 3,004.240 | 12.260 |
| O5L | LEVEL_RECLAIM | 1 | 2022 | 510 | 508 | 41.732 | -1,080.680 | 0.878 | -0.327 | 2,185.280 | 16.497 |
| O5L | LEVEL_RECLAIM | 1 | 2023 | 480 | 479 | 46.764 | -30.340 | 0.994 | -0.291 | 1,095.040 | 10.911 |
| O5L | LEVEL_RECLAIM | 2 | 2020 | 519 | 512 | 27.734 | -986.020 | 0.888 | -0.407 | 1,837.380 | 12.271 |
| O5L | LEVEL_RECLAIM | 2 | 2021 | 501 | 494 | 28.947 | -2,400.240 | 0.737 | -0.356 | 2,720.660 | 12.260 |
| O5L | LEVEL_RECLAIM | 2 | 2022 | 510 | 508 | 29.921 | -284.180 | 0.975 | -0.275 | 2,155.280 | 16.497 |
| O5L | LEVEL_RECLAIM | 2 | 2023 | 480 | 479 | 32.777 | -761.340 | 0.897 | -0.258 | 1,396.820 | 10.911 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2020 | 266 | 262 | 47.328 | -983.520 | 0.855 | -0.104 | 2,157.140 | 25.009 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2021 | 233 | 233 | 48.927 | -1,074.680 | 0.795 | -0.089 | 1,189.380 | 20.464 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2022 | 176 | 174 | 51.149 | 357.460 | 1.055 | -0.022 | 1,808.560 | 39.264 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2023 | 211 | 209 | 53.110 | 415.860 | 1.085 | 0.025 | 473.140 | 25.401 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2020 | 266 | 262 | 30.916 | -1,977.520 | 0.778 | -0.157 | 2,296.660 | 25.009 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2021 | 233 | 233 | 33.906 | -383.680 | 0.941 | -0.065 | 1,300.440 | 20.464 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2022 | 176 | 174 | 33.908 | -94.540 | 0.989 | -0.050 | 2,651.980 | 39.264 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2023 | 211 | 209 | 36.842 | 25.860 | 1.004 | 0.041 | 915.920 | 25.401 |
| PDH | LEVEL_RECLAIM | 1 | 2020 | 266 | 262 | 36.260 | -975.520 | 0.706 | -0.504 | 1,216.480 | 10.659 |
| PDH | LEVEL_RECLAIM | 1 | 2021 | 233 | 233 | 37.768 | -1,008.680 | 0.628 | -0.499 | 1,168.180 | 9.337 |
| PDH | LEVEL_RECLAIM | 1 | 2022 | 176 | 174 | 39.080 | -270.540 | 0.906 | -0.396 | 939.980 | 15.680 |
| PDH | LEVEL_RECLAIM | 1 | 2023 | 211 | 209 | 44.498 | 204.360 | 1.090 | -0.336 | 471.020 | 11.519 |
| PDH | LEVEL_RECLAIM | 2 | 2020 | 266 | 262 | 24.809 | -885.520 | 0.785 | -0.505 | 1,375.240 | 10.659 |
| PDH | LEVEL_RECLAIM | 2 | 2021 | 233 | 233 | 27.039 | -810.680 | 0.756 | -0.452 | 1,021.120 | 9.337 |
| PDH | LEVEL_RECLAIM | 2 | 2022 | 176 | 174 | 25.862 | -1,022.540 | 0.750 | -0.424 | 1,394.480 | 15.680 |
| PDH | LEVEL_RECLAIM | 2 | 2023 | 211 | 209 | 29.187 | -678.140 | 0.804 | -0.353 | 1,099.820 | 11.519 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2020 | 196 | 194 | 44.330 | -2,088.240 | 0.709 | -0.151 | 2,497.220 | 32.780 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2021 | 217 | 214 | 50.935 | -896.440 | 0.866 | -0.036 | 1,656.560 | 30.473 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2022 | 307 | 305 | 47.869 | -1,722.800 | 0.865 | -0.083 | 2,484.340 | 40.342 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2023 | 197 | 195 | 51.795 | 325.300 | 1.063 | -0.025 | 697.500 | 28.294 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2020 | 196 | 194 | 29.897 | -2,589.740 | 0.705 | -0.206 | 3,529.620 | 32.780 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2021 | 217 | 214 | 37.850 | -924.440 | 0.888 | -0.002 | 2,280.520 | 30.473 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2022 | 307 | 305 | 36.393 | -171.800 | 0.989 | -0.009 | 3,025.340 | 40.342 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2023 | 197 | 195 | 37.436 | 56.800 | 1.008 | 0.002 | 1,469.040 | 28.294 |
| PDL | LEVEL_RECLAIM | 1 | 2020 | 196 | 194 | 33.505 | -2,380.740 | 0.401 | -0.554 | 2,389.280 | 13.997 |
| PDL | LEVEL_RECLAIM | 1 | 2021 | 217 | 214 | 48.131 | -10.940 | 0.996 | -0.263 | 495.680 | 12.482 |
| PDL | LEVEL_RECLAIM | 1 | 2022 | 307 | 305 | 39.672 | -1,074.300 | 0.788 | -0.402 | 1,129.620 | 14.681 |
| PDL | LEVEL_RECLAIM | 1 | 2023 | 197 | 195 | 47.692 | -123.200 | 0.946 | -0.257 | 548.900 | 11.562 |
| PDL | LEVEL_RECLAIM | 2 | 2020 | 196 | 194 | 24.742 | -2,140.240 | 0.524 | -0.482 | 2,183.220 | 13.997 |
| PDL | LEVEL_RECLAIM | 2 | 2021 | 217 | 214 | 34.579 | -450.440 | 0.878 | -0.210 | 816.680 | 12.482 |
| PDL | LEVEL_RECLAIM | 2 | 2022 | 307 | 305 | 29.508 | -630.800 | 0.900 | -0.315 | 1,371.500 | 14.681 |
| PDL | LEVEL_RECLAIM | 2 | 2023 | 197 | 195 | 34.872 | 223.800 | 1.078 | -0.200 | 628.420 | 11.562 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2020 | 280 | 276 | 47.464 | -409.960 | 0.934 | -0.103 | 1,277.840 | 22.432 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2021 | 312 | 307 | 50.814 | -747.720 | 0.895 | -0.058 | 1,317.820 | 23.007 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2022 | 260 | 257 | 56.809 | 2,260.780 | 1.265 | 0.096 | 1,019.000 | 37.990 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2023 | 310 | 307 | 52.117 | 390.780 | 1.054 | -0.014 | 722.880 | 25.371 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2020 | 280 | 276 | 31.159 | -316.460 | 0.961 | -0.129 | 1,764.900 | 22.432 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2021 | 312 | 307 | 34.853 | -1,422.720 | 0.846 | -0.089 | 1,879.280 | 23.007 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2022 | 260 | 257 | 36.187 | 1,777.780 | 1.146 | 0.012 | 2,629.900 | 37.990 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2023 | 310 | 307 | 32.899 | -1,952.220 | 0.814 | -0.096 | 2,154.920 | 25.371 |
| PMH | LEVEL_RECLAIM | 1 | 2020 | 280 | 276 | 35.145 | -1,212.460 | 0.639 | -0.537 | 1,315.780 | 9.810 |
| PMH | LEVEL_RECLAIM | 1 | 2021 | 312 | 307 | 39.414 | -926.220 | 0.743 | -0.471 | 1,017.360 | 10.100 |
| PMH | LEVEL_RECLAIM | 1 | 2022 | 260 | 257 | 43.580 | -205.220 | 0.954 | -0.313 | 843.640 | 16.982 |
| PMH | LEVEL_RECLAIM | 1 | 2023 | 310 | 307 | 42.020 | -421.220 | 0.885 | -0.413 | 520.740 | 11.275 |
| PMH | LEVEL_RECLAIM | 2 | 2020 | 280 | 276 | 22.826 | -2,037.460 | 0.536 | -0.552 | 2,087.660 | 9.810 |
| PMH | LEVEL_RECLAIM | 2 | 2021 | 312 | 307 | 24.756 | -1,221.220 | 0.744 | -0.520 | 1,351.280 | 10.100 |
| PMH | LEVEL_RECLAIM | 2 | 2022 | 260 | 257 | 32.685 | 398.280 | 1.069 | -0.210 | 1,683.240 | 16.982 |
| PMH | LEVEL_RECLAIM | 2 | 2023 | 310 | 307 | 28.339 | -1,232.720 | 0.760 | -0.413 | 1,266.800 | 11.275 |
| PML | BREAK_CANDLE_HIGH | 1 | 2020 | 297 | 293 | 49.147 | -1,283.780 | 0.858 | -0.067 | 1,613.100 | 29.836 |
| PML | BREAK_CANDLE_HIGH | 1 | 2021 | 368 | 366 | 47.814 | -1,507.360 | 0.863 | -0.093 | 2,405.480 | 28.193 |
| PML | BREAK_CANDLE_HIGH | 1 | 2022 | 452 | 444 | 50.225 | -1,382.240 | 0.927 | -0.023 | 2,140.800 | 42.564 |
| PML | BREAK_CANDLE_HIGH | 1 | 2023 | 368 | 367 | 48.501 | -2,053.320 | 0.810 | -0.079 | 2,871.980 | 27.047 |
| PML | BREAK_CANDLE_HIGH | 2 | 2020 | 297 | 293 | 35.495 | -217.780 | 0.980 | -0.033 | 1,878.800 | 29.836 |
| PML | BREAK_CANDLE_HIGH | 2 | 2021 | 368 | 366 | 31.967 | -2,433.860 | 0.830 | -0.121 | 3,470.540 | 28.193 |
| PML | BREAK_CANDLE_HIGH | 2 | 2022 | 452 | 444 | 36.937 | -287.740 | 0.988 | 0.023 | 2,882.960 | 42.564 |
| PML | BREAK_CANDLE_HIGH | 2 | 2023 | 368 | 367 | 32.698 | -1,976.820 | 0.851 | -0.116 | 4,190.360 | 27.047 |
| PML | LEVEL_RECLAIM | 1 | 2020 | 297 | 293 | 39.932 | -1,072.280 | 0.743 | -0.414 | 1,354.280 | 12.465 |
| PML | LEVEL_RECLAIM | 1 | 2021 | 368 | 366 | 41.530 | -554.860 | 0.877 | -0.412 | 902.540 | 11.492 |
| PML | LEVEL_RECLAIM | 1 | 2022 | 452 | 444 | 40.766 | -2,697.240 | 0.691 | -0.355 | 2,800.180 | 16.579 |
| PML | LEVEL_RECLAIM | 1 | 2023 | 368 | 367 | 43.597 | -667.820 | 0.846 | -0.348 | 1,114.200 | 10.872 |
| PML | LEVEL_RECLAIM | 2 | 2020 | 297 | 293 | 27.986 | -1,052.280 | 0.798 | -0.394 | 1,615.820 | 12.465 |
| PML | LEVEL_RECLAIM | 2 | 2021 | 368 | 366 | 31.148 | -224.860 | 0.962 | -0.315 | 1,084.700 | 11.492 |
| PML | LEVEL_RECLAIM | 2 | 2022 | 452 | 444 | 31.081 | -766.740 | 0.925 | -0.241 | 1,381.840 | 16.579 |
| PML | LEVEL_RECLAIM | 2 | 2023 | 368 | 367 | 31.608 | -403.320 | 0.928 | -0.296 | 1,424.320 | 10.872 |

## Actual costs and sensitivity

| level_type | stop | target_r | ticks | valid_trades | gross_usd | fees_usd | net_usd | pf | avg_net_r | break_even_fee_per_side |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | 0 | 1460 | 4,043.500 | 2,131.600 | 1,911.900 | 1.054 | -0.013 | 1.385 |
| O15H | BREAK_CANDLE_HIGH | 2 | 0 | 1460 | 5,680.000 | 2,131.600 | 3,548.400 | 1.075 | 0.005 | 1.945 |
| O15H | BREAK_CANDLE_HIGH | 1 | 1 | 1460 | 2,056.500 | 2,131.600 | -75.100 | 0.998 | -0.051 | 0.704 |
| O15H | BREAK_CANDLE_HIGH | 2 | 1 | 1460 | 3,847.000 | 2,131.600 | 1,715.400 | 1.036 | -0.023 | 1.317 |
| O15H | BREAK_CANDLE_HIGH | 1 | 2 | 1460 | 692.500 | 2,131.600 | -1,439.100 | 0.962 | -0.075 | 0.237 |
| O15H | BREAK_CANDLE_HIGH | 2 | 2 | 1460 | 2,087.000 | 2,131.600 | -44.600 | 0.999 | -0.056 | 0.715 |
| O15H | LEVEL_RECLAIM | 1 | 0 | 1460 | 126.000 | 2,131.600 | -2,005.600 | 0.883 | -0.368 | 0.043 |
| O15H | LEVEL_RECLAIM | 2 | 0 | 1460 | 183.500 | 2,131.600 | -1,948.100 | 0.913 | -0.291 | 0.063 |
| O15H | LEVEL_RECLAIM | 1 | 1 | 1460 | -871.000 | 2,131.600 | -3,002.600 | 0.833 | -0.404 | -0.298 |
| O15H | LEVEL_RECLAIM | 2 | 1 | 1460 | -1,003.500 | 2,131.600 | -3,135.100 | 0.867 | -0.338 | -0.344 |
| O15H | LEVEL_RECLAIM | 1 | 2 | 1460 | -2,473.000 | 2,131.600 | -4,604.600 | 0.761 | -0.453 | -0.847 |
| O15H | LEVEL_RECLAIM | 2 | 2 | 1460 | -2,198.000 | 2,131.600 | -4,329.600 | 0.825 | -0.382 | -0.753 |
| O15L | BREAK_CANDLE_HIGH | 1 | 0 | 1780 | -177.000 | 2,598.800 | -2,775.800 | 0.949 | -0.021 | -0.050 |
| O15L | BREAK_CANDLE_HIGH | 2 | 0 | 1780 | -3,319.000 | 2,598.800 | -5,917.800 | 0.916 | -0.057 | -0.932 |
| O15L | BREAK_CANDLE_HIGH | 1 | 1 | 1780 | -2,185.000 | 2,598.800 | -4,783.800 | 0.914 | -0.051 | -0.614 |
| O15L | BREAK_CANDLE_HIGH | 2 | 1 | 1780 | -4,931.500 | 2,598.800 | -7,530.300 | 0.895 | -0.080 | -1.385 |
| O15L | BREAK_CANDLE_HIGH | 1 | 2 | 1780 | -3,839.500 | 2,598.800 | -6,438.300 | 0.887 | -0.074 | -1.079 |
| O15L | BREAK_CANDLE_HIGH | 2 | 2 | 1780 | -7,182.000 | 2,598.800 | -9,780.800 | 0.867 | -0.104 | -2.017 |
| O15L | LEVEL_RECLAIM | 1 | 0 | 1780 | -1,331.000 | 2,598.800 | -3,929.800 | 0.838 | -0.363 | -0.374 |
| O15L | LEVEL_RECLAIM | 2 | 0 | 1780 | -93.000 | 2,598.800 | -2,691.800 | 0.912 | -0.289 | -0.026 |
| O15L | LEVEL_RECLAIM | 1 | 1 | 1780 | -2,677.000 | 2,598.800 | -5,275.800 | 0.792 | -0.399 | -0.752 |
| O15L | LEVEL_RECLAIM | 2 | 1 | 1780 | -1,807.000 | 2,598.800 | -4,405.800 | 0.863 | -0.338 | -0.508 |
| O15L | LEVEL_RECLAIM | 1 | 2 | 1780 | -4,264.000 | 2,598.800 | -6,862.800 | 0.744 | -0.437 | -1.198 |
| O15L | LEVEL_RECLAIM | 2 | 2 | 1780 | -3,887.500 | 2,598.800 | -6,486.300 | 0.809 | -0.392 | -1.092 |
| O5H | BREAK_CANDLE_HIGH | 1 | 0 | 1627 | -244.500 | 2,375.420 | -2,619.920 | 0.943 | -0.052 | -0.075 |
| O5H | BREAK_CANDLE_HIGH | 2 | 0 | 1627 | -80.000 | 2,375.420 | -2,455.420 | 0.959 | -0.051 | -0.025 |
| O5H | BREAK_CANDLE_HIGH | 1 | 1 | 1627 | -1,735.500 | 2,375.420 | -4,110.920 | 0.912 | -0.080 | -0.533 |
| O5H | BREAK_CANDLE_HIGH | 2 | 1 | 1627 | -1,679.500 | 2,375.420 | -4,054.920 | 0.933 | -0.073 | -0.516 |
| O5H | BREAK_CANDLE_HIGH | 1 | 2 | 1627 | -3,482.500 | 2,375.420 | -5,857.920 | 0.878 | -0.109 | -1.070 |
| O5H | BREAK_CANDLE_HIGH | 2 | 2 | 1627 | -3,230.000 | 2,375.420 | -5,605.420 | 0.909 | -0.099 | -0.993 |
| O5H | LEVEL_RECLAIM | 1 | 0 | 1627 | -56.500 | 2,375.420 | -2,431.920 | 0.882 | -0.386 | -0.017 |
| O5H | LEVEL_RECLAIM | 2 | 0 | 1627 | -2,679.500 | 2,375.420 | -5,054.920 | 0.820 | -0.353 | -0.823 |
| O5H | LEVEL_RECLAIM | 1 | 1 | 1627 | -1,261.500 | 2,375.420 | -3,636.920 | 0.833 | -0.426 | -0.388 |
| O5H | LEVEL_RECLAIM | 2 | 1 | 1627 | -3,996.000 | 2,375.420 | -6,371.420 | 0.783 | -0.397 | -1.228 |
| O5H | LEVEL_RECLAIM | 1 | 2 | 1627 | -2,642.500 | 2,375.420 | -5,017.920 | 0.781 | -0.462 | -0.812 |
| O5H | LEVEL_RECLAIM | 2 | 2 | 1627 | -5,248.000 | 2,375.420 | -7,623.420 | 0.752 | -0.434 | -1.613 |
| O5L | BREAK_CANDLE_HIGH | 1 | 0 | 1993 | -3,790.000 | 2,909.780 | -6,699.780 | 0.896 | -0.045 | -0.951 |
| O5L | BREAK_CANDLE_HIGH | 2 | 0 | 1993 | -7,074.000 | 2,909.780 | -9,983.780 | 0.880 | -0.079 | -1.775 |
| O5L | BREAK_CANDLE_HIGH | 1 | 1 | 1993 | -5,511.000 | 2,909.780 | -8,420.780 | 0.872 | -0.066 | -1.383 |
| O5L | BREAK_CANDLE_HIGH | 2 | 1 | 1993 | -9,115.500 | 2,909.780 | -12,025.280 | 0.859 | -0.107 | -2.287 |
| O5L | BREAK_CANDLE_HIGH | 1 | 2 | 1993 | -7,909.000 | 2,909.780 | -10,818.780 | 0.840 | -0.094 | -1.984 |
| O5L | BREAK_CANDLE_HIGH | 2 | 2 | 1993 | -11,580.000 | 2,909.780 | -14,489.780 | 0.833 | -0.129 | -2.905 |
| O5L | LEVEL_RECLAIM | 1 | 0 | 1993 | -1,132.000 | 2,909.780 | -4,041.780 | 0.853 | -0.348 | -0.284 |
| O5L | LEVEL_RECLAIM | 2 | 0 | 1993 | 330.500 | 2,909.780 | -2,579.280 | 0.926 | -0.283 | 0.083 |
| O5L | LEVEL_RECLAIM | 1 | 1 | 1993 | -2,744.000 | 2,909.780 | -5,653.780 | 0.804 | -0.384 | -0.688 |
| O5L | LEVEL_RECLAIM | 2 | 1 | 1993 | -1,522.000 | 2,909.780 | -4,431.780 | 0.879 | -0.325 | -0.382 |
| O5L | LEVEL_RECLAIM | 1 | 2 | 1993 | -4,437.000 | 2,909.780 | -7,346.780 | 0.758 | -0.421 | -1.113 |
| O5L | LEVEL_RECLAIM | 2 | 2 | 1993 | -4,349.500 | 2,909.780 | -7,259.280 | 0.812 | -0.380 | -1.091 |
| PDH | BREAK_CANDLE_HIGH | 1 | 0 | 878 | 634.000 | 1,281.880 | -647.880 | 0.972 | -0.031 | 0.361 |
| PDH | BREAK_CANDLE_HIGH | 2 | 0 | 878 | -223.500 | 1,281.880 | -1,505.380 | 0.950 | -0.031 | -0.127 |
| PDH | BREAK_CANDLE_HIGH | 1 | 1 | 878 | -3.000 | 1,281.880 | -1,284.880 | 0.945 | -0.053 | -0.002 |
| PDH | BREAK_CANDLE_HIGH | 2 | 1 | 878 | -1,148.000 | 1,281.880 | -2,429.880 | 0.922 | -0.064 | -0.654 |
| PDH | BREAK_CANDLE_HIGH | 1 | 2 | 878 | -921.000 | 1,281.880 | -2,202.880 | 0.909 | -0.085 | -0.524 |
| PDH | BREAK_CANDLE_HIGH | 2 | 2 | 878 | -2,152.000 | 1,281.880 | -3,433.880 | 0.892 | -0.089 | -1.226 |
| PDH | LEVEL_RECLAIM | 1 | 0 | 878 | 96.500 | 1,281.880 | -1,185.380 | 0.887 | -0.390 | 0.055 |
| PDH | LEVEL_RECLAIM | 2 | 0 | 878 | -886.000 | 1,281.880 | -2,167.880 | 0.846 | -0.375 | -0.505 |
| PDH | LEVEL_RECLAIM | 1 | 1 | 878 | -768.500 | 1,281.880 | -2,050.380 | 0.817 | -0.441 | -0.438 |
| PDH | LEVEL_RECLAIM | 2 | 1 | 878 | -2,115.000 | 1,281.880 | -3,396.880 | 0.773 | -0.439 | -1.204 |
| PDH | LEVEL_RECLAIM | 1 | 2 | 878 | -1,651.500 | 1,281.880 | -2,933.380 | 0.754 | -0.482 | -0.940 |
| PDH | LEVEL_RECLAIM | 2 | 2 | 878 | -2,877.500 | 1,281.880 | -4,159.380 | 0.736 | -0.487 | -1.639 |
| PDL | BREAK_CANDLE_HIGH | 1 | 0 | 908 | -2,243.000 | 1,325.680 | -3,568.680 | 0.885 | -0.058 | -1.235 |
| PDL | BREAK_CANDLE_HIGH | 2 | 0 | 908 | -903.500 | 1,325.680 | -2,229.180 | 0.942 | -0.025 | -0.498 |
| PDL | BREAK_CANDLE_HIGH | 1 | 1 | 908 | -3,056.500 | 1,325.680 | -4,382.180 | 0.862 | -0.074 | -1.683 |
| PDL | BREAK_CANDLE_HIGH | 2 | 1 | 908 | -2,303.500 | 1,325.680 | -3,629.180 | 0.908 | -0.047 | -1.268 |
| PDL | BREAK_CANDLE_HIGH | 1 | 2 | 908 | -3,827.500 | 1,325.680 | -5,153.180 | 0.841 | -0.089 | -2.108 |
| PDL | BREAK_CANDLE_HIGH | 2 | 2 | 908 | -3,203.000 | 1,325.680 | -4,528.680 | 0.887 | -0.075 | -1.764 |
| PDL | LEVEL_RECLAIM | 1 | 0 | 908 | -1,431.500 | 1,325.680 | -2,757.180 | 0.792 | -0.330 | -0.788 |
| PDL | LEVEL_RECLAIM | 2 | 0 | 908 | -1,076.000 | 1,325.680 | -2,401.680 | 0.856 | -0.271 | -0.593 |
| PDL | LEVEL_RECLAIM | 1 | 1 | 908 | -2,263.500 | 1,325.680 | -3,589.180 | 0.743 | -0.371 | -1.246 |
| PDL | LEVEL_RECLAIM | 2 | 1 | 908 | -1,672.000 | 1,325.680 | -2,997.680 | 0.828 | -0.301 | -0.921 |
| PDL | LEVEL_RECLAIM | 1 | 2 | 908 | -3,159.500 | 1,325.680 | -4,485.180 | 0.694 | -0.413 | -1.740 |
| PDL | LEVEL_RECLAIM | 2 | 2 | 908 | -2,373.000 | 1,325.680 | -3,698.680 | 0.796 | -0.337 | -1.307 |
| PMH | BREAK_CANDLE_HIGH | 1 | 0 | 1147 | 4,051.500 | 1,674.620 | 2,376.880 | 1.084 | 0.002 | 1.766 |
| PMH | BREAK_CANDLE_HIGH | 2 | 0 | 1147 | 563.500 | 1,674.620 | -1,111.120 | 0.972 | -0.058 | 0.246 |
| PMH | BREAK_CANDLE_HIGH | 1 | 1 | 1147 | 3,168.500 | 1,674.620 | 1,493.880 | 1.051 | -0.022 | 1.381 |
| PMH | BREAK_CANDLE_HIGH | 2 | 1 | 1147 | -239.000 | 1,674.620 | -1,913.620 | 0.952 | -0.078 | -0.104 |
| PMH | BREAK_CANDLE_HIGH | 1 | 2 | 1147 | 2,344.500 | 1,674.620 | 669.880 | 1.022 | -0.044 | 1.022 |
| PMH | BREAK_CANDLE_HIGH | 2 | 2 | 1147 | -976.500 | 1,674.620 | -2,651.120 | 0.935 | -0.097 | -0.426 |
| PMH | LEVEL_RECLAIM | 1 | 0 | 1147 | 36.500 | 1,674.620 | -1,638.120 | 0.885 | -0.392 | 0.016 |
| PMH | LEVEL_RECLAIM | 2 | 0 | 1147 | -1,316.500 | 1,674.620 | -2,991.120 | 0.843 | -0.382 | -0.574 |
| PMH | LEVEL_RECLAIM | 1 | 1 | 1147 | -1,090.500 | 1,674.620 | -2,765.120 | 0.817 | -0.436 | -0.475 |
| PMH | LEVEL_RECLAIM | 2 | 1 | 1147 | -2,418.500 | 1,674.620 | -4,093.120 | 0.796 | -0.429 | -1.054 |
| PMH | LEVEL_RECLAIM | 1 | 2 | 1147 | -2,167.500 | 1,674.620 | -3,842.120 | 0.760 | -0.480 | -0.945 |
| PMH | LEVEL_RECLAIM | 2 | 2 | 1147 | -3,450.000 | 1,674.620 | -5,124.620 | 0.757 | -0.478 | -1.504 |
| PML | BREAK_CANDLE_HIGH | 1 | 0 | 1470 | -2,610.500 | 2,146.200 | -4,756.700 | 0.902 | -0.037 | -0.888 |
| PML | BREAK_CANDLE_HIGH | 2 | 0 | 1470 | -399.000 | 2,146.200 | -2,545.200 | 0.958 | -0.027 | -0.136 |
| PML | BREAK_CANDLE_HIGH | 1 | 1 | 1470 | -4,080.500 | 2,146.200 | -6,226.700 | 0.875 | -0.063 | -1.388 |
| PML | BREAK_CANDLE_HIGH | 2 | 1 | 1470 | -2,770.000 | 2,146.200 | -4,916.200 | 0.921 | -0.059 | -0.942 |
| PML | BREAK_CANDLE_HIGH | 1 | 2 | 1470 | -5,863.500 | 2,146.200 | -8,009.700 | 0.843 | -0.088 | -1.994 |
| PML | BREAK_CANDLE_HIGH | 2 | 2 | 1470 | -4,245.500 | 2,146.200 | -6,391.700 | 0.900 | -0.079 | -1.444 |
| PML | LEVEL_RECLAIM | 1 | 0 | 1470 | -1,598.000 | 2,146.200 | -3,744.200 | 0.819 | -0.341 | -0.544 |
| PML | LEVEL_RECLAIM | 2 | 0 | 1470 | 911.000 | 2,146.200 | -1,235.200 | 0.952 | -0.254 | 0.310 |
| PML | LEVEL_RECLAIM | 1 | 1 | 1470 | -2,846.000 | 2,146.200 | -4,992.200 | 0.770 | -0.379 | -0.968 |
| PML | LEVEL_RECLAIM | 2 | 1 | 1470 | -301.000 | 2,146.200 | -2,447.200 | 0.909 | -0.304 | -0.102 |
| PML | LEVEL_RECLAIM | 1 | 2 | 1470 | -4,103.000 | 2,146.200 | -6,249.200 | 0.726 | -0.415 | -1.396 |
| PML | LEVEL_RECLAIM | 2 | 2 | 1470 | -1,505.000 | 2,146.200 | -3,651.200 | 0.870 | -0.345 | -0.512 |

Entry slippage changes executed entry, original risk and the target mechanically. Exit slippage is adverse even on targets, matching the existing executor. Costs therefore are not simply a constant subtraction between slippage scenarios. Break-even fee per side is gross diagnostic P&L divided by twice completed diagnostics, and may be negative.

## Concentration and interpretation

| level_type | stop | target_r | net_usd | avg_net_r | positive_years | net_2022 | share_2022_of_net_pct | risk_points_max | risk_points_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | BREAK_CANDLE_HIGH | 1 | -75.100 | -0.051 | 1 | -233.720 | — | 277.250 | 20.500 |
| O15H | BREAK_CANDLE_HIGH | 2 | 1,715.400 | -0.023 | 2 | -159.720 | -9.311 | 277.250 | 20.500 |
| O15H | LEVEL_RECLAIM | 1 | -3,002.600 | -0.404 | 0 | -950.220 | — | 186.500 | 7.250 |
| O15H | LEVEL_RECLAIM | 2 | -3,135.100 | -0.338 | 0 | -1,457.220 | — | 186.500 | 7.250 |
| O15L | BREAK_CANDLE_HIGH | 1 | -4,783.800 | -0.051 | 1 | -2,880.800 | — | 277.250 | 25.500 |
| O15L | BREAK_CANDLE_HIGH | 2 | -7,530.300 | -0.080 | 0 | -2,415.800 | — | 277.250 | 25.500 |
| O15L | LEVEL_RECLAIM | 1 | -5,275.800 | -0.399 | 0 | -604.800 | — | 147.750 | 8.750 |
| O15L | LEVEL_RECLAIM | 2 | -4,405.800 | -0.338 | 1 | -1,384.300 | — | 147.750 | 8.750 |
| O5H | BREAK_CANDLE_HIGH | 1 | -4,110.920 | -0.080 | 1 | -1,562.380 | — | 277.250 | 22.250 |
| O5H | BREAK_CANDLE_HIGH | 2 | -4,054.920 | -0.073 | 1 | -3,358.880 | — | 277.250 | 22.250 |
| O5H | LEVEL_RECLAIM | 1 | -3,636.920 | -0.426 | 1 | 4.620 | — | 186.500 | 8.000 |
| O5H | LEVEL_RECLAIM | 2 | -6,371.420 | -0.397 | 0 | -962.880 | — | 186.500 | 8.000 |
| O5L | BREAK_CANDLE_HIGH | 1 | -8,420.780 | -0.066 | 1 | -2,068.180 | — | 277.250 | 26.250 |
| O5L | BREAK_CANDLE_HIGH | 2 | -12,025.280 | -0.107 | 0 | -752.180 | — | 277.250 | 26.250 |
| O5L | LEVEL_RECLAIM | 1 | -5,653.780 | -0.384 | 0 | -1,080.680 | — | 149.750 | 9.000 |
| O5L | LEVEL_RECLAIM | 2 | -4,431.780 | -0.325 | 0 | -284.180 | — | 149.750 | 9.000 |
| PDH | BREAK_CANDLE_HIGH | 1 | -1,284.880 | -0.053 | 2 | 357.460 | — | 277.250 | 21.375 |
| PDH | BREAK_CANDLE_HIGH | 2 | -2,429.880 | -0.064 | 1 | -94.540 | — | 277.250 | 21.375 |
| PDH | LEVEL_RECLAIM | 1 | -2,050.380 | -0.441 | 1 | -270.540 | — | 232.500 | 7.500 |
| PDH | LEVEL_RECLAIM | 2 | -3,396.880 | -0.439 | 0 | -1,022.540 | — | 232.500 | 7.500 |
| PDL | BREAK_CANDLE_HIGH | 1 | -4,382.180 | -0.074 | 1 | -1,722.800 | — | 277.250 | 29.125 |
| PDL | BREAK_CANDLE_HIGH | 2 | -3,629.180 | -0.047 | 1 | -171.800 | — | 277.250 | 29.125 |
| PDL | LEVEL_RECLAIM | 1 | -3,589.180 | -0.371 | 0 | -1,074.300 | — | 182.500 | 9.000 |
| PDL | LEVEL_RECLAIM | 2 | -2,997.680 | -0.301 | 1 | -630.800 | — | 182.500 | 9.000 |
| PMH | BREAK_CANDLE_HIGH | 1 | 1,493.880 | -0.022 | 2 | 2,260.780 | 151.336 | 277.250 | 21.250 |
| PMH | BREAK_CANDLE_HIGH | 2 | -1,913.620 | -0.078 | 1 | 1,777.780 | — | 277.250 | 21.250 |
| PMH | LEVEL_RECLAIM | 1 | -2,765.120 | -0.436 | 0 | -205.220 | — | 198.750 | 7.750 |
| PMH | LEVEL_RECLAIM | 2 | -4,093.120 | -0.429 | 1 | 398.280 | — | 198.750 | 7.750 |
| PML | BREAK_CANDLE_HIGH | 1 | -6,226.700 | -0.063 | 0 | -1,382.240 | — | 277.250 | 27.500 |
| PML | BREAK_CANDLE_HIGH | 2 | -4,916.200 | -0.059 | 0 | -287.740 | — | 277.250 | 27.500 |
| PML | LEVEL_RECLAIM | 1 | -4,992.200 | -0.379 | 0 | -2,697.240 | — | 118.500 | 9.125 |
| PML | LEVEL_RECLAIM | 2 | -2,447.200 | -0.304 | 0 | -766.740 | — | 118.500 | 9.125 |

A positive dollar result with negative average R may reflect large-risk observations rather than consistent opportunity. Shares above 100% mean other years offset the profitable year; a missing share means aggregate net was not positive. The top-five-risk observations and their signed contributions are retained in largest_risk_diagnostics.csv without exclusions.

The previous favorable-50-point associations do not automatically imply a useful risk path. This audit does not select a best level, stop or target by in-sample profit. Review yearly consistency, stop logic, adverse paths and fee sensitivity before deciding whether to freeze one controlled strategy. Validation and OOS remain unqueried.

## Reproducibility and complete exports

frozen protocol.json; exact_raw_events.csv; source_reconciliation.csv; all_event_paths.csv; all_target_executions.csv; population_and_quality.csv; stop_path_comparison.csv; fixed_target_diagnostics.csv; yearly_stability.csv; fee_slippage_sensitivity.csv; descriptive_context.csv; largest_risk_diagnostics.csv; ambiguity_audit.csv; recommendation.json; execution_verification.json. All observations are retained locally. The bundle includes aggregate reports and an index linking full raw artifacts by hash; no sampling is used.

The report’s standalone viewer is available from the Lab Research page. Production strategies, stored runs, source studies and market-data files are unchanged.

## Review conclusion and delivery verification

The raw break-close setup does not support advancement under these tested rules: all 32 primary level/stop/target combinations have negative average net R after actual fees and one adverse tick each side. Thirty of 32 also lose net dollars. The two positive-dollar cases, PMH / break-candle-high / 1R and O15H / break-candle-high / 2R, have negative average net R and only two profitable years each. These are not strong candidates merely because aggregate dollars are positive.

PMH's positive case is carried by 2022 ($2,260.78 versus total $1,493.88); O15H's is carried by 2020 ($2,092.56 versus total $1,715.40). The top five largest-risk diagnostics contribute only $45.20 and $167.20 respectively, so the disagreement between dollar P&L and average R should not be simplistically attributed only to those five observations. Different risk weighting and uneven yearly performance matter.

With actual fees and zero slippage, only two cases have positive average net R; with one or two ticks, none do. No best level, stop or target is chosen. Any future confirmation-entry audit must be separately frozen; no rescue filters were added here.

Verification:

- 102 backend/research tests, 31 frontend tests and 2 browser smoke workflows passed; production build passed (existing large bundle warning remains).
- All 18 deterministic research artifacts reproduced byte-for-byte; the ZIP independently reproduced exactly. Full repeat: 157.658 seconds.
- Every one of 135,156 completed native diagnostic fills matched the independent simulation. P&L, fees, R, target price, unique scenario identity and post-confirmation exits were additionally reconciled from the entire exported log.
- Raw 11,364 signals include 101 confirmed at session close; these have no post-entry minute and are preserved as unexecutable signals. All other 11,263 signals completed both target simulations under both stops and all three costs.
- Ten raw events lack ATR but remain executable for structural risk/targets. Two distinct events encounter a later data gap in a stop-only path; all tested target trades exit before that gap. No minute is invented or skipped to claim a fill.
- Local aggregate bundle: 376,968 bytes; all indexed artifacts: 181,250,055 bytes, including full unsampled paths and fills.
- Read-only Lab report filters, year tables and CSV/JSON/ZIP exports passed. Original eight-level report remains accessible.
- Saved run/study/version/reveal metadata, source data and original studies remain unchanged. Validation/OOS outcomes were not queried. No production execution changes, strategy optimization or paid downloads.
