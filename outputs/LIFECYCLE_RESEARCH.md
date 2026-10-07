# MNQ same-day FVG lifecycle research

Descriptive observations only. No entries, fills of orders, positions, exits, stops, targets or P&L are simulated.

Primary research denominator: full NY date covered, with no incomplete post-formation bars skipped. All records remain in Parquet; censoring and quality exclusions affect summaries only. Missing empty clock buckets are not synthesized and may include scheduled closures.

## Lifecycle counts and denominators

| Metric | All | Bullish | Bearish |
| --- | --- | --- | --- |
| records | 10608 | 5709 | 4899 |
| research_day_eligible | 10549 | 5676 | 4873 |
| censored_records | 18 | 12 | 6 |
| records_with_skipped_incomplete_bars | 41 | 21 | 20 |
| touched_in_observed_window | 9258 | 4964 | 4294 |
| untouched_in_observed_window | 1350 | 745 | 605 |
| touched_same_day | 9201 | 4932 | 4269 |
| never_touched_same_day | 1348 | 744 | 604 |
| fully_filled_observed | 8558 | 4571 | 3987 |
| close_invalidated_observed | 7787 | 4091 | 3696 |
| wick_invalidated_observed | 8545 | 4563 | 3982 |
| fully_filled_same_day | 8504 | 4541 | 3963 |
| close_invalidated_same_day | 7737 | 4065 | 3672 |
| wick_invalidated_same_day | 8491 | 4533 | 3958 |
| expired_untouched | 1341 | 744 | 597 |
| expired_after_touch | 719 | 399 | 320 |
| expired_untouched_qualified | 1340 | 744 | 596 |
| expired_after_touch_qualified | 718 | 399 | 319 |
| close_method_expired | 2814 | 1611 | 1203 |
| wick_method_expired | 2060 | 1143 | 917 |
| percent_touched_same_day | 87.221538 | 86.892178 | 87.605171 |
| percent_never_touched_same_day | 12.778462 | 13.107822 | 12.394829 |

“Observed” totals include established events on partial or quality-flagged histories. The same-day counts and percentages use the qualified denominator. Shared expiration means neither method invalidated; per-method expiration totals are retained separately.

### Bars until first touch (touched qualified records only)

| Direction | N | Average | Median |
| --- | --- | --- | --- |
| all | 9201 | 6.78 | 2.00 |
| bullish | 4932 | 7.00 | 2.00 |
| bearish | 4269 | 6.53 | 2.00 |

### Maximum points away before touch or expiry (all qualified records)

| Direction | N | Average | Median |
| --- | --- | --- | --- |
| all | 10549 | 64.18 | 27.25 |
| bullish | 5676 | 58.11 | 25.75 |
| bearish | 4873 | 71.24 | 29.50 |

### Maximum points away before first touch (touched qualified records only)

| Direction | N | Average | Median |
| --- | --- | --- | --- |
| all | 9201 | 37.29 | 16.25 |
| bullish | 4932 | 33.57 | 16.75 |
| bearish | 4269 | 41.59 | 16.00 |

## Never-touched continuation

This is a hindsight cohort: membership requires observing the entire date. It is not a real-time selection rule. No invalidation method is used as a research filter. A gap-through can invalidate without satisfying the overlap definition of touch.

| Cohort | Total | Bullish | Bearish | Avg away | Median away | >=10 % | >=25 % | >=50 % | >=75 % | >=100 % | >=150 % | >=200 % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 1348 | 744 | 604 | 247.69 | 193.62 | 99.925816 | 99.851632 | 97.626113 | 92.507418 | 84.866469 | 66.839763 | 48.367953 |
| bullish | 744 | 744 | 0 | 220.80 | 177.38 | 100.0 | 100.0 | 97.849462 | 91.935484 | 82.526882 | 60.752688 | 41.801075 |
| bearish | 604 | 0 | 604 | 280.81 | 224.62 | 99.834437 | 99.668874 | 97.350993 | 93.211921 | 87.748344 | 74.337748 | 56.456954 |

### By Candle 3 start time, America/New_York

