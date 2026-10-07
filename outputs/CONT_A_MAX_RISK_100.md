# CONT-A — Second-Candle Continuation — Max Risk <100

A true controlled backtest, not a filtered baseline CSV. The only changed strategy rule is original structural risk strictly below 100 points, applied before the daily lock. Baseline source, results and all validated inputs remain unchanged. Zero costs, one MNQ, unchanged original structural stop and fixed 2R target.

## Signal accounting

| Stage | Count |
| --- | --- |
| actual_trades | 235 |
| calendar_cutoff_positive_risk_eligible | 390 |
| competing_after_actual_entry | 102 |
| eligible_after_max_risk | 337 |
| max_risk_rejections | 53 |
| raw_signals | 1649 |
| replacement_trade_days | 13 |

| Audit reason | Signals |
| --- | --- |
| DAILY_LOCK_COMPETING_SIGNAL | 102 |
| MAX_RISK_FILTER | 53 |
| NOT_FULL_XNYS_SESSION | 19 |
| SELECTED | 235 |
| TRIGGER_AT_OR_AFTER_1100 | 1240 |

Cutoff and calendar precede risk eligibility. All otherwise-eligible signals with risk ≥100 are marked MAX_RISK_FILTER, including signals occurring after an actual entry; only risk-eligible later signals count as daily-lock competition. Rejection never consumes the daily slot. The baseline selector is reused to preserve chronological order and oldest-formation/FVG-ID ties. No signal generation or execution implementation is copied or altered.

Raw 1,649 events still exactly match lifecycle IDs. The prior qualified 1,639 excludes 9 later-day incomplete histories and 1 censored date; those future-known qualifications remain reconciliation only, not filters.

## Baseline and historical-subset comparison

| Metric | Original baseline | Old descriptive <100 subset | True <100 variant |
| --- | --- | --- | --- |
| trades | 263 | 222 | 235 |
| winners | 101 | 89 | 93 |
| losers | 162 | 133 | 142 |
| win_rate_percent | 38.4030 | 40.0901 | 39.5745 |
| net_pnl_usd | 525.5000 | 4,303.5000 | 4,277.0000 |
| gross_profit_usd | 22,686.0000 | 18,073.5000 | 19,259.5000 |
| gross_loss_usd | 22,160.5000 | 13,770.0000 | 14,982.5000 |
| profit_factor | 1.0237 | 1.3125 | 1.2855 |
| average_pnl_per_trade_usd | 1.9981 | 19.3851 | 18.2000 |
| average_r | 0.1047 | 0.1689 | 0.1553 |
| median_r | -1.0000 | -1.0000 | -1.0000 |
| total_r | 27.5416 | 37.5031 | 36.5031 |
| average_winner_usd | 224.6139 | 203.0730 | 207.0914 |
| average_loser_usd | -136.7932 | -103.5338 | -105.5106 |
| max_closed_trade_drawdown_usd | 2,488.0000 | 1,612.5000 | 1,725.0000 |
| maximum_consecutive_losses | 10 | 10 | 11 |
| average_risk_points | 69.2833 | 53.3750 | 54.2638 |
| median_risk_points | 59.5000 | 53.3750 | 54.7500 |

All 222 old subset trades remain byte-for-value identical across their original fields. The true run adds **13** replacement trades with **$-26.50** net P&L (4 winners, 9 losers). Thus $4,303.50 + (-26.5) = $4,277.00. Of 41 original wide-risk trade dates, 13 receive a later eligible trade and 28 have no qualifying replacement. The variant retains original signal-derived trade IDs for matching; its separate filename identifies the variant.

## Replacement-trade audit

Full identifiers and all trade details are in the ignored replacement CSV. Times below are America/New_York, including UTC offset.

