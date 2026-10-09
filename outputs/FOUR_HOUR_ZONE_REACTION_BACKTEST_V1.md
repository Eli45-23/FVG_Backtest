# Four-hour zone reaction backtests — Development v1

**DEVELOPMENT_ONLY_NOT_VALIDATED.** Human-label approval is no longer a prerequisite for this explicitly authorized mechanical experiment. It is not evidence of a trading edge.

## Frozen experiment

2020–2023 New York Development dates; accepted/resolved historical subset only. Supply/demand geometry, bar construction and lifecycle remain unchanged. Each setup is an independent account: one open position at a time, new contact episode required after exit. Results must not be added as though they were a combined portfolio.

One MNQ micro; fixed 2R; stop one tick beyond the opposite zone edge; confirmed whole five-minute candle including wicks; native one-minute fills starting at confirmation. One adverse tick entry and exit plus actual $0.73/side fees. No holidays, half-days, management, maximum-risk or indicator filters.

## Results after fees and slippage

| setup | trades | wins | losses | win_rate | net_usd | pf | average_r | max_drawdown_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 245 | 91 | 154 | 37.143 | -3,375.200 | 0.832 | -0.108 | 4,121.800 |
| B | 12 | 5 | 7 | 41.667 | 49.480 | 1.053 | 0.098 | 463.340 |
| C | 123 | 55 | 68 | 44.715 | 1,852.420 | 1.279 | 0.080 | 890.560 |

*A: penetrate then reject. B: exact boundary tap without penetration then reject. C: whole-candle break then immediate adjacent whole-candle confirmation.*

Profit factor uses net winning/losing trade dollars. Gross P&L already includes adverse slippage but excludes fees; R uses original executed risk. Drawdown starts from zero and uses closed trades.

| setup | signals | gross_usd | fees_usd | net_usd | total_r | median_r | average_risk_points | median_risk_points | max_risk_points |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 589 | -3,017.500 | 357.700 | -3,375.200 | -26.488 | -0.693 | 82.329 | 70.750 | 241.250 |
| B | 12 | 67.000 | 17.520 | 49.480 | 1.176 | -0.353 | 80.896 | 86.000 | 127.750 |
| C | 158 | 2,032.000 | 179.580 | 1,852.420 | 9.853 | -0.101 | 77.661 | 69.750 | 200.500 |

## Year-by-year results

| setup | year | trades | win_rate | net_usd | pf | average_r | max_drawdown_usd |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 2020 | 38 | 34.211 | -379.980 | 0.843 | -0.126 | 1,346.040 |
| A | 2021 | 49 | 34.694 | -456.540 | 0.874 | -0.216 | 1,034.120 |
| A | 2022 | 83 | 40.964 | -1,932.680 | 0.794 | -0.058 | 2,954.720 |
| A | 2023 | 75 | 36.000 | -606.000 | 0.871 | -0.084 | 1,249.720 |
| B | 2020 | 2 | 100.000 | 297.580 | — | 1.242 | 0.000 |
| B | 2021 | 2 | 0.000 | -154.920 | 0.000 | -1.031 | 154.920 |
| B | 2022 | 4 | 25.000 | -283.840 | 0.481 | -0.073 | 308.420 |
| B | 2023 | 4 | 50.000 | 190.660 | 1.796 | 0.261 | 239.420 |
| C | 2020 | 17 | 23.529 | -373.820 | 0.625 | -0.250 | 890.560 |
| C | 2021 | 30 | 43.333 | 84.200 | 1.052 | 0.079 | 469.260 |
| C | 2022 | 33 | 60.606 | 2,020.320 | 2.166 | 0.472 | 555.420 |
| C | 2023 | 43 | 41.860 | 121.720 | 1.053 | -0.090 | 843.980 |

## Long / short

| setup | direction | trades | net_usd | pf | average_r | max_drawdown_usd |
| --- | --- | --- | --- | --- | --- | --- |
| A | LONG | 117 | -1,877.320 | 0.826 | -0.071 | 2,499.060 |
| A | SHORT | 128 | -1,497.880 | 0.840 | -0.142 | 2,379.300 |
| B | LONG | 5 | -446.300 | 0.201 | -0.559 | 558.840 |
| B | SHORT | 7 | 495.780 | 2.297 | 0.567 | 238.460 |
| C | LONG | 68 | 1,232.220 | 1.452 | 0.082 | 756.260 |
| C | SHORT | 55 | 620.200 | 1.158 | 0.078 | 699.760 |