| Time | Direction | N | Avg away | Median away | >=10 % | >=25 % | >=50 % | >=75 % | >=100 % | >=150 % | >=200 % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 09:30-09:59 | all | 159 | 355.17 | 289.25 | 100.0 | 100.0 | 100.0 | 100.0 | 99.371069 | 93.710692 | 81.132075 |
| 09:30-09:59 | bullish | 91 | 327.67 | 271.00 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 91.208791 | 79.120879 |
| 09:30-09:59 | bearish | 68 | 391.97 | 312.62 | 100.0 | 100.0 | 100.0 | 100.0 | 98.529412 | 97.058824 | 83.823529 |
| 10:00-10:29 | all | 117 | 309.18 | 254.25 | 100.0 | 100.0 | 100.0 | 100.0 | 97.435897 | 86.324786 | 64.957265 |
| 10:00-10:29 | bullish | 59 | 269.20 | 221.25 | 100.0 | 100.0 | 100.0 | 100.0 | 98.305085 | 83.050847 | 57.627119 |
| 10:00-10:29 | bearish | 58 | 349.84 | 316.62 | 100.0 | 100.0 | 100.0 | 100.0 | 96.551724 | 89.655172 | 72.413793 |
| 10:30-10:59 | all | 92 | 341.88 | 279.38 | 100.0 | 100.0 | 100.0 | 100.0 | 98.913043 | 90.217391 | 78.26087 |
| 10:30-10:59 | bullish | 43 | 254.90 | 235.50 | 100.0 | 100.0 | 100.0 | 100.0 | 97.674419 | 88.372093 | 65.116279 |
| 10:30-10:59 | bearish | 49 | 418.21 | 328.75 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 91.836735 | 89.795918 |
| 11:00-and-later | all | 980 | 214.07 | 169.38 | 99.897959 | 99.795918 | 96.734694 | 89.693878 | 79.693878 | 57.959184 | 38.265306 |
| 11:00-and-later | bullish | 551 | 195.30 | 153.25 | 100.0 | 100.0 | 97.096189 | 89.110708 | 76.76951 | 51.179673 | 32.123412 |
| 11:00-and-later | bearish | 429 | 238.17 | 187.50 | 99.7669 | 99.5338 | 96.270396 | 90.44289 | 83.449883 | 66.666667 | 46.153846 |

## Second-candle continuation research

Denominator: both exact +5/+10-minute post-formation bars exist, are complete and have no zone overlap. Numerator: second close strictly exceeds the first high (bullish) or is below its low (bearish). MFE starts strictly after that second candle.

| Direction | First two untouched | Occurrences | Frequency % | MFE N | Avg MFE | Median MFE | >=25 % | >=50 % | >=100 % | >=150 % | >=200 % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 4973 | 1639 | 32.957973 | 1639 | 125.20 | 82.50 | 83.038438 | 67.419158 | 43.563148 | 28.370958 | 18.913972 |
| bullish | 2718 | 932 | 34.289919 | 932 | 112.13 | 75.00 | 81.866953 | 64.806867 | 40.128755 | 23.06867 | 14.592275 |
| bearish | 2255 | 707 | 31.35255 | 707 | 142.41 | 94.50 | 84.582744 | 70.862801 | 48.090523 | 35.360679 | 24.611033 |

## Pullback-continuation research

The first pause of each kind is recorded while still untouched. An occurrence requires a strictly later untouched candle to close beyond that pause’s running pre-pause extreme. Only one first occurrence per definition per FVG is counted; the definitions can overlap.

| Pause definition | Direction | Pauses | Occurrences | Frequency % | MFE N | Avg MFE | Median MFE | >=25 % | >=50 % | >=100 % | >=150 % | >=200 % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No new extreme | all | 5093 | 2444 | 47.987434 | 2442 | 114.20 | 77.25 | 79.156429 | 63.513514 | 39.92629 | 24.692875 | 16.298116 |
| No new extreme | bullish | 2786 | 1403 | 50.358938 | 1401 | 104.62 | 71.50 | 79.942898 | 61.456103 | 36.259814 | 20.913633 | 14.061385 |
| No new extreme | bearish | 2307 | 1041 | 45.123537 | 1041 | 127.10 | 87.75 | 78.097983 | 66.282421 | 44.860711 | 29.779059 | 19.308357 |
| Opposite close | all | 5593 | 2643 | 47.255498 | 2639 | 116.82 | 76.50 | 80.371353 | 63.054187 | 41.189845 | 25.464191 | 16.52141 |
| Opposite close | bullish | 3053 | 1518 | 49.721585 | 1514 | 106.87 | 71.62 | 80.05284 | 61.360634 | 37.978864 | 22.060766 | 13.738441 |
| Opposite close | bearish | 2540 | 1125 | 44.291339 | 1125 | 130.22 | 86.25 | 80.8 | 65.333333 | 45.511111 | 30.044444 | 20.266667 |

MFE is the nonnegative favorable extreme from the research occurrence close through later complete candles on the same NY date. It includes later price observations even after zone touch/invalidation, and excludes the occurrence candle itself. No subsequent complete candle means null MFE, not zero; these records remain in occurrence counts but are excluded from MFE averages and threshold denominators. Multiple FVGs can share candles, so counts are not independent trades.

## Validation

| Check | Passed |
| --- | --- |
| exactly_one_record_per_fvg | True |
| original_fvg_fields_preserved | True |
| no_candle3_or_prior_day_interactions | True |
| earliest_events_match_complete_source_bars | True |
| exact_first_second_slots_verified | True |
| untouched_extrema_verified | True |
| first_pause_and_trigger_predicates_and_thresholds_verified | True |
| mfe_excludes_trigger_candle | True |

Input files unchanged: True.

See [LIFECYCLE_LAYER.md](LIFECYCLE_LAYER.md) for field semantics, censoring, tests and reproducible commands. Full-precision summaries are retained in ignored `outputs/data/MNQ_FVG_LIFECYCLE_validation.json`.
