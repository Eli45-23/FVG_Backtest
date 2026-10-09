# Eight-level reaction and entry-timing research — Development v1

**DEVELOPMENT_RESEARCH_NOT_VALIDATED.** Fixed daily PDH/PDL, midnight PMH/PML, opening 5m and opening 15m highs/lows. Four reaction families, ten predefined entry definitions. All detection uses confirmed five-minute candles; all forward measurement uses subsequent one-minute data.

## Executive findings

The complete study contains 88,911 entry observations, not independent trades, across all eight level types. 29 of 160 registered 30-minute / favorable-50-point comparisons have a positive date-clustered difference with global BH q ≤ 0.05. These overlap heavily: they are not 29 independent edges, and no trade profit or optimal take-profit is established.

The corrected results are concentrated in downward break entries: immediate break at all eight levels, first full candle at six, next close hold at six, and next full hold at six. Two upward rejection-close comparisons and one upward retest-close comparison also pass. None of the failed-break entry comparisons clears the registered correction. Failure to clear correction is not proof that a reaction never works.

These are direction-specific crossings. For example, a DOWN break of PDH means price crosses PDH from above and closes below; it is not an upward breakout above PDH. “Direct” describes what was known at entry; later retests are retained, not removed with hindsight.

There is no defensible universal best entry or take-profit from this study. Confirmation reduces opportunities and can miss moves; shared-root comparisons are selected subsets. A level reaction can have an elevated favorable-hit rate while suffering large adverse movement. Stops, costs and position ownership require a separate frozen execution-feasibility test.

## Population and source coverage

| level_type | entry_observations | maximum_entry_dates | available_dates |
| --- | --- | --- | --- |
| PDH | 7256 | 399 | 1001 |
| PDL | 6602 | 352 | 1001 |
| PMH | 10569 | 615 | 990 |
| PML | 10254 | 562 | 990 |
| O5H | 14615 | 794 | 1004 |
| O5L | 14079 | 751 | 1004 |
| O15H | 13275 | 725 | 1003 |
| O15L | 12261 | 672 | 1003 |

There are 1,006 XNYS Development dates. Available-date counts reflect complete source coverage; they are not tuned exclusions. All source event identities are preserved. The six old populations are reused, while O15 events are newly generated with the same causal event/sequence mechanics. No existing immutable study is overwritten.

| level | source_events | study_id | reused_exactly |
| --- | --- | --- | --- |
| PDH | 11573 | 5cb7fab0d4e7414792a3fbe59ded4999 | True |
| PDL | 10465 | 5cb7fab0d4e7414792a3fbe59ded4999 | True |
| PMH | 16828 | 78c96aa0e91147ba9913e365f33ed2f9 | True |
| PML | 16361 | 78c96aa0e91147ba9913e365f33ed2f9 | True |
| O5H | 23457 | 5cb7fab0d4e7414792a3fbe59ded4999 | True |
| O5L | 22485 | 5cb7fab0d4e7414792a3fbe59ded4999 | True |
| O15H | 21137 | EIGHT_LEVEL_REACTION_ENTRY_V1 | False |
| O15L | 19353 | EIGHT_LEVEL_REACTION_ENTRY_V1 | False |

## What each entry means

- BREAK_CLOSE: immediate confirmed close across the level, including later failures.
- BREAK_FIRST_FULL: first entire candle beyond the level before a subsequent retouch; possibly the break candle itself.
- BREAK_NEXT_CLOSE_HOLD / BREAK_NEXT_FULL_HOLD: adjacent next candle closes beyond / remains entirely beyond.
- RETEST_CLOSE_HOLD: later distinct retest episode closes on the breakout side.
- RETEST_RANGE_ESCAPE: confirmed close beyond the accumulated retest-contact range, without an invented large-body filter.
- REJECTION_CLOSE / REJECTION_CONFIRMATION: frozen rejection close / adjacent close beyond its directional extreme.
- FAILED_BREAK_CLOSE / FAILED_BREAK_CONFIRMATION: adjacent return across the broken level / next close beyond the failure candle extreme, measured opposite the original break.

## Primary evidence: immediate downward breaks

Probabilities and intervals below are percentage points on an equal-NY-date basis. Raw event-weighted hit counts/rates remain in the outcome tables and viewer. These should not be interchanged.

| level_type | events | matched_dates | event_probability | baseline_probability | effect | ci_low | ci_high | bh_q | positive_years |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PDH | 886 | 349 | 26.677 | 19.804 | 6.873 | 3.359 | 10.328 | 0.005 | 4 |
| PDL | 917 | 338 | 32.466 | 25.313 | 7.153 | 3.072 | 11.365 | 0.008 | 4 |
| PMH | 1162 | 459 | 28.071 | 20.967 | 7.105 | 3.787 | 10.325 | 0.005 | 4 |
| PML | 1485 | 551 | 31.418 | 25.329 | 6.089 | 3.214 | 9.170 | 0.005 | 4 |
| O5H | 1636 | 617 | 29.659 | 22.373 | 7.286 | 4.571 | 10.064 | 0.005 | 4 |
| O5L | 2010 | 743 | 33.232 | 26.393 | 6.839 | 4.212 | 9.439 | 0.005 | 4 |
| O15H | 1470 | 558 | 27.143 | 20.326 | 6.817 | 3.984 | 9.769 | 0.005 | 4 |
| O15L | 1798 | 660 | 30.095 | 24.765 | 5.330 | 2.364 | 8.312 | 0.012 | 4 |

## Other corrected associations

