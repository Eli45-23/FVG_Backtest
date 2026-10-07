# CONT-A — Second-Candle FVG Continuation: zero-cost baseline

One MNQ micro, $2/index point, 0.25-point ticks. Structural first-post-FVG-candle stop ± one tick; fixed original 2R target; otherwise 16:00 ET close. Commission and slippage are zero. No trade management or parameter optimization.

## Signal reconciliation and selection

The independent 5-minute signal builder finds **1,649** raw events, matching exactly the FVG-ID set in the lifecycle file. The prior **1,639** research count excluded **9** events with incomplete later-day bars and **1** on a censored final NY date. Applying that same qualification reproduces 1,639, average subsequent MFE 125.1951 points and median 82.50. These hindsight exclusions are **not entry filters** here. All raw events also satisfy the strict favorable-side condition.

| Audit result | Signals |
| --- | --- |
| DAILY_LOCK_COMPETING_SIGNAL | 127 |
| NOT_FULL_XNYS_SESSION | 19 |
| SELECTED | 263 |
| TRIGGER_AT_OR_AFTER_1100 | 1240 |

Eligible signals before daily lock: **390**. The first eligible signal per date wins; ties use oldest formation, then stable FVG ID. Rejected and competing signals are saved individually in the ignored audit CSV. Filter reasons are sequential: the 11:00 trigger-start cutoff is checked before the calendar.

## Overall performance

| Metric | Value |
| --- | --- |
| average_duration_minutes | 85.4829 |
| average_loser_usd | -136.7932 |
| average_pnl_per_trade_usd | 1.9981 |
| average_r | 0.1047 |
| average_risk_points | 69.2833 |
| average_winner_usd | 224.6139 |
| breakeven | 0 |
| gross_loss_usd | 22,160.5000 |
| gross_pnl_usd | 525.5000 |
| gross_profit_usd | 22,686.0000 |
| largest_loser_usd | -1,472.5000 |
| largest_winner_usd | 846.0000 |
| long_trades | 145 |
| losers | 162 |
| max_closed_trade_drawdown_usd | 2,488.0000 |
| max_drawdown_bottom_time_utc | 2026-06-29T14:31:00+00:00 |
| max_drawdown_peak_is_initial_zero | False |
| max_drawdown_peak_time_utc | 2025-11-14T15:48:00+00:00 |
| maximum_consecutive_losses | 10 |
| maximum_consecutive_wins | 5 |
| median_duration_minutes | 42.0000 |
| median_loser_usd | -114.5000 |
| median_r | -1.0000 |
| median_risk_points | 59.5000 |
| median_winner_usd | 200.0000 |
| net_pnl_points | 262.7500 |
| net_pnl_usd | 525.5000 |
| peak_equity_usd | 2,432.5000 |
| peak_recovered | False |
| profit_factor | 1.0237 |
| profit_factor_status | finite |
| recovery_time_utc | N/A |
| same_minute_conflicts | 0 |
| session_close_trades | 21 |
| short_trades | 118 |
| total_r | 27.5416 |
| trades | 263 |
| win_rate_percent | 38.4030 |
| winners | 101 |

Profit/loss statistics are USD unless explicitly labeled points or R. Gross loss is a positive magnitude. Gross profit/loss split net trade P&L into positive/negative contributions; with zero costs these equal gross values. R uses each trade’s original risk; varying risk sizes explain why positive total R can coexist with a small dollar profit. Win rate uses all trades, including session-close exits and any breakevens.

## Long versus short

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd | average_risk_points |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LONG | 145 | 38.6207 | -558.5000 | 0.9498 | 0.1025 | 2,406.5000 | 60.0414 |
| SHORT | 118 | 38.1356 | 1,084.0000 | 1.0982 | 0.1074 | 2,123.0000 | 80.6398 |

## Yearly performance

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd |
| --- | --- | --- | --- | --- | --- | --- |
| 2024 | 88 | 38.6364 | 1,164.0000 | 1.2302 | 0.1415 | 856.0000 |
| 2025 | 101 | 41.5842 | 599.5000 | 1.0685 | 0.2103 | 1,853.0000 |
| 2026 | 74 | 33.7838 | -1,238.0000 | 0.8517 | -0.0832 | 2,041.0000 |

2026 ends with the available October 5 session and is a partial year. Group drawdowns are recomputed from zero for that group, not inherited from overall equity.