| formation_date | direction | rejected_baseline_entry_time_ny | rejected_baseline_risk_points | entry_time_ny | risk_points | net_pnl_usd | exit_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-07-25 | LONG | 2024-07-25 10:10:00-04:00 | 105.5000 | 2024-07-25 10:35:00-04:00 | 59.5000 | 238.0000 | TARGET |
| 2025-02-20 | SHORT | 2025-02-20 10:00:00-05:00 | 132.0000 | 2025-02-20 10:55:00-05:00 | 56.2500 | -112.5000 | STOP |
| 2025-08-01 | SHORT | 2025-08-01 09:50:00-04:00 | 126.5000 | 2025-08-01 10:05:00-04:00 | 43.7500 | -87.5000 | STOP |
| 2025-09-05 | SHORT | 2025-09-05 10:25:00-04:00 | 101.0000 | 2025-09-05 10:40:00-04:00 | 48.5000 | 194.0000 | TARGET |
| 2025-11-14 | LONG | 2025-11-14 09:55:00-05:00 | 113.7500 | 2025-11-14 10:45:00-05:00 | 94.7500 | 379.0000 | TARGET |
| 2025-11-19 | SHORT | 2025-11-19 09:55:00-05:00 | 117.2500 | 2025-11-19 10:55:00-05:00 | 93.7500 | 375.0000 | TARGET |
| 2025-12-11 | LONG | 2025-12-11 09:50:00-05:00 | 118.2500 | 2025-12-11 10:25:00-05:00 | 91.2500 | -182.5000 | STOP |
| 2026-01-09 | LONG | 2026-01-09 10:30:00-05:00 | 102.2500 | 2026-01-09 10:35:00-05:00 | 67.0000 | -134.0000 | STOP |
| 2026-01-29 | SHORT | 2026-01-29 10:15:00-05:00 | 104.5000 | 2026-01-29 10:50:00-05:00 | 58.5000 | -117.0000 | STOP |
| 2026-03-31 | SHORT | 2026-03-31 09:50:00-04:00 | 124.5000 | 2026-03-31 10:55:00-04:00 | 97.7500 | -195.5000 | STOP |
| 2026-06-23 | LONG | 2026-06-23 10:05:00-04:00 | 142.2500 | 2026-06-23 10:15:00-04:00 | 69.0000 | -138.0000 | STOP |
| 2026-07-30 | LONG | 2026-07-30 10:00:00-04:00 | 108.5000 | 2026-07-30 10:05:00-04:00 | 77.5000 | -155.0000 | STOP |
| 2026-08-13 | LONG | 2026-08-13 09:50:00-04:00 | 139.7500 | 2026-08-13 10:15:00-04:00 | 45.2500 | -90.5000 | STOP |

## Trigger time (second candle start, New York)

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd | signals | average_risk_points |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 09:30-09:59 | 74 | 48.6486 | 3,300.5000 | 1.8172 | 0.3850 | 523.0000 | 89 | 56.7331 |
| 10:00-10:29 | 85 | 32.9412 | -124.5000 | 0.9792 | -0.0246 | 1,560.0000 | 126 | 53.5147 |
| 10:30-10:59 | 76 | 38.1579 | 1,101.0000 | 1.2224 | 0.1329 | 1,096.5000 | 122 | 52.6974 |

The true 10:00–10:29 result is −$124.50, PF 0.9792, versus +$529 in the old subset. Five replacement trades in this window all lost, totaling −$653.50. Eight replacements in 10:30–10:59 added +$627.00.

Signals in this table are eligible after the strict max-risk filter and before the daily lock. The 10:00–10:29 window remains included.

## Long versus short

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd | average_risk_points |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LONG | 140 | 39.2857 | 1,944.5000 | 1.2286 | 0.1356 | 1,617.0000 | 50.6839 |
| SHORT | 95 | 40.0000 | 2,332.5000 | 1.3601 | 0.1844 | 1,021.0000 | 59.5395 |

