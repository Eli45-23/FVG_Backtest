# Deterministic MNQ 5-minute data layer

## Run and test

From the workspace root, using the existing pinned dependencies in `outputs/requirements.txt`:

```sh
work/.venv/bin/python outputs/build_5m.py
work/.venv/bin/python -m unittest discover -s outputs/tests -v
```

The builder requires no API key, makes no network calls and does not download anything. It reads the existing raw Parquet and atomically replaces only the derived Parquet. Re-running is deterministic under the pinned runtime. Source data is verified by SHA-256 before/after construction; output Parquet is read back and compared before publication. Input/output cannot be the same path.

## Timestamp authority and interpretation

[Databento's OHLCV schema documentation](https://databento.com/docs/schemas-and-data-formats/ohlcv), checked 2026-10-06, states that `ts_event` marks the start of each interval, with an inclusive start based on trade `ts_recv`. The convention is provider-documented, not inferred from observed timestamps. No-trade intervals do not produce records.

For example, source 09:25 is the minute [09:25, 09:26). Output 09:25 is the five-minute interval [09:25, 09:30), containing minutes 09:25, 09:26, 09:27, 09:28 and 09:29. This candle is not complete until 09:30. A candle labeled 09:35 completes at 09:40. Consumers must respect these availability times.

Buckets are formed by flooring UTC timestamps to 5-minute clock boundaries. Their New York representation is also aligned to :00, :05, :10, etc. Both timestamps remain timezone-aware and retain nanosecond resolution. `timestamp_ny` uses the IANA America/New_York zone and handles daylight saving time. No fixed UTC offset or manual timestamp shift is applied. Repeated fall-back wall-clock times are distinct UTC instants.

## Aggregation and schema

Source minute timestamps must be unique, non-null, UTC and minute-aligned. Invalid OHLC, undefined prices, noninteger prices/volumes, negative volume and wrong record types cause an explicit failure. Rows are stably sorted in memory. The raw file is never changed.

Integer source prices are aggregated first: first open, maximum high, minimum low, final close. Conversion divides the fixed-point integer by 1e9 using exact Decimal arithmetic; Parquet stores `decimal128(20,9)`, not integer ticks or rounded binary floating point. Volume remains an unsigned integer sum. There is no price back-adjustment across continuous-contract rolls.

Output columns:

| Column | Meaning |
|---|---|
| timestamp_utc | Five-minute bucket start, timestamp[ns, UTC] |
| timestamp_ny | Same instant, timestamp[ns, America/New_York] |
| open, high, low, close | Exact decimal price values |
| volume | Total source contract volume, uint64 |
| ny_date | New York **calendar date**, date32 |
| ny_time | Convenience HH:MM:SS wall-clock string; use timestamp_ny for timezone/offset |
| is_rth | 09:30 <= New York bucket start < 16:00 |
| is_premarket | New York bucket start < 09:30 |
| is_postmarket | New York bucket start >= 16:00 |
| minute_count | Number of distinct observed source minute records, 1–5 |
| is_complete_5m | minute_count == 5 |
| instrument_count | Number of distinct underlying instrument IDs in the bucket |
| is_mixed_contract | More than one underlying contract in a bucket |

Session flags are exhaustive clock-time labels on each New York calendar date, including weekends and holidays. They are **not** an exchange holiday/early-close calendar and do not assign a futures trading date. Every available source minute is retained in exactly one bucket.

No missing minutes or empty five-minute buckets are synthesized. Partially populated buckets retain observed first/last prices and are flagged incomplete. Entirely absent buckets are omitted; therefore the incomplete count is not a count of all wall-clock intervals without trading. The layer cannot determine whether an absent minute reflects no trades, a halt or a data gap from OHLCV alone.

## Local deliverables and evidence

All market-data outputs remain under ignored `outputs/data/`:

- `MNQ_5m_2024-01-01_2026-10-06.parquet`
- `MNQ_5m_sample.csv`: 828 bars across New York calendar dates February 5–7, 2024, each with 78 observed RTH bars; CSV timestamps include numeric UTC offsets. Parquet retains the named timezone.
- `MNQ_5m_validation.json`: full counts, source fingerprint and incomplete-bucket evidence.
- `MNQ_5m_spot_checks.txt`: all 27 bars from 09:20 through 10:00 ET on those three dates, including OHLCV and completeness.

The raw input is `GLBX.MDP3_MNQ.v.0_ohlcv-1m_2024-01-01_2026-10-06.parquet` in the same directory.

## Validation results

| Check | Result |
|---|---:|
| Source minutes | 977,725 |
| Five-minute bars | 195,546 |
| Complete | 195,542 |
| Incomplete | 4 |
| Duplicate output timestamps | 0 |
| Invalid OHLC bars | 0 |
| RTH bars | 54,618 |
| Premarket bars | 81,291 |
| Postmarket bars | 59,637 |
| Mixed-contract buckets | 0 |
| Source / output total volume | 1,161,621,763 / 1,161,621,763 |

First bar starts 2024-01-01 23:00:00 UTC; last starts 2026-10-05 23:55:00 UTC. The source request ends exclusively at 2026-10-06 00:00:00 UTC.

Every output bar is independently reconciled to raw minutes using integer epoch buckets and NumPy reductions, separate from the groupby construction. All OHLC inequalities, counts, volumes, timezones and timestamp uniqueness passed. The source fingerprint remained:
`1017843fa2937108fec7938891e46259492d2bf0a158cc35c40047691ce6d8c5`.

The four incomplete buckets are retained. Evidence shows absence in the local raw data; cause is not established:

| New York bucket start | Source minutes | Absent source minute(s), UTC |
|---|---:|---|
| 2024-12-17 23:00 -05:00 | 4 | 2024-12-18 04:04 |
| 2025-04-02 16:30 -04:00 | 4 | 2025-04-02 20:31 |
| 2025-04-02 18:00 -04:00 | 3 | 2025-04-02 22:00, 22:01 |
| 2025-09-16 23:55 -04:00 | 4 | 2025-09-17 03:59 |

These are localized completeness issues (4 of 195,546 observed buckets, about 0.00205%). All are outside the requested RTH mask. No corrective filling is applied; downstream research can use the completeness flag. This does not establish source completeness during entirely empty intervals.

Nineteen synthetic-data tests cover exact conversion, OHLC/volume aggregation, clock alignment, winter/summer conversion, both DST transitions, calendar dates, session boundaries, special 09:25/09:30/09:35 labels, missing minutes/empty buckets, duplicate rejection, invalid inputs, contract-boundary flags, independent reconciliation, raw immutability, Parquet round-trip and deterministic bytes. There is no strategy, signal, entry, stop, target, trade management or performance-statistics implementation.

## Git

Only source code, synthetic tests, dependency pins and documentation are committed locally. `.gitignore` excludes `outputs/data/`, raw Parquet/DBN files, `.env` credentials and scratch/runtime files. The CSV sample and validation outputs are also ignored. There is no configured remote and no GitHub push.