| level_type | entry_kind | direction | events | matched_dates | event_probability | baseline_probability | effect | ci_low | ci_high | bh_q | positive_years |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PDL | REJECTION_CLOSE | UP | 416 | 221 | 28.499 | 22.268 | 6.231 | 1.640 | 11.066 | 0.036 | 4 |
| PML | RETEST_CLOSE_HOLD | UP | 353 | 204 | 23.820 | 16.381 | 7.439 | 2.327 | 12.490 | 0.036 | 4 |
| PML | REJECTION_CLOSE | UP | 719 | 399 | 26.318 | 21.554 | 4.765 | 1.325 | 8.421 | 0.036 | 4 |

## Each level: all primary entry comparisons

### PDH

| entry_kind | direction | events | matched_dates | event_probability | baseline_probability | effect | bh_q | positive_years | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BREAK_CLOSE | UP | 986 | 389 | 21.889 | 17.622 | 4.267 | 0.067 | 4 | 27.797 | 28.712 |
| BREAK_CLOSE | DOWN | 886 | 349 | 26.677 | 19.804 | 6.873 | 0.005 | 4 | 33.209 | 29.049 |
| BREAK_FIRST_FULL | UP | 417 | 282 | 17.908 | 16.977 | 0.931 | 0.869 | 2 | 27.886 | 27.506 |
| BREAK_FIRST_FULL | DOWN | 366 | 239 | 27.894 | 20.154 | 7.740 | 0.022 | 4 | 35.507 | 30.569 |
| BREAK_NEXT_CLOSE_HOLD | UP | 705 | 364 | 20.160 | 17.446 | 2.714 | 0.351 | 2 | 27.118 | 27.445 |
| BREAK_NEXT_CLOSE_HOLD | DOWN | 629 | 320 | 27.495 | 19.974 | 7.521 | 0.005 | 4 | 33.558 | 29.125 |
| BREAK_NEXT_FULL_HOLD | UP | 417 | 282 | 17.908 | 16.977 | 0.931 | 0.869 | 2 | 27.886 | 27.506 |
| BREAK_NEXT_FULL_HOLD | DOWN | 366 | 239 | 27.894 | 20.154 | 7.740 | 0.022 | 4 | 35.523 | 30.572 |
| RETEST_CLOSE_HOLD | UP | 300 | 187 | 12.656 | 12.460 | 0.196 | 0.982 | 2 | 26.418 | 31.375 |
| RETEST_CLOSE_HOLD | DOWN | 241 | 147 | 16.916 | 16.702 | 0.214 | 0.982 | 2 | 27.514 | 25.175 |
| RETEST_RANGE_ESCAPE | UP | 138 | 101 | 10.396 | 11.387 | -0.991 | 0.902 | 2 | 22.030 | 26.994 |
| RETEST_RANGE_ESCAPE | DOWN | 88 | 60 | 18.333 | 15.203 | 3.130 | 0.809 | 4 | 29.911 | 23.541 |
| REJECTION_CLOSE | UP | 412 | 244 | 17.008 | 16.138 | 0.870 | 0.872 | 3 | 29.626 | 34.005 |
| REJECTION_CLOSE | DOWN | 437 | 255 | 21.418 | 20.918 | 0.500 | 0.939 | 2 | 30.901 | 30.654 |
| REJECTION_CONFIRMATION | UP | 98 | 82 | 15.244 | 17.196 | -1.952 | 0.846 | 1 | 29.306 | 37.694 |
| REJECTION_CONFIRMATION | DOWN | 104 | 87 | 27.011 | 22.043 | 4.969 | 0.533 | 3 | 38.590 | 26.392 |
| FAILED_BREAK_CLOSE | UP | 240 | 150 | 15.111 | 15.021 | 0.090 | 0.982 | 2 | 27.509 | 29.268 |
| FAILED_BREAK_CLOSE | DOWN | 258 | 153 | 20.806 | 18.097 | 2.709 | 0.664 | 3 | 31.854 | 26.900 |
| FAILED_BREAK_CONFIRMATION | UP | 89 | 72 | 12.500 | 15.075 | -2.575 | 0.750 | 2 | 26.210 | 26.631 |
| FAILED_BREAK_CONFIRMATION | DOWN | 79 | 67 | 25.373 | 20.641 | 4.732 | 0.670 | 2 | 33.507 | 31.700 |

### PDL