## Path and execution

| setup | average_mfe_points | average_mae_points | average_mfe_r | average_mae_r | average_duration_minutes | session_close_exits | same_minute_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 65.195 | 58.522 | 0.823 | 0.750 | 130.898 | 89 | 0 |
| B | 56.396 | 51.792 | 0.825 | 0.688 | 83.500 | 4 | 0 |
| C | 60.449 | 43.730 | 0.847 | 0.633 | 132.520 | 61 | 0 |

MFE/MAE include the exit minute’s full range. Intraminute ordering is unknown; these excursions can include movement after the simulated exit. Stop-first resolves same-minute stop/target ambiguity. Native adverse stop-gap fills are retained.

## Signal selection audit

- A: {"AT_SESSION_CLOSE": 10, "ENTERED": 245, "EPISODE_BEGAN_BEFORE_PREVIOUS_EXIT": 44, "POSITION_OPEN": 290}
- B: {"ENTERED": 12}
- C: {"AT_SESSION_CLOSE": 1, "ENTERED": 123, "EPISODE_BEGAN_BEFORE_PREVIOUS_EXIT": 4, "POSITION_OPEN": 30}

## Source and causality checks

Replayed 320 accepted zones (168 supply, 152 demand) and reproduced saved formation identities and lifecycle invalidations exactly. 104 unresolved calendar dates remain excluded. 933 eligible full XNYS sessions; 7 incomplete/invalid five-minute RTH bars reset pending patterns. All 380 completed fills were independently checked against the native executor, including exits, fees, timing, conflicts and MFE/MAE.

No future completeness or outcome label is used to select a signal. Any missing owned execution minute is reported as EXECUTION_DATA_UNAVAILABLE and locks that setup for the rest of the session; it is not silently dropped at signal detection. Entry at the session-closing instant is not permitted.

## Limitations

- These are new Development hypotheses, not validated strategies. The detector’s visual agreement with discretionary zones has not been established; the user explicitly waived that prerequisite.
- Results cover the accepted historical subset, not every Development session. Zone availability also depends on causal ATR warmup and source completeness.
- Contact episodes are measured within each RTH session and reset after data gaps; they are not the all-hours lifecycle touch counter.
- Pending C confirmation may complete after invalidation caused by that same breakout. The saved lifecycle is not changed; unrelated later breaks cannot reuse invalidated zones.
- The first pass does not optimize parameters or select a winning strategy. Monthly, direction, episode, equity, signal and trade tables accompany this report.
- These runs use the trusted native execution engine through a reproducible research runner; they are not inserted into the application’s saved-run database.
- Validation/OOS outcomes were not read. Existing market files and historical artifacts retain their hashes. No paid data was downloaded.

## Reproduction

Run `work/.venv/bin/python scripts/zone_reaction_backtest/verify.py` from the repository. The verification script runs the same experiment twice and requires byte-identical economic/configuration artifacts. Source identities and scoped test evidence are saved alongside results.

## Review of this first pass

Setup A lost money in every Development year. Setup B has only 12 trades and cannot support a firm conclusion. Setup C made $1,852.42 overall, but 2022 contributed $2,020.32; the other three years combined lost $167.90. Its positive aggregate is therefore not evidence of consistent yearly profitability. No automatic winner or next filter is selected.

## Completed verification

132 scoped synthetic/regression tests passed, including 21 new zone-reaction tests. Two complete Development reruns produced byte-identical economic, configuration, audit and generated-report artifacts. All 380 completed fills agreed with the independent reference. No selected trade encountered missing owned execution data. No same-minute stop/target conflicts occurred. Native execution, provider geometry and legacy data code were not modified; reserved-period historical golden runs were not re-executed.

The complete local result bundle is `work/four-hour-zone-reaction-backtest-v1/results/`, including the generated report, per-setup trade files, all raw signals, selection reasons, yearly/monthly/direction/episode tables, equity, source verification and the determinism manifest. This committed review copy adds interpretation and verification after the reproducible generated report.