## Monthly performance

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd | long_pnl_usd | short_pnl_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-01 | 7 | 42.8571 | -14.0000 | 0.9365 | 0.0357 | 157.5000 | 83.5000 | -97.5000 |
| 2024-02 | 11 | 45.4545 | 68.5000 | 1.1299 | 0.4100 | 239.5000 | 163.5000 | -95.0000 |
| 2024-03 | 6 | 33.3333 | -5.5000 | 0.9838 | 0.0000 | 216.5000 | 25.5000 | -31.0000 |
| 2024-04 | 4 | 0.0000 | -309.5000 | 0.0000 | -1.0000 | 309.5000 | -52.5000 | -257.0000 |
| 2024-05 | 8 | 50.0000 | 261.0000 | 1.7909 | 0.5000 | 330.0000 | 133.5000 | 127.5000 |
| 2024-06 | 4 | 75.0000 | 512.0000 | 11.4490 | 1.2500 | 49.0000 | 48.0000 | 464.0000 |
| 2024-07 | 7 | 42.8571 | 261.5000 | 1.5173 | 0.2857 | 339.5000 | 231.0000 | 30.5000 |
| 2024-08 | 9 | 55.5556 | 524.0000 | 2.0417 | 0.6988 | 307.5000 | 297.0000 | 227.0000 |
| 2024-09 | 9 | 22.2222 | -275.5000 | 0.6182 | -0.3333 | 626.0000 | -331.5000 | 56.0000 |
| 2024-10 | 12 | 33.3333 | 154.0000 | 1.1732 | -0.0495 | 447.0000 | -539.5000 | 693.5000 |
| 2024-11 | 6 | 33.3333 | 84.0000 | 1.2809 | 0.0000 | 212.0000 | 4.5000 | 79.5000 |
| 2024-12 | 5 | 20.0000 | -96.5000 | 0.7323 | -0.4000 | 360.5000 | 170.0000 | -266.5000 |
| 2025-01 | 10 | 30.0000 | -191.5000 | 0.7450 | -0.2819 | 487.0000 | -485.5000 | 294.0000 |
| 2025-02 | 6 | 50.0000 | 381.5000 | 1.6831 | 0.2224 | 558.5000 | 93.0000 | 288.5000 |
| 2025-03 | 7 | 28.5714 | -244.0000 | 0.6499 | -0.1429 | 547.0000 | -326.5000 | 82.5000 |
| 2025-04 | 6 | 66.6667 | -767.0000 | 0.5861 | 1.0000 | 1,853.0000 | -386.5000 | -380.5000 |
| 2025-05 | 11 | 54.5455 | 1,049.0000 | 2.8665 | 0.6364 | 322.5000 | 1,094.5000 | -45.5000 |
| 2025-06 | 7 | 28.5714 | -262.0000 | 0.5094 | -0.1429 | 344.5000 | 31.5000 | -293.5000 |
| 2025-07 | 11 | 45.4545 | 289.5000 | 1.7018 | 0.3993 | 318.5000 | 50.0000 | 239.5000 |
| 2025-08 | 9 | 55.5556 | 602.5000 | 2.1379 | 0.4479 | 276.5000 | 45.5000 | 557.0000 |
| 2025-09 | 10 | 40.0000 | -55.0000 | 0.9077 | 0.2725 | 228.0000 | -95.5000 | 40.5000 |
| 2025-10 | 9 | 33.3333 | -91.5000 | 0.8275 | 0.0000 | 359.5000 | 130.0000 | -221.5000 |
| 2025-11 | 9 | 33.3333 | -118.5000 | 0.8957 | 0.0644 | 675.5000 | -151.5000 | 33.0000 |
| 2025-12 | 6 | 33.3333 | 6.5000 | 1.0109 | 0.0000 | 363.0000 | -289.0000 | 295.5000 |
| 2026-01 | 8 | 25.0000 | -548.5000 | 0.3949 | -0.5503 | 770.5000 | 1.0000 | -549.5000 |
| 2026-02 | 11 | 36.3636 | -526.5000 | 0.6518 | -0.0236 | 1,163.0000 | -210.5000 | -316.0000 |
| 2026-03 | 8 | 37.5000 | 54.5000 | 1.0677 | 0.1250 | 687.5000 | 478.5000 | -424.0000 |
| 2026-04 | 8 | 25.0000 | 54.0000 | 1.0966 | -0.2500 | 559.0000 | 54.0000 | 0 |
| 2026-05 | 9 | 33.3333 | -199.0000 | 0.7628 | 0.0000 | 839.0000 | 175.0000 | -374.0000 |
| 2026-06 | 12 | 25.0000 | -653.5000 | 0.6965 | -0.3339 | 1,200.5000 | -1,063.0000 | 409.5000 |
| 2026-07 | 5 | 40.0000 | 666.0000 | 2.5524 | 0.3372 | 217.0000 | -308.0000 | 974.0000 |
| 2026-08 | 7 | 28.5714 | -528.0000 | 0.4433 | -0.3675 | 829.0000 | 260.5000 | -788.5000 |
| 2026-09 | 6 | 66.6667 | 443.0000 | 3.2487 | 0.7331 | 138.0000 | 111.0000 | 332.0000 |
| 2026-10 | 0 | N/A | 0 | N/A | N/A | 0.0000 | 0 | 0 |