| entry_kind | direction | events | matched_dates | event_probability | baseline_probability | effect | bh_q | positive_years | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BREAK_CLOSE | UP | 823 | 310 | 26.763 | 24.430 | 2.333 | 0.533 | 2 | 35.502 | 36.165 |
| BREAK_CLOSE | DOWN | 917 | 338 | 32.466 | 25.313 | 7.153 | 0.008 | 4 | 36.929 | 37.638 |
| BREAK_FIRST_FULL | UP | 351 | 216 | 25.502 | 23.584 | 1.918 | 0.747 | 1 | 36.561 | 34.277 |
| BREAK_FIRST_FULL | DOWN | 391 | 236 | 29.626 | 24.669 | 4.957 | 0.225 | 3 | 37.233 | 36.171 |
| BREAK_NEXT_CLOSE_HOLD | UP | 574 | 273 | 23.077 | 23.546 | -0.469 | 0.939 | 1 | 34.592 | 34.720 |
| BREAK_NEXT_CLOSE_HOLD | DOWN | 648 | 311 | 30.552 | 25.049 | 5.503 | 0.067 | 4 | 35.954 | 37.967 |
| BREAK_NEXT_FULL_HOLD | UP | 351 | 216 | 25.502 | 23.584 | 1.918 | 0.747 | 1 | 36.561 | 34.277 |
| BREAK_NEXT_FULL_HOLD | DOWN | 391 | 236 | 29.626 | 24.669 | 4.957 | 0.225 | 3 | 37.233 | 36.171 |
| RETEST_CLOSE_HOLD | UP | 235 | 138 | 23.792 | 19.821 | 3.972 | 0.425 | 3 | 32.839 | 33.472 |
| RETEST_CLOSE_HOLD | DOWN | 230 | 137 | 24.818 | 22.683 | 2.134 | 0.811 | 2 | 36.347 | 36.006 |
| RETEST_RANGE_ESCAPE | UP | 75 | 62 | 14.247 | 19.849 | -5.602 | 0.361 | 0 | 27.184 | 34.385 |
| RETEST_RANGE_ESCAPE | DOWN | 94 | 72 | 26.389 | 20.874 | 5.515 | 0.533 | 2 | 35.394 | 31.980 |
| REJECTION_CLOSE | UP | 416 | 221 | 28.499 | 22.268 | 6.231 | 0.036 | 4 | 35.474 | 37.362 |
| REJECTION_CLOSE | DOWN | 289 | 166 | 29.501 | 25.923 | 3.578 | 0.550 | 2 | 39.850 | 39.540 |
| REJECTION_CONFIRMATION | UP | 78 | 63 | 22.222 | 25.100 | -2.878 | 0.822 | 1 | 31.046 | 44.671 |
| REJECTION_CONFIRMATION | DOWN | 83 | 65 | 32.308 | 23.276 | 9.031 | 0.257 | 3 | 41.464 | 34.217 |
| FAILED_BREAK_CLOSE | UP | 253 | 158 | 26.266 | 24.411 | 1.855 | 0.822 | 2 | 36.201 | 37.079 |
| FAILED_BREAK_CLOSE | DOWN | 227 | 141 | 23.404 | 25.229 | -1.825 | 0.827 | 1 | 35.674 | 35.588 |
| FAILED_BREAK_CONFIRMATION | UP | 86 | 71 | 25.352 | 24.271 | 1.081 | 0.939 | 2 | 38.723 | 30.230 |
| FAILED_BREAK_CONFIRMATION | DOWN | 90 | 71 | 17.606 | 26.672 | -9.066 | 0.082 | 1 | 32.671 | 38.046 |

### PMH

| entry_kind | direction | events | matched_dates | event_probability | baseline_probability | effect | bh_q | positive_years | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BREAK_CLOSE | UP | 1550 | 603 | 23.362 | 20.220 | 3.141 | 0.107 | 4 | 29.722 | 34.126 |
| BREAK_CLOSE | DOWN | 1162 | 459 | 28.071 | 20.967 | 7.105 | 0.005 | 4 | 36.478 | 29.438 |
| BREAK_FIRST_FULL | UP | 682 | 446 | 17.321 | 19.458 | -2.137 | 0.450 | 1 | 29.045 | 31.362 |
| BREAK_FIRST_FULL | DOWN | 499 | 314 | 28.238 | 21.566 | 6.672 | 0.008 | 4 | 36.816 | 31.678 |
| BREAK_NEXT_CLOSE_HOLD | UP | 1109 | 559 | 20.352 | 19.676 | 0.676 | 0.869 | 2 | 29.138 | 31.686 |
| BREAK_NEXT_CLOSE_HOLD | DOWN | 845 | 411 | 28.114 | 20.908 | 7.206 | 0.005 | 4 | 35.812 | 31.591 |
| BREAK_NEXT_FULL_HOLD | UP | 682 | 446 | 17.321 | 19.458 | -2.137 | 0.450 | 1 | 29.045 | 31.362 |
| BREAK_NEXT_FULL_HOLD | DOWN | 499 | 314 | 28.238 | 21.566 | 6.672 | 0.008 | 4 | 36.816 | 31.678 |
| RETEST_CLOSE_HOLD | UP | 471 | 269 | 14.820 | 14.333 | 0.487 | 0.939 | 3 | 25.576 | 30.324 |
| RETEST_CLOSE_HOLD | DOWN | 312 | 200 | 16.917 | 18.086 | -1.170 | 0.869 | 1 | 30.364 | 30.271 |
| RETEST_RANGE_ESCAPE | UP | 187 | 139 | 11.990 | 13.566 | -1.576 | 0.811 | 1 | 21.588 | 29.645 |
| RETEST_RANGE_ESCAPE | DOWN | 107 | 84 | 20.238 | 17.508 | 2.731 | 0.811 | 3 | 31.615 | 31.156 |
| REJECTION_CLOSE | UP | 479 | 272 | 15.025 | 14.246 | 0.779 | 0.872 | 3 | 25.592 | 30.138 |
| REJECTION_CLOSE | DOWN | 737 | 430 | 25.694 | 23.239 | 2.455 | 0.496 | 4 | 36.915 | 33.357 |
| REJECTION_CONFIRMATION | UP | 101 | 84 | 14.286 | 14.566 | -0.280 | 0.982 | 2 | 23.711 | 25.222 |
| REJECTION_CONFIRMATION | DOWN | 171 | 136 | 28.554 | 24.511 | 4.042 | 0.533 | 3 | 40.176 | 39.423 |
| FAILED_BREAK_CLOSE | UP | 299 | 208 | 15.024 | 14.510 | 0.514 | 0.939 | 3 | 26.550 | 33.314 |
| FAILED_BREAK_CLOSE | DOWN | 410 | 256 | 25.586 | 22.753 | 2.833 | 0.533 | 4 | 39.837 | 29.930 |
| FAILED_BREAK_CONFIRMATION | UP | 120 | 101 | 10.891 | 15.261 | -4.370 | 0.329 | 1 | 24.449 | 28.292 |
| FAILED_BREAK_CONFIRMATION | DOWN | 147 | 133 | 30.075 | 22.858 | 7.217 | 0.203 | 3 | 39.138 | 34.231 |