## Yearly

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd |
| --- | --- | --- | --- | --- | --- | --- |
| 2024 | 86 | 39.5349 | 1,504.0000 | 1.3254 | 0.1716 | 1,015.0000 |
| 2025 | 92 | 44.5652 | 3,295.0000 | 1.6086 | 0.3000 | 954.0000 |
| 2026 | 57 | 31.5789 | -522.0000 | 0.8944 | -0.1028 | 1,585.5000 |

2026 improves from baseline −$1,238 to −$522, but remains negative. Its six replacements all lost (−$830), reversing the old subset’s +$308. Long P&L improves from −$558.50 to +$1,944.50; short P&L improves from +$1,084 to +$2,332.50.

2026 is partial through the existing input period ending 2026-10-06 (exclusive). Group drawdowns restart from zero within each group.

## Monthly

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd | long_pnl_usd | short_pnl_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-01 | 7 | 42.8571 | -14.0000 | 0.9365 | 0.0357 | 157.5000 | 83.5000 | -97.5000 |
| 2024-02 | 11 | 45.4545 | 68.5000 | 1.1299 | 0.4100 | 239.5000 | 163.5000 | -95.0000 |
| 2024-03 | 6 | 33.3333 | -5.5000 | 0.9838 | 0.0000 | 216.5000 | 25.5000 | -31.0000 |
| 2024-04 | 4 | 0.0000 | -309.5000 | 0.0000 | -1.0000 | 309.5000 | -52.5000 | -257.0000 |
| 2024-05 | 8 | 50.0000 | 261.0000 | 1.7909 | 0.5000 | 330.0000 | 133.5000 | 127.5000 |
| 2024-06 | 4 | 75.0000 | 512.0000 | 11.4490 | 1.2500 | 49.0000 | 48.0000 | 464.0000 |
| 2024-07 | 7 | 57.1429 | 710.5000 | 3.4126 | 0.7143 | 207.0000 | 469.0000 | 241.5000 |
| 2024-08 | 8 | 62.5000 | 746.0000 | 3.6548 | 0.8750 | 112.5000 | 297.0000 | 449.0000 |
| 2024-09 | 9 | 22.2222 | -275.5000 | 0.6182 | -0.3333 | 626.0000 | -331.5000 | 56.0000 |
| 2024-10 | 11 | 27.2727 | -177.0000 | 0.8009 | -0.1818 | 447.0000 | -539.5000 | 362.5000 |
| 2024-11 | 6 | 33.3333 | 84.0000 | 1.2809 | 0.0000 | 212.0000 | 4.5000 | 79.5000 |
| 2024-12 | 5 | 20.0000 | -96.5000 | 0.7323 | -0.4000 | 360.5000 | 170.0000 | -266.5000 |
| 2025-01 | 10 | 30.0000 | -191.5000 | 0.7450 | -0.2819 | 487.0000 | -485.5000 | 294.0000 |
| 2025-02 | 4 | 25.0000 | -171.0000 | 0.5799 | -0.2500 | 407.0000 | 93.0000 | -264.0000 |
| 2025-03 | 7 | 28.5714 | -244.0000 | 0.6499 | -0.1429 | 547.0000 | -326.5000 | 82.5000 |
| 2025-04 | 4 | 100.0000 | 1,086.0000 | ∞ | 2.0000 | 0.0000 | 1,086.0000 | 0 |
| 2025-05 | 11 | 54.5455 | 1,049.0000 | 2.8665 | 0.6364 | 322.5000 | 1,094.5000 | -45.5000 |
| 2025-06 | 7 | 28.5714 | -262.0000 | 0.5094 | -0.1429 | 344.5000 | 31.5000 | -293.5000 |
| 2025-07 | 11 | 45.4545 | 289.5000 | 1.7018 | 0.3993 | 318.5000 | 50.0000 | 239.5000 |
| 2025-08 | 8 | 50.0000 | 333.0000 | 1.9148 | 0.2539 | 276.5000 | 45.5000 | 287.5000 |
| 2025-09 | 9 | 55.5556 | 422.5000 | 2.3520 | 0.6667 | 200.0000 | 132.5000 | 290.0000 |
| 2025-10 | 9 | 33.3333 | -91.5000 | 0.8275 | 0.0000 | 359.5000 | 130.0000 | -221.5000 |
| 2025-11 | 6 | 66.6667 | 1,014.5000 | 4.3537 | 1.0000 | 154.0000 | 225.0000 | 789.5000 |
| 2025-12 | 6 | 33.3333 | 60.5000 | 1.1117 | 0.0000 | 309.0000 | -471.5000 | 532.0000 |
| 2026-01 | 6 | 0.0000 | -714.0000 | 0.0000 | -1.0000 | 714.0000 | -291.0000 | -423.0000 |
| 2026-02 | 8 | 50.0000 | 394.5000 | 1.6675 | 0.3426 | 422.5000 | -210.5000 | 605.0000 |
| 2026-03 | 8 | 37.5000 | 108.0000 | 1.1438 | 0.1250 | 634.0000 | 727.5000 | -619.5000 |
| 2026-04 | 8 | 25.0000 | 54.0000 | 1.0966 | -0.2500 | 559.0000 | 54.0000 | 0 |
| 2026-05 | 8 | 37.5000 | 50.0000 | 1.0847 | 0.1250 | 590.0000 | 175.0000 | -125.0000 |
| 2026-06 | 5 | 0.0000 | -748.0000 | 0.0000 | -1.0000 | 748.0000 | -592.5000 | -155.5000 |
| 2026-07 | 3 | 33.3333 | 109.0000 | 1.3949 | 0.0000 | 155.0000 | -155.0000 | 264.0000 |
| 2026-08 | 5 | 20.0000 | -218.5000 | 0.5794 | -0.4000 | 519.5000 | 50.5000 | -269.0000 |
| 2026-09 | 6 | 66.6667 | 443.0000 | 3.2487 | 0.7331 | 138.0000 | 111.0000 | 332.0000 |
| 2026-10 | 0 | N/A | 0 | N/A | N/A | 0.0000 | 0 | 0 |