## Trigger-bar start time, America/New_York

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd | signals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 09:30-09:59 | 94 | 43.6170 | 1,605.5000 | 1.2083 | 0.2405 | 2,090.0000 | 115 |
| 10:00-10:29 | 96 | 33.3333 | -2,315.5000 | 0.7552 | -0.0390 | 3,584.0000 | 144 |
| 10:30-10:59 | 73 | 38.3562 | 1,235.5000 | 1.2474 | 0.1190 | 1,364.5000 | 131 |

Time buckets use the second candle’s START; a 10:55 trigger enters at 11:00 and belongs to 10:30–10:59. A trigger starting 11:00 is rejected.

## Weekday

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd |
| --- | --- | --- | --- | --- | --- | --- |
| Monday | 52 | 34.6154 | -1,986.5000 | 0.6226 | -0.0201 | 2,710.5000 |
| Tuesday | 44 | 52.2727 | 2,880.0000 | 1.9185 | 0.5230 | 1,653.0000 |
| Wednesday | 56 | 37.5000 | -228.0000 | 0.9430 | 0.0518 | 1,563.5000 |
| Thursday | 60 | 40.0000 | 1,480.5000 | 1.2943 | 0.1756 | 1,324.5000 |
| Friday | 51 | 29.4118 | -1,620.5000 | 0.6574 | -0.1540 | 2,335.5000 |

## Original stop-size research

| Group | trades | win_rate_percent | net_pnl_usd | profit_factor | average_r | max_closed_trade_drawdown_usd |
| --- | --- | --- | --- | --- | --- | --- |
| 0-25 | 16 | 50.0000 | 311.0000 | 1.9424 | 0.5000 | 163.5000 |
| 25-50 | 87 | 36.7816 | 723.5000 | 1.1738 | 0.0931 | 821.5000 |
| 50-75 | 84 | 41.6667 | 2,177.0000 | 1.3655 | 0.1892 | 1,002.5000 |
| 75-100 | 35 | 40.0000 | 1,092.0000 | 1.3288 | 0.1572 | 1,167.5000 |
| 100-150 | 29 | 31.0345 | -1,879.0000 | 0.5633 | -0.2742 | 2,118.5000 |
| 150-200 | 8 | 25.0000 | -597.0000 | 0.6923 | -0.2138 | 1,400.0000 |
| 200+ | 4 | 25.0000 | -1,302.0000 | 0.3939 | -0.0750 | 1,472.5000 |

Risk bins are left-inclusive/right-exclusive: 25 points belongs to 25–50; 200 belongs to 200+. These do not filter trades.

## MFE / MAE

| MFE threshold, points | Trades reaching it (%) |
| --- | --- |
| 25 | 70.7224 |
| 50 | 54.7529 |
| 75 | 41.0646 |
| 100 | 28.1369 |
| 150 | 12.5475 |
| 200 | 4.5627 |

| MFE threshold, original R | Trades reaching it (%) |
| --- | --- |
| 0.5 | 67.6806 |
| 1 | 53.9924 |
| 1.5 | 41.8251 |
| 2 | 33.4601 |

| Other excursion check | Value |
| --- | --- |
| average_mae_points | 59.1740 |
| average_mfe_points | 75.3660 |
| median_mae_points | 48.0000 |
| median_mfe_points | 59.0000 |
| stop_conflict_with_mfe_at_least_2r | 0 |
| stop_with_mfe_at_least_2r | 0 |

Excursions include full high/low of owned minutes through and including the exit minute. They exclude all signal-candle activity. For stop/target exits the intraminute ordering of that exit minute’s extrema is unknown; the trade log flags this. MFE/MAE are OHLC bounds, not necessarily realizable pre-fill excursions. Both levels in a minute resolve stop-first; the logged MFE may still exceed 2R.