### PML

| entry_kind | direction | events | matched_dates | event_probability | baseline_probability | effect | bh_q | positive_years | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BREAK_CLOSE | UP | 1187 | 453 | 23.190 | 20.561 | 2.629 | 0.304 | 3 | 32.394 | 34.098 |
| BREAK_CLOSE | DOWN | 1485 | 551 | 31.418 | 25.329 | 6.089 | 0.005 | 4 | 36.755 | 34.994 |
| BREAK_FIRST_FULL | UP | 500 | 332 | 20.708 | 19.961 | 0.747 | 0.872 | 2 | 31.663 | 32.668 |
| BREAK_FIRST_FULL | DOWN | 633 | 395 | 27.785 | 24.646 | 3.139 | 0.329 | 2 | 34.993 | 35.299 |
| BREAK_NEXT_CLOSE_HOLD | UP | 833 | 421 | 21.595 | 19.873 | 1.722 | 0.582 | 4 | 30.557 | 34.198 |
| BREAK_NEXT_CLOSE_HOLD | DOWN | 1054 | 507 | 28.102 | 24.916 | 3.186 | 0.212 | 3 | 34.426 | 35.909 |
| BREAK_NEXT_FULL_HOLD | UP | 500 | 332 | 20.708 | 19.959 | 0.749 | 0.872 | 2 | 31.671 | 32.658 |
| BREAK_NEXT_FULL_HOLD | DOWN | 633 | 395 | 27.785 | 24.646 | 3.139 | 0.329 | 2 | 34.993 | 35.299 |
| RETEST_CLOSE_HOLD | UP | 353 | 204 | 23.820 | 16.381 | 7.439 | 0.036 | 4 | 30.041 | 30.684 |
| RETEST_CLOSE_HOLD | DOWN | 421 | 242 | 17.913 | 21.232 | -3.318 | 0.330 | 1 | 30.741 | 33.697 |
| RETEST_RANGE_ESCAPE | UP | 134 | 100 | 13.500 | 15.139 | -1.639 | 0.827 | 1 | 26.552 | 26.680 |
| RETEST_RANGE_ESCAPE | DOWN | 154 | 116 | 17.385 | 20.302 | -2.917 | 0.747 | 2 | 27.324 | 36.458 |
| REJECTION_CLOSE | UP | 719 | 399 | 26.318 | 21.554 | 4.765 | 0.036 | 4 | 34.293 | 36.480 |
| REJECTION_CLOSE | DOWN | 426 | 244 | 18.156 | 21.184 | -3.028 | 0.385 | 1 | 30.928 | 33.565 |
| REJECTION_CONFIRMATION | UP | 133 | 113 | 23.894 | 22.354 | 1.540 | 0.872 | 2 | 33.357 | 37.022 |
| REJECTION_CONFIRMATION | DOWN | 94 | 80 | 18.750 | 21.518 | -2.768 | 0.827 | 1 | 29.942 | 32.407 |
| FAILED_BREAK_CLOSE | UP | 407 | 274 | 20.468 | 21.659 | -1.191 | 0.827 | 2 | 32.844 | 38.860 |
| FAILED_BREAK_CLOSE | DOWN | 332 | 217 | 19.055 | 21.845 | -2.790 | 0.533 | 1 | 32.437 | 37.662 |
| FAILED_BREAK_CONFIRMATION | UP | 144 | 131 | 17.557 | 22.447 | -4.890 | 0.287 | 0 | 31.089 | 36.216 |
| FAILED_BREAK_CONFIRMATION | DOWN | 112 | 98 | 23.810 | 23.990 | -0.180 | 0.982 | 2 | 34.625 | 40.101 |

### O5H

