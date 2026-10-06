# Deterministic MNQ five-minute FVG formation

## Run and test

From the workspace root, with the existing pinned environment:

```sh
work/.venv/bin/python outputs/detect_fvgs.py
work/.venv/bin/python -m unittest discover -s outputs/tests -v
```

The detector reads `outputs/data/MNQ_5m_2024-01-01_2026-10-06.parquet`. It needs no API key, makes no network calls, and never modifies the input. A SHA-256 comparison confirms input immutability. Derived Parquet is written atomically after validation and checked by reading it back.

## Exact definition and scope

Adjacent source rows form Candle 1, Candle 2 and Candle 3. Rows are sorted chronologically in memory; incomplete or out-of-session rows are **not removed before forming triples**.

- All three bars must be complete. Both UTC start-time differences must equal five minutes.
- Normal formation requires all three starts in New York 09:30 inclusive to 16:00 exclusive.
- The sole premarket exception is the same-date 09:25 / 09:30 / 09:35 triple. The 09:20 / 09:25 / 09:30 triple is rejected.
- Bullish: Candle 3 low strictly exceeds Candle 1 high. Bottom = Candle 1 high; top = Candle 3 low.
- Bearish: Candle 3 high is strictly below Candle 1 low. Bottom = Candle 3 high; top = Candle 1 low.
- Equal touching wicks do not form a gap. Candle 2 has no additional direction, body, displacement or volume requirement.
- Every qualifying overlapping triple is retained. There is no minimum size, maximum size, merge, daily limit, cutoff or extra contract-roll filter.

The formation date is Candle 3's New York calendar date. Session eligibility here is a clock-time mask, not an exchange holiday or early-close calendar. This retains the user's data-layer definition; for example a qualifying holiday-morning triple is not excluded by a separate calendar rule.

Formation timestamps are **Candle 3 starts**, as requested. All three candles are fully observable only at Candle 3 start + five minutes: an opening exception has formation start 09:35 and is knowable at 09:40 ET. This layer does not implement later date eligibility, zone touches, invalidation, entries, stops, targets, trade management, backtesting or performance metrics.

## Output contract and IDs

`MNQ_FVGs_2024-01-01_2026-10-06.parquet` includes every requested record field:

- `fvg_id`, `direction` (`bullish` or `bearish`)
- `formation_bar_start_utc`, `formation_bar_start_ny`, `formation_date_ny`
- `candle1_start_utc`, `candle2_start_utc`, `candle3_start_utc`
- `bottom`, `top`, `size_points`, `opening_exception`
- `candle1_open/high/low/close`, `candle2_open/high/low/close`, `candle3_open/high/low/close`

UTC and America/New_York timestamps remain timezone-aware nanosecond timestamps; date is a date32. OHLC and zone values retain exact decimal128(20,9) prices. Gap size uses decimal128(21,9). There are no float comparisons or price rounding in detection. Printed averages/medians use nine decimal places, round-half-even.

IDs are the full SHA-256 of the ASCII string:

```
mnq-5m-fvg-v1|MNQ.v.0|direction|candle1_UTC_epoch_ns|candle2_UTC_epoch_ns|candle3_UTC_epoch_ns
```

The ID is independent of file paths, row numbers, process and timezone display. Changing only input order or input coverage does not change an event's ID. The identity represents the symbol/direction/triple; a future revised price within the same qualifying triple retains the same ID. Source-file SHA-256 is embedded separately for provenance. A changed definition should use a new ID version.

Input validation rejects duplicate, null, naive, unaligned or inconsistent timestamps; invalid OHLC; non-Decimal prices; and contradictory completeness flags. An empty or shorter-than-three input returns a typed empty output. It does not synthesize bars, deduplicate source rows or repair malformed input silently.

## Validation and manual evidence

The vectorized detector is checked against a separate sequential oracle over **every** source triple, including non-events. Every field of every detected record is compared, which checks both missing/spurious detections and candle/zone values. All source bars are read unchanged. Tests include exact-equality boundaries, every incomplete position, both possible missing intervals, opening/premarket/RTH boundaries, winter/summer offsets, ID stability, negative controls, typed empty output, exact decimals, deterministic Parquet bytes and randomized streams against the independent oracle.

The test suite contains 23 FVG tests and 19 existing bar-layer tests (42 total).

Ignored local evidence files under `outputs/data/`:

- `MNQ_FVGs_sample.csv`: exactly 10 FVG records, five bullish and five bearish (first five of each in chronological order).
- `MNQ_FVGs_spot_checks.txt`: human-readable table with formation ET time, all three candles' OHLC, direction, zone bounds, size and opening flag.
- `MNQ_FVGs_opening_exceptions_sample_months.txt`: every opening-exception event in January, February and March 2024, including both winter and daylight-saving offsets.
- `MNQ_FVGs_validation.json`: counts, size summaries, all validation confirmations and source fingerprint.

These tables and the full validation report are also printed by the command. The output data, CSVs and reports remain ignored; only source, synthetic tests and documentation are committed. Nothing is pushed.

## Validated local run

Read 195,546 bars. Found **10,608 FVGs**: 5,709 bullish and 4,899 bearish. Opening exceptions: **319**.

| Size statistic (points) | Bullish | Bearish |
|---|---:|---:|
| Average | 11.571290944 | 13.356042049 |
| Median | 7.250000000 | 8.000000000 |

Overall minimum size: 0.250000000 points; maximum: 577.500000000 points. The maximum is the bullish event at 2025-04-07 10:15 ET, bottom 17332.25 and top 17909.75. It passed the source-triple reconciliation; no size cap is applied. This confirms agreement with the input, not independent exchange-tick verification.

No output FVG uses an incomplete bar, bridges a missing interval, duplicates an ID, or violates its direction inequality. All embedded candles, zone bounds, dates and session rules match the independent oracle. The four incomplete input bars remain in the source and cannot participate. No new data-quality failures were found.

| Year | FVGs |
|---|---:|
| 2024 | 3,793 |
| 2025 | 3,779 |
| 2026 | 3,036 |

| Month | FVGs |
|---|---:|
| 2024-01 | 340 |
| 2024-02 | 344 |
| 2024-03 | 294 |
| 2024-04 | 323 |
| 2024-05 | 332 |
| 2024-06 | 276 |
| 2024-07 | 353 |
| 2024-08 | 338 |
| 2024-09 | 286 |
| 2024-10 | 320 |
| 2024-11 | 307 |
| 2024-12 | 280 |
| 2025-01 | 304 |
| 2025-02 | 300 |
| 2025-03 | 324 |
| 2025-04 | 346 |
| 2025-05 | 326 |
| 2025-06 | 286 |
| 2025-07 | 313 |
| 2025-08 | 311 |
| 2025-09 | 300 |
| 2025-10 | 343 |
| 2025-11 | 288 |
| 2025-12 | 338 |
| 2026-01 | 346 |
| 2026-02 | 300 |
| 2026-03 | 322 |
| 2026-04 | 346 |
| 2026-05 | 353 |
| 2026-06 | 340 |
| 2026-07 | 360 |
| 2026-08 | 295 |
| 2026-09 | 330 |
| 2026-10 | 44 |

2026 is partial, through the exclusive 2026-10-06 source endpoint.

Opening-exception sample totals: January 2024 **11**, February **7**, March **8**; every one of those 26 records is printed and saved in the opening-exception table.

Unchanged source SHA-256: `badd703b65d89953e0b209ed07218960d94b10423579e9a512b17f8eedbf592c`.
