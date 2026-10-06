# MNQ historical downloader

Run from the workspace root:

```sh
python3 -m venv work/.venv
work/.venv/bin/python -m pip install -r outputs/requirements.txt
work/.venv/bin/python outputs/download_mnq.py --env-file /Users/DayTrade/.env
```

The configured local key file for this workspace is `/Users/DayTrade/.env`; the command above selects it explicitly. Alternatively, create `.env` in the workspace root containing `DATABENTO_API_KEY=your_key`.
Never commit it. An alternate local file can be specified with `--env-file /absolute/path/.env`.

Request: GLBX.MDP3, MNQ.v.0, continuous symbology, ohlcv-1m, 2024-01-01 00:00 UTC inclusive to 2026-10-06 00:00 UTC exclusive.
Downloading incurs Databento charges. The earlier estimate was $3.569463267922.

Output is under `outputs/data/`. Existing Parquet files are inspected without downloading again. Only `--overwrite` authorizes a fresh download. Concurrent runs are locked out. A completed temporary DBN file is reused if Parquet conversion fails; incomplete DBN files are never reused. The existing Parquet remains intact until its replacement is ready.

Parquet preserves original records and unshifted `ts_event` values as nanosecond UTC timestamps. OHLC prices are exact Databento fixed-point integers: divide by 1,000,000,000 for dollar prices. No adjustment, resampling, sorting, deduplication, filling or backtesting is performed. Native instrument IDs and other source fields are retained; symbol mapping is not added.

The script prints row count, minimum/maximum timestamp, byte size, absolute path and quality checks. Duplicate counts include both all participating rows and excess rows. Invalid OHLC includes null/undefined/nonfinite prices and inconsistent high/low/open/close relationships. Negative prices are not automatically considered invalid. Quality failures retain the raw file and return exit code 2; operational failures return 1; success returns 0. Missing time intervals are not filled or classified as invalid (market closures/no trades can produce gaps).

`.gitignore` excludes data, credentials and scratch files. Git ignores do not untrack files previously committed elsewhere.

## Five-minute construction

The deterministic data-only layer is documented in [BAR_LAYER.md](BAR_LAYER.md).
Run `work/.venv/bin/python outputs/build_5m.py` to build and validate local five-minute bars; no API key or network access is required. Run the synthetic tests with `work/.venv/bin/python -m unittest discover -s outputs/tests -v`.