| entry_kind | direction | events | matched_dates | event_probability | baseline_probability | effect | bh_q | positive_years | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BREAK_CLOSE | UP | 2107 | 787 | 25.469 | 22.941 | 2.528 | 0.164 | 3 | 31.883 | 35.341 |
| BREAK_CLOSE | DOWN | 1636 | 617 | 29.659 | 22.373 | 7.286 | 0.005 | 4 | 36.560 | 31.653 |
| BREAK_FIRST_FULL | UP | 909 | 585 | 21.823 | 21.477 | 0.347 | 0.939 | 1 | 30.718 | 32.770 |
| BREAK_FIRST_FULL | DOWN | 694 | 441 | 28.099 | 21.751 | 6.348 | 0.005 | 4 | 36.483 | 32.249 |
| BREAK_NEXT_CLOSE_HOLD | UP | 1518 | 746 | 23.313 | 22.221 | 1.091 | 0.747 | 2 | 30.801 | 33.216 |
| BREAK_NEXT_CLOSE_HOLD | DOWN | 1169 | 566 | 28.581 | 22.007 | 6.574 | 0.005 | 4 | 35.900 | 31.908 |
| BREAK_NEXT_FULL_HOLD | UP | 907 | 585 | 21.781 | 21.474 | 0.307 | 0.947 | 1 | 30.697 | 32.723 |
| BREAK_NEXT_FULL_HOLD | DOWN | 692 | 441 | 28.099 | 21.775 | 6.324 | 0.005 | 4 | 36.403 | 32.295 |
| RETEST_CLOSE_HOLD | UP | 679 | 381 | 20.118 | 17.214 | 2.904 | 0.287 | 3 | 29.427 | 32.583 |
| RETEST_CLOSE_HOLD | DOWN | 454 | 262 | 18.410 | 19.081 | -0.672 | 0.872 | 2 | 29.412 | 31.681 |
| RETEST_RANGE_ESCAPE | UP | 276 | 203 | 14.327 | 16.662 | -2.335 | 0.604 | 2 | 25.210 | 30.057 |
| RETEST_RANGE_ESCAPE | DOWN | 149 | 120 | 20.417 | 19.925 | 0.492 | 0.982 | 2 | 31.691 | 31.669 |
| REJECTION_CLOSE | UP | 691 | 385 | 20.206 | 17.181 | 3.025 | 0.287 | 3 | 29.511 | 32.448 |
| REJECTION_CLOSE | DOWN | 963 | 560 | 27.199 | 25.493 | 1.707 | 0.577 | 2 | 35.701 | 34.546 |
| REJECTION_CONFIRMATION | UP | 171 | 130 | 17.564 | 17.379 | 0.185 | 0.982 | 2 | 26.899 | 32.337 |
| REJECTION_CONFIRMATION | DOWN | 229 | 192 | 25.000 | 26.086 | -1.086 | 0.872 | 2 | 36.595 | 35.668 |
| FAILED_BREAK_CLOSE | UP | 448 | 283 | 19.711 | 17.478 | 2.234 | 0.579 | 2 | 29.703 | 33.351 |
| FAILED_BREAK_CLOSE | DOWN | 561 | 343 | 25.899 | 24.358 | 1.541 | 0.775 | 3 | 39.377 | 34.051 |
| FAILED_BREAK_CONFIRMATION | UP | 170 | 142 | 16.901 | 16.997 | -0.095 | 0.982 | 2 | 26.394 | 32.536 |
| FAILED_BREAK_CONFIRMATION | DOWN | 192 | 159 | 30.294 | 25.592 | 4.701 | 0.375 | 4 | 39.789 | 34.312 |

### O5L

| entry_kind | direction | events | matched_dates | event_probability | baseline_probability | effect | bh_q | positive_years | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BREAK_CLOSE | UP | 1603 | 597 | 24.824 | 21.472 | 3.352 | 0.067 | 3 | 32.942 | 32.804 |
| BREAK_CLOSE | DOWN | 2010 | 743 | 33.232 | 26.393 | 6.839 | 0.005 | 4 | 37.088 | 35.878 |
| BREAK_FIRST_FULL | UP | 672 | 435 | 19.483 | 20.072 | -0.589 | 0.872 | 2 | 31.294 | 33.237 |
| BREAK_FIRST_FULL | DOWN | 841 | 543 | 30.773 | 24.909 | 5.865 | 0.015 | 4 | 37.233 | 34.506 |
| BREAK_NEXT_CLOSE_HOLD | UP | 1135 | 561 | 21.298 | 20.315 | 0.983 | 0.775 | 3 | 31.367 | 33.192 |
| BREAK_NEXT_CLOSE_HOLD | DOWN | 1411 | 686 | 32.123 | 26.037 | 6.086 | 0.005 | 4 | 36.228 | 36.093 |
| BREAK_NEXT_FULL_HOLD | UP | 672 | 435 | 19.483 | 20.059 | -0.576 | 0.872 | 2 | 31.292 | 33.293 |
| BREAK_NEXT_FULL_HOLD | DOWN | 841 | 543 | 30.773 | 24.909 | 5.865 | 0.015 | 4 | 37.233 | 34.506 |
| RETEST_CLOSE_HOLD | UP | 515 | 289 | 17.622 | 16.170 | 1.452 | 0.747 | 3 | 29.626 | 35.302 |
| RETEST_CLOSE_HOLD | DOWN | 586 | 327 | 19.021 | 21.407 | -2.385 | 0.532 | 0 | 29.625 | 31.627 |
| RETEST_RANGE_ESCAPE | UP | 192 | 147 | 13.152 | 16.172 | -3.020 | 0.533 | 1 | 26.554 | 31.539 |
| RETEST_RANGE_ESCAPE | DOWN | 215 | 156 | 19.551 | 19.699 | -0.147 | 0.982 | 2 | 28.540 | 33.928 |
| REJECTION_CLOSE | UP | 1038 | 574 | 26.622 | 23.572 | 3.050 | 0.175 | 4 | 35.865 | 38.949 |
| REJECTION_CLOSE | DOWN | 595 | 332 | 19.187 | 21.374 | -2.187 | 0.533 | 1 | 29.821 | 31.317 |
| REJECTION_CONFIRMATION | UP | 233 | 205 | 22.520 | 24.595 | -2.075 | 0.750 | 0 | 35.117 | 38.256 |
| REJECTION_CONFIRMATION | DOWN | 136 | 110 | 22.121 | 21.763 | 0.358 | 0.982 | 3 | 31.530 | 34.970 |
| FAILED_BREAK_CLOSE | UP | 570 | 356 | 21.723 | 21.969 | -0.246 | 0.982 | 2 | 35.128 | 35.831 |
| FAILED_BREAK_CLOSE | DOWN | 445 | 281 | 23.962 | 22.243 | 1.719 | 0.775 | 2 | 31.982 | 34.100 |
| FAILED_BREAK_CONFIRMATION | UP | 218 | 190 | 20.263 | 21.422 | -1.159 | 0.869 | 1 | 34.321 | 35.828 |
| FAILED_BREAK_CONFIRMATION | DOWN | 151 | 124 | 25.806 | 22.049 | 3.757 | 0.595 | 1 | 36.136 | 31.672 |