| Monthly statistic | Value |
| --- | --- |
| best_month | 2025-04 |
| longest_losing_month_sequence | 4 |
| losing_months | 14 |
| profitable_months | 19 |
| worst_month | 2026-06 |
| zero_pnl_months | 1 |

The longest losing-month sequence runs December 2024 through March 2025 (four months). A zero-P&L or no-trade month breaks a losing-month sequence. October 2026 is partial with no trades.

## Entry distance from favorable FVG boundary (points)

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd |
| --- | --- | --- | --- | --- | --- | --- |
| 0-25 | 6 | 50.0000 | 83.0000 | 1.7094 | 0.5000 | 77.0000 |
| 25-50 | 47 | 38.2979 | 425.5000 | 1.2325 | 0.1299 | 420.0000 |
| 50-75 | 75 | 37.3333 | 824.5000 | 1.1828 | 0.1025 | 715.5000 |
| 75-100 | 47 | 40.4255 | 919.5000 | 1.2661 | 0.1693 | 906.5000 |
| 100+ | 60 | 41.6667 | 2,024.5000 | 1.3994 | 0.1959 | 1,058.0000 |

Distance is entry − FVG top for longs and FVG bottom − entry for shorts. Bins include the lower bound and exclude the upper bound. This is descriptive only. Risk = distance − first-bar clearance + 0.25, so distance can exceed 100 despite risk <100.

## MFE / MAE

| Metric | Value |
| --- | --- |
| average_mae_points | 45.7245 |
| average_mae_r | 0.8532 |
| average_mfe_points | 64.4330 |
| average_mfe_r | 1.2055 |
| median_mae_points | 43.7500 |
| median_mfe_points | 51.2500 |
| stop_conflict_with_mfe_at_least_2r | 0 |
| stop_with_mfe_at_least_2r | 0 |

| MFE points reached | Percent |
| --- | --- |
| 25 | 68.9362 |
| 50 | 50.6383 |
| 75 | 37.4468 |
| 100 | 25.1064 |
| 150 | 8.5106 |
| 200 | 1.2766 |