## Equity and interpretation

Final closed-trade equity is **$525.50**, from an initial zero. Peak equity is **$2,432.50**. Maximum drawdown is **$2,488.00**, from the peak at 2025-11-14T15:48:00+00:00 to the bottom at 2026-06-29T14:31:00+00:00. Prior peak recovered: **False**. Longest losing streak: **10 trades**. The equity CSV preserves every closed-trade observation. This is closed-equity drawdown, not mark-to-market drawdown or an account-capital estimate.

The historical zero-cost result is marginal: PF **1.0237**, approximately **$2.00 per trade**. A uniform round-trip cost of that amount would consume the measured profit before any slippage-induced changes to paths. No cost scenario or parameter was optimized. This full-period descriptive baseline is not an out-of-sample demonstration of a durable edge.

## Calendar, execution and determinism

Calendar: `exchange_calendars 4.13.2`, XNYS, explicit bounds 2024-01-01 to 2026-10-06. A full session requires a local 09:30 open, 16:00 close and exactly 390 minutes. Non-session holidays/weekends and early closes are excluded, including the 2025-01-09 exceptional closure. The library computes its schedule locally; no internet lookup occurs during runs. The exact schedule and fingerprint are saved. [Official library documentation](https://github.com/gerrymanoim/exchange_calendars).

Entry is the confirmed second 5-minute close, timestamped at start + 5 minutes. The 1-minute bar starting exactly at entry is owned and evaluated; the preceding minute is excluded. Stop/target fills have an unknown intraminute time: `exit_bar_start_*` identifies the interval, and `exit_time_*` is its end/confirmation time. Duration uses that convention. Stops/targets stay active in 15:59–16:00 before a possible session-close exit.

An adverse opening gap beyond a stop fills at the worse of stop/open; targets fill at their limit with no favorable gap improvement. Stop-first priority applies even if both boundaries are crossed in a gap/conflict minute. Entry and all exit fills support adverse configured slippage ticks; initial risk/target use executed entry. Commission is charged twice. Baseline uses both at zero. Missing owned minutes fail the run rather than silently skipping a trade or simulating through the gap. No such failure occurred.

Executable prices are rounded to 0.25 ticks: nearest half-up for entry/target/exit, outward for structural stops. Current source prices are tick-aligned, so baseline rounding does not alter them. Body ratios, candle directions, range, and causal simple ATR(14) true-range means are recorded but never filter signals. ATR is nullable if 14 complete observations are unavailable and is descriptive across session/roll gaps.

Stable IDs depend on strategy version and signal identity. Results contain no wall-clock generation timestamps or random choices. Two complete runs must produce identical trade Parquet, CSV and summary bytes. Runtime dependencies and calendar are pinned; original inputs are fingerprinted before/after and validated layer code remains unchanged.

| Validation | Result |
| --- | --- |
| fills_excursions_pnl_match_independent_replay | True |
| independent_integer_execution_replay_trades | 263 |
| inputs_unchanged | True |
| no_late_entries | True |
| one_trade_per_date | True |
| original_stop_and_2r_target_only | True |
| owned_execution_minutes_complete | True |
| same_day_only | True |
| tick_alignment | True |

Reproduce with `work/.venv/bin/python outputs/cont_a_backtest.py`, then `work/.venv/bin/python outputs/cont_a_report.py`. Install any missing dependencies with `work/.venv/bin/python -m pip install -r outputs/requirements_backtest.txt`. Run all tests with `work/.venv/bin/python -m unittest discover -s outputs/tests -v`.

## Files

New source: `cont_a_backtest.py`, `cont_a_metrics.py`, `cont_a_validate.py`, `cont_a_report.py`, `requirements_backtest.txt`, `tests/test_cont_a.py`. `.gitignore` additionally excludes `outputs/results/`. Prior validated source/data files are unchanged.

Ignored `outputs/results/` contains `CONT_A_second_candle_baseline_trades.parquet`, matching `_trades.csv`, `_summary.json`, `_signal_audit.csv`, `_equity.csv` and `_xnys_calendar.csv`. The report is the only committed results document; no trade-level or market-data files are committed. This task requests a local commit only.

## Completed baseline verification

115 tests passed (36 CONT-A tests). Two complete runs produced byte-identical trade Parquet/CSV, summary, audit, calendar and equity files. All grouped trade counts and P&L reconcile. The independent raw-integer replay matched all 263 executions. Previous validated code and all four input files remained unchanged.