### O15H

| entry_kind | direction | events | matched_dates | event_probability | baseline_probability | effect | bh_q | positive_years | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BREAK_CLOSE | UP | 1924 | 716 | 21.556 | 20.333 | 1.223 | 0.583 | 3 | 29.286 | 32.596 |
| BREAK_CLOSE | DOWN | 1470 | 558 | 27.143 | 20.326 | 6.817 | 0.005 | 4 | 35.165 | 28.997 |
| BREAK_FIRST_FULL | UP | 862 | 551 | 19.283 | 19.263 | 0.021 | 0.990 | 3 | 29.292 | 30.154 |
| BREAK_FIRST_FULL | DOWN | 629 | 388 | 26.396 | 19.281 | 7.115 | 0.005 | 4 | 36.559 | 29.799 |
| BREAK_NEXT_CLOSE_HOLD | UP | 1408 | 684 | 19.630 | 19.169 | 0.461 | 0.872 | 3 | 28.302 | 31.273 |
| BREAK_NEXT_CLOSE_HOLD | DOWN | 1059 | 509 | 26.234 | 19.843 | 6.391 | 0.005 | 4 | 34.486 | 29.791 |
| BREAK_NEXT_FULL_HOLD | UP | 860 | 551 | 19.238 | 19.259 | -0.022 | 0.990 | 3 | 29.267 | 30.108 |
| BREAK_NEXT_FULL_HOLD | DOWN | 628 | 388 | 26.396 | 19.297 | 7.099 | 0.005 | 4 | 36.436 | 29.817 |
| RETEST_CLOSE_HOLD | UP | 584 | 323 | 15.789 | 14.437 | 1.353 | 0.750 | 2 | 27.693 | 29.191 |
| RETEST_CLOSE_HOLD | DOWN | 412 | 238 | 15.560 | 17.849 | -2.289 | 0.553 | 1 | 28.429 | 27.216 |
| RETEST_RANGE_ESCAPE | UP | 257 | 189 | 12.257 | 14.245 | -1.987 | 0.664 | 1 | 23.551 | 28.921 |
| RETEST_RANGE_ESCAPE | DOWN | 141 | 105 | 19.524 | 19.065 | 0.459 | 0.982 | 2 | 28.240 | 33.883 |
| REJECTION_CLOSE | UP | 588 | 324 | 15.689 | 14.397 | 1.293 | 0.750 | 2 | 27.600 | 29.223 |
| REJECTION_CLOSE | DOWN | 875 | 495 | 24.158 | 23.963 | 0.195 | 0.982 | 2 | 33.770 | 30.387 |
| REJECTION_CONFIRMATION | UP | 151 | 113 | 13.717 | 15.342 | -1.625 | 0.850 | 1 | 24.649 | 30.509 |
| REJECTION_CONFIRMATION | DOWN | 207 | 172 | 20.930 | 23.922 | -2.991 | 0.582 | 1 | 33.116 | 34.337 |
| FAILED_BREAK_CLOSE | UP | 395 | 264 | 15.341 | 14.484 | 0.857 | 0.872 | 2 | 27.402 | 32.808 |
| FAILED_BREAK_CLOSE | DOWN | 484 | 295 | 25.610 | 21.920 | 3.690 | 0.286 | 3 | 37.187 | 30.607 |
| FAILED_BREAK_CONFIRMATION | UP | 157 | 128 | 14.453 | 13.992 | 0.462 | 0.979 | 1 | 25.563 | 31.965 |
| FAILED_BREAK_CONFIRMATION | DOWN | 184 | 152 | 27.741 | 22.123 | 5.618 | 0.287 | 3 | 40.249 | 32.137 |

### O15L