| MFE original R reached | Percent |
| --- | --- |
| 0.5000 | 68.9362 |
| 1 | 56.1702 |
| 1.5000 | 43.8298 |
| 2 | 36.5957 |

## Equity

| Metric | Value |
| --- | --- |
| net_pnl_usd | 4,277.0000 |
| peak_equity_usd | 5,281.5000 |
| max_closed_trade_drawdown_usd | 1,725.0000 |
| max_drawdown_peak_time_utc | 2024-09-05T15:25:00+00:00 |
| max_drawdown_bottom_time_utc | 2025-03-19T14:44:00+00:00 |
| peak_recovered | True |
| recovery_time_utc | 2025-05-21T15:09:00+00:00 |
| maximum_consecutive_wins | 5 |
| maximum_consecutive_losses | 11 |

| Longest time below prior peak | Value |
| --- | --- |
| calendar_days | 257.9889 |
| end_utc | 2025-05-21T15:09:00+00:00 |
| observation_end | last recorded trade close; no mark-to-market |
| recovered | True |
| start_utc | 2024-09-05T15:25:00+00:00 |

Underwater duration is elapsed calendar time from the prior observed equity peak to the first equal-or-higher closed equity, or to the last recorded close if unrecovered. Initial zero is anchored at first entry if necessary. It is not mark-to-market. The longest episode and maximum-dollar drawdown need not be the same episode.

## Interpretation

The single-variable change improves net P&L by $3,751.50 and lowers maximum closed drawdown, while the longest losing streak increases from 10 to 11. Replacement trades slightly reduce profit relative to the historical subset. The long side improves materially, but 2026 remains weaker than earlier years. This is an in-sample controlled comparison prompted by research on the same history, not independent evidence of a durable edge. No other thresholds or filters were tested.

## Unchanged execution and reproducibility

The variant calls the original signal builder, level calculation, calendar, execution and metrics functions. Entry uses the confirmed second-candle close; ownership starts with the 1-minute bar beginning at entry. Stop-first resolves same-minute conflicts. Adverse gaps fill at the worse of stop/open; targets receive no favorable improvement. The 15:59 minute is evaluated before session-close exit. Missing owned minutes fail the run. Exit timestamps indicate minute-end confirmation. MFE/MAE include the full exit-minute range, whose intraminute order is unknown. No stop movement, protection, trailing, partial exits, candle-strength, ATR, distance or new time filters are present.

The original pinned exchange_calendars/XNYS full-session schedule is reused offline. Risk and executable prices use Decimal and 0.25-point ticks. 99.75 is allowed; 100.00 and 100.25 are rejected. Costs remain zero.

| Validation | Result |
| --- | --- |
| all_retained_baseline_trades_identical | True |
| fills_excursions_pnl_match_independent_replay | True |
| group_totals_reconcile | True |
| independent_integer_execution_replay_trades | 235 |
| owned_execution_minutes_complete | True |
| protected_files_unchanged | True |

Run: `work/.venv/bin/python outputs/cont_a_max_risk.py`. Render: `work/.venv/bin/python outputs/render_cont_a_max_risk.py`. Tests: `work/.venv/bin/python -m unittest discover -s outputs/tests -v`. A second run can use `--output-dir work/cont_a_max_risk_repeat`. No baseline runner is invoked.

New files: `cont_a_max_risk.py`, `render_cont_a_max_risk.py`, `tests/test_cont_a_max_risk.py`, and this report. All variant trades, summary, audit, replacements, equity and verification receipts remain ignored under `outputs/results/`. No baseline source or results files are changed.

Completed verification: **137 tests passed**, including 22 new variant tests. Two full runs yielded byte-identical trade Parquet, trade CSV, summary, audit, replacements and equity files. Independent raw-integer execution verification matched all 235 trades. Protected baseline files and inputs were unchanged.
