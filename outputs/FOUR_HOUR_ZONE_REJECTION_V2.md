# Newest-zone penetration/rejection — Development v2

**DEVELOPMENT_ONLY_NOT_VALIDATED.** This tests only the user-confirmed penetration/rejection setup. No taps, breakout entries, additional filters or optimization.

## Rules and scope

Accepted Development 2020–2023 historical subset. One newest confirmed supply and one newest demand; permanent same-type replacement, no older-zone fallback. Entire confirmed five-minute candle beyond the distal edge invalidates a zone at any trading hour. Body-only or wick-only penetration does not invalidate. Zone state persists overnight, but pending entry episodes remain RTH-only and reset overnight, as in the frozen previous entry convention.

Price must penetrate the near edge, then the first separate full five-minute candle including wicks back outside triggers: short below supply, long above demand. Entry at confirmation close; subsequent one-minute activity only. One open position overall; a fresh episode after exit is needed for reentry. No holidays/half-days, session-close exit.

One MNQ micro; one-tick buffer beyond the opposite zone boundary; fixed original 2R; no management. One adverse tick each side and actual $0.73/side fees. Replacing or invalidating the source zone does not move an already-open trade’s stop or target.

## Overall results

| trades | wins | losses | win_rate | net_usd | pf | average_r | max_drawdown_usd | reached_1r | reached_2r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 115 | 42 | 73 | 36.522 | -1,776.400 | 0.815 | -0.122 | 2,169.820 | 34 | 14 |

| gross_usd | fees_usd | net_usd | total_r | median_r | average_risk_points | median_risk_points | max_risk_points | session_close_exits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -1,608.500 | 167.900 | -1,776.400 | -14.055 | -0.525 | 84.939 | 70.250 | 230.250 | 50 |

## Requested milestone counts

| trades | reached_1r | reached_1r_pct | reached_2r | reached_2r_pct | 1r_ambiguity | 2r_ambiguity |
| --- | --- | --- | --- | --- | --- | --- |
| 115 | 34 | 29.565 | 14 | 12.174 | 0 | 0 |

Milestones are gross price movement from the executed entry divided by original structural risk. They are counted only before actual exit. Reaching 1R does not exit or move the stop. Same-minute stop/threshold contact counts stop-first, not success; ambiguity is reported separately. The two counts overlap: trades reaching 2R also reach 1R. Costs mean a target fill is slightly less than net 2R.

## Yearly

| year | trades | wins | losses | win_rate | net_usd | pf | average_r | max_drawdown_usd | reached_1r | reached_2r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 17 | 6 | 11 | 35.294 | 117.680 | 1.141 | 0.013 | 448.640 | 7 | 3 |
| 2021 | 25 | 8 | 17 | 32.000 | -809.500 | 0.633 | -0.224 | 962.900 | 5 | 3 |
| 2022 | 42 | 16 | 26 | 38.095 | -1,087.820 | 0.780 | -0.119 | 2,169.800 | 11 | 4 |
| 2023 | 31 | 12 | 19 | 38.710 | 3.240 | 1.002 | -0.120 | 875.180 | 11 | 4 |

## Direction

| direction | trades | wins | losses | win_rate | net_usd | pf | average_r | max_drawdown_usd | reached_1r | reached_2r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LONG | 46 | 18 | 28 | 39.130 | 144.340 | 1.035 | 0.020 | 1,167.500 | 17 | 7 |
| SHORT | 69 | 24 | 45 | 34.783 | -1,920.740 | 0.646 | -0.217 | 2,652.760 | 17 | 7 |

## Excursions

| average_mfe_points | median_mfe_points | average_mae_points | median_mae_points | average_mfe_r | average_mae_r | average_duration_minutes | same_minute_conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 65.702 | 43.750 | 60.815 | 51.000 | 0.798 | 0.745 | 141.052 | 0 |

MFE/MAE preserve the native full exit-minute range and can include movement after the actual fill; milestone counts instead use conservative ordering.

## Accounting and preservation

Raw signals: 214. Selection outcomes: {"AT_SESSION_CLOSE": 5, "ENTERED": 115, "EPISODE_BEGAN_BEFORE_PREVIOUS_EXIT": 13, "POSITION_OPEN": 81}.
Zone-state transitions: {"AVAILABLE": 320, "FULL_5M_BREAK": 138, "REPLACED_BY_NEW_ZONE": 182}.
Reproduced all 320 accepted zone formations exactly. 933 eligible full XNYS sessions; 104 unresolved historical dates excluded from entries; 7 incomplete RTH bars cleared pending patterns. All 115 completed fills independently reconciled, including fees, exit time, stop/target conflicts and excursions.

Historical provider lifecycle and prior backtest files are unchanged. This strategy’s five-minute lifecycle is separate. Confirmed complete source bars are used for all-hours invalidation even when a date is excluded from entry eligibility. Absent/incomplete source bars cannot establish a break; no hidden break is guessed. Owned execution gaps are explicit failures, never fabricated fills.

No Validation/OOS outcome rows read; both data files are predicate-scanned only within Development. Full-file hashes verify preservation. No paid downloads, database changes or parameter searches. Results are reproducible research artifacts, not saved-run database entries.

## Reproduction and checks

Run `work/.venv/bin/python scripts/zone_rejection_v2/verify.py`. It runs scoped synthetic/regression tests and two full backtests, requiring byte-identical result/configuration artifacts. See reproducibility_manifest.json and synthetic_test_results.txt. Detailed signals, zone transitions, per-trade milestones, monthly tables and equity remain local in the results directory.

## Completed verification and review

144 scoped tests passed (12 new tests for newest-zone selection, all-hours invalidation, causal replacement and milestone ordering, plus 132 existing tests). Two full Development reruns produced byte-identical artifacts. All 115 native fills matched the independent execution check. No selected trade failed for missing owned execution data. Prior results and source hashes remained unchanged. Production engine code was not modified.

This specified run lost $1,776.40 after fees and slippage. Of 115 trades, 34 reached 1R (29.57%) and 14 reached 2R (12.17%) before exit; those counts overlap. Twenty reached 1R without subsequently reaching 2R before exit. No intraminute stop/milestone conflicts affected the counts. Long trades contributed +$144.34 and shorts −$1,920.74. No new filter or target is selected from these results.

This committed copy includes the completed verification; the deterministic generated report and detailed trade/milestone records remain in `work/four-hour-zone-rejection-v2/results/`.