| entry_kind | direction | events | matched_dates | event_probability | baseline_probability | effect | bh_q | positive_years | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BREAK_CLOSE | UP | 1423 | 539 | 23.007 | 19.847 | 3.161 | 0.091 | 3 | 30.423 | 31.540 |
| BREAK_CLOSE | DOWN | 1798 | 660 | 30.095 | 24.765 | 5.330 | 0.012 | 4 | 35.498 | 33.605 |
| BREAK_FIRST_FULL | UP | 579 | 380 | 17.452 | 18.417 | -0.966 | 0.827 | 1 | 29.005 | 33.039 |
| BREAK_FIRST_FULL | DOWN | 734 | 470 | 29.057 | 23.301 | 5.756 | 0.020 | 4 | 35.893 | 33.542 |
| BREAK_NEXT_CLOSE_HOLD | UP | 987 | 500 | 19.690 | 18.834 | 0.856 | 0.827 | 2 | 29.696 | 32.988 |
| BREAK_NEXT_CLOSE_HOLD | DOWN | 1245 | 602 | 29.804 | 23.887 | 5.917 | 0.005 | 4 | 35.338 | 33.554 |
| BREAK_NEXT_FULL_HOLD | UP | 579 | 380 | 17.452 | 18.417 | -0.966 | 0.827 | 1 | 29.005 | 33.039 |
| BREAK_NEXT_FULL_HOLD | DOWN | 734 | 470 | 29.057 | 23.301 | 5.756 | 0.020 | 4 | 35.893 | 33.542 |
| RETEST_CLOSE_HOLD | UP | 438 | 254 | 19.042 | 15.408 | 3.634 | 0.271 | 4 | 29.435 | 34.016 |
| RETEST_CLOSE_HOLD | DOWN | 486 | 278 | 21.367 | 20.294 | 1.073 | 0.869 | 2 | 30.920 | 30.495 |
| RETEST_RANGE_ESCAPE | UP | 162 | 128 | 16.016 | 15.002 | 1.013 | 0.872 | 2 | 30.520 | 28.968 |
| RETEST_RANGE_ESCAPE | DOWN | 177 | 136 | 18.260 | 19.488 | -1.228 | 0.872 | 2 | 29.733 | 33.393 |
| REJECTION_CLOSE | UP | 847 | 479 | 25.254 | 21.398 | 3.856 | 0.091 | 4 | 33.865 | 36.323 |
| REJECTION_CLOSE | DOWN | 500 | 282 | 21.064 | 20.339 | 0.725 | 0.872 | 2 | 30.421 | 30.131 |
| REJECTION_CONFIRMATION | UP | 171 | 152 | 23.026 | 21.570 | 1.456 | 0.869 | 1 | 35.851 | 31.033 |
| REJECTION_CONFIRMATION | DOWN | 115 | 92 | 18.478 | 20.025 | -1.547 | 0.872 | 2 | 29.541 | 32.233 |
| FAILED_BREAK_CLOSE | UP | 522 | 324 | 19.866 | 19.948 | -0.082 | 0.982 | 2 | 31.866 | 34.184 |
| FAILED_BREAK_CLOSE | DOWN | 411 | 243 | 21.790 | 19.912 | 1.878 | 0.747 | 3 | 30.762 | 29.342 |
| FAILED_BREAK_CONFIRMATION | UP | 204 | 173 | 15.222 | 19.277 | -4.055 | 0.320 | 1 | 29.066 | 37.681 |
| FAILED_BREAK_CONFIRMATION | DOWN | 149 | 115 | 20.870 | 20.707 | 0.163 | 0.982 | 2 | 29.388 | 32.988 |

## Yearly stability

All four years for every candidate are in context_comparisons.csv and the viewer. Positive-year counts alone do not prove equality across years or execution profitability. The following shows the predeclared immediate-break DOWN reference for every level/year.

| level_type | value | events | complete | matched_dates | event_probability | baseline_probability | effect | mean_mfe | mean_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O15H | 2020 | 418 | 388 | 144 | 20.635 | 16.093 | 4.542 | 29.752 | 23.352 |
| O15H | 2021 | 334 | 311 | 128 | 16.669 | 15.454 | 1.215 | 28.305 | 24.029 |
| O15H | 2022 | 359 | 335 | 137 | 41.601 | 32.423 | 9.178 | 50.458 | 42.071 |
| O15H | 2023 | 359 | 336 | 149 | 29.139 | 17.481 | 11.658 | 32.517 | 27.080 |
| O15L | 2020 | 447 | 418 | 161 | 25.699 | 19.865 | 5.835 | 32.098 | 30.484 |
| O15L | 2021 | 435 | 409 | 152 | 31.318 | 20.452 | 10.867 | 33.882 | 28.382 |
| O15L | 2022 | 483 | 458 | 179 | 40.555 | 36.974 | 3.581 | 45.255 | 45.377 |
| O15L | 2023 | 433 | 412 | 168 | 22.055 | 20.355 | 1.700 | 29.704 | 28.871 |
| O5H | 2020 | 462 | 433 | 161 | 24.440 | 17.348 | 7.091 | 32.309 | 25.613 |
| O5H | 2021 | 372 | 345 | 140 | 21.879 | 17.927 | 3.953 | 31.063 | 25.798 |
| O5H | 2022 | 404 | 382 | 150 | 42.874 | 35.006 | 7.868 | 50.206 | 46.353 |
| O5H | 2023 | 398 | 379 | 166 | 29.343 | 19.583 | 9.760 | 32.666 | 29.067 |
| O5L | 2020 | 519 | 491 | 185 | 23.759 | 21.326 | 2.433 | 31.532 | 31.865 |
| O5L | 2021 | 501 | 474 | 178 | 28.245 | 21.446 | 6.799 | 32.418 | 32.806 |
| O5L | 2022 | 510 | 485 | 196 | 51.341 | 39.821 | 11.521 | 52.135 | 48.096 |
| O5L | 2023 | 480 | 453 | 184 | 28.289 | 21.970 | 6.319 | 31.886 | 30.363 |
| PDH | 2020 | 266 | 238 | 95 | 19.406 | 15.315 | 4.091 | 27.473 | 26.604 |
| PDH | 2021 | 233 | 223 | 89 | 20.562 | 14.277 | 6.285 | 26.083 | 23.288 |
| PDH | 2022 | 176 | 162 | 76 | 45.329 | 32.990 | 12.339 | 53.444 | 42.900 |
| PDH | 2023 | 211 | 197 | 89 | 24.625 | 18.864 | 5.761 | 31.567 | 27.136 |
| PDL | 2020 | 196 | 173 | 67 | 29.520 | 22.293 | 7.228 | 36.322 | 37.785 |
| PDL | 2021 | 217 | 196 | 82 | 29.634 | 19.735 | 9.900 | 34.395 | 31.787 |
| PDL | 2022 | 307 | 282 | 107 | 40.480 | 35.153 | 5.327 | 42.336 | 47.849 |
| PDL | 2023 | 197 | 185 | 82 | 27.247 | 20.519 | 6.729 | 31.936 | 28.132 |
| PMH | 2020 | 280 | 267 | 111 | 19.588 | 15.719 | 3.869 | 29.650 | 24.378 |
| PMH | 2021 | 312 | 292 | 111 | 21.474 | 15.845 | 5.628 | 30.617 | 25.829 |
| PMH | 2022 | 260 | 242 | 107 | 48.367 | 35.613 | 12.754 | 56.165 | 41.213 |
| PMH | 2023 | 310 | 295 | 130 | 24.244 | 17.765 | 6.479 | 32.308 | 27.930 |
| PML | 2020 | 297 | 276 | 118 | 22.634 | 21.183 | 1.451 | 32.937 | 31.001 |
| PML | 2021 | 368 | 348 | 136 | 28.708 | 20.656 | 8.052 | 33.832 | 32.315 |
| PML | 2022 | 452 | 428 | 157 | 47.178 | 36.950 | 10.228 | 47.366 | 44.185 |
| PML | 2023 | 368 | 349 | 140 | 23.780 | 20.331 | 3.448 | 29.678 | 29.553 |

## Distances, timing and adverse path

The viewer and fixed_point_outcomes.csv include every candidate at 5, 10, 15, 30, 60 minutes and actual session close, with 10/25/50/75/100/150/200-point thresholds. ATR-normalized 0.5/1/1.5/2 thresholds are secondary. There is no search for an optimal threshold.

A high/low touch of a distance does not imply realizable profit: both favorable and adverse thresholds may be reached, and the ordering inside one minute is unknown. Adverse excursion through the first favorable hit conservatively includes that entire minute. Median time is conditional on reaching the threshold; non-hits are not zero-minute hits.

## Entry coverage and paired comparisons

entry_frequency.csv supplies all raw event counts, distinct roots/dates, available level dates and eligible root denominators. Repeated retests can generate several entry observations for one break; root coverage and event counts are separate. Root opportunities for break/retest/failure are all matching-direction breaks; rejection uses matching-approach TOUCH observations.

paired_entry_comparisons.csv uses the earliest available candidate per root and direction. It reports confirmation delay, common-root hit rates, and early 50-point opportunities without a later entry. Because common-root membership is selected by the later signal, this is a diagnostic comparison, not a causal ranking or a new entry eligibility filter.

## Censoring and limitations

| horizon | raw_events | complete | censored | atr_unavailable_complete | censor_reasons |
| --- | --- | --- | --- | --- | --- |
| 5 | 88911 | 87856 | 1055 | 75 | {"OUTSIDE_SESSION": 1055} |
| 10 | 88911 | 86839 | 2072 | 75 | {"OUTSIDE_SESSION": 2072} |
| 15 | 88911 | 86041 | 2870 | 75 | {"OUTSIDE_SESSION": 2870} |
| 30 | 88911 | 83709 | 5202 | 75 | {"OUTSIDE_SESSION": 5202} |
| 60 | 88911 | 78874 | 10037 | 75 | {"MISSING_MINUTES": 2, "OUTSIDE_SESSION": 10035} |
| session_close | 88911 | 87842 | 1069 | 71 | {"MISSING_MINUTES": 14, "OUTSIDE_SESSION": 1055} |

Future horizon completeness never affects causal event membership. A session-close observation is not a completed 30-minute observation. Missing ATR stays eligible for point measurements; ATR-normalized values remain unavailable. No source minute is fabricated.

The event detector’s rejection is the first candle of a touching episode with a close at least one tick back on the approach side. A failed break is the immediately next candle, not an arbitrary failure hours later. Retest-range escape is the explicitly frozen range mechanic; none of these claims to enumerate every discretionary visual pattern.
The matched pool controls year, confirmation half-hour and causal ATR bucket, not every trend or regime feature. Bootstrap intervals condition on this empirical pool. Date clustering addresses repeated observations within dates but is not a guarantee against serial dependence across days. Development has been inspected in previous projects. All nonprimary distances, horizons, yearly and contextual splits are exploratory.

## Integrity and reproducibility

Verified 88,911 unique causal entries, 566,636 exact source OHLC checks, all 1003 available opening-15m dates against actual one-minute extrema, and 32 deterministic chart examples. Source hashes and prior artifacts are unchanged.
Reproduction scripts are under scripts/eight_level_study. Full, unsampled source/entry observations and outcomes are retained in Parquet. Aggregate CSV/JSON, the protocol, report, viewer and audit charts are included in the bundle; the evidence manifest links full raw files by hash. Validation/OOS outcomes were not accessed; no paid downloads, strategy optimization or production execution changes occurred.

## What this supports next

Review exact chart examples and candidate-specific adverse paths first. The downward-break associations merit review as research observations, but this task does not select a final strategy, entry or target. Any later execution test needs frozen risk/exit/cost rules and must retain unsuccessful breaks and missed confirmations.

## Delivery verification

- 87 backend/research tests, 29 frontend tests and 1 browser smoke test passed.
- Production build passed; existing large-bundle warning remains.
- All 54 deterministic research artifacts reproduced byte-for-byte; the ZIP also reproduced exactly.
- All 32 chart files loaded in the browser; eight examples spanning all eight levels and four reaction families were visually reviewed.
- Level/entry/direction/horizon controls, reset, evidence/year tables and CSV/JSON/ZIP downloads passed.
- Full repeat took 72.373 seconds; retained artifacts total 72,982,271 bytes, including the 3,303,001-byte ZIP.
- Idle Lab restart preserved run/study/version/reveal metadata. No outcome columns were queried for this check.
- Actual Validation/OOS outcomes were not accessed. No production strategy/execution code changed.

Open **Research → Eight-level reaction and entry study** in the Lab. Full local artifacts are under `work/eight-level-reaction-entry-study-v1/`; the complete protocol and every aggregate table are in `study_bundle.zip`.
