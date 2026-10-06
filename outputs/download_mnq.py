#!/usr/bin/env python3
"""Download unadjusted MNQ continuous bars. No timestamp shifting or backtesting."""
import argparse
import fcntl
import json
import logging
import os
from pathlib import Path
import sys
import warnings

import databento as db
from dotenv import dotenv_values
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'outputs' / 'data'
NAME = 'GLBX.MDP3_MNQ.v.0_ohlcv-1m_2024-01-01_2026-10-06'
REQUEST = dict(dataset='GLBX.MDP3', symbols=['MNQ.v.0'], stype_in='continuous',
               schema='ohlcv-1m', start='2024-01-01', end='2026-10-06')
UNDEF_PRICE = 2**63 - 1


def inspect_file(path):
    table = pq.read_table(path)
    frame = table.to_pandas()
    if 'ts_event' in frame:
        ts = pd.DatetimeIndex(frame['ts_event'])
    elif frame.index.name == 'ts_event':
        ts = pd.DatetimeIndex(frame.index)
    else:
        raise ValueError('Missing ts_event')
    if str(ts.tz) != 'UTC' or ts.dtype.unit != 'ns':
        raise ValueError('Expected nanosecond UTC timestamps')
    prices = frame[['open', 'high', 'low', 'close']]
    # Integer prices preserve original Databento fixed-point values (1e-9 USD).
    if not all(pd.api.types.is_integer_dtype(dtype) for dtype in prices.dtypes):
        raise ValueError('Expected raw integer prices')
    missing = prices.isna() | prices.eq(UNDEF_PRICE)
    invalid = ~np.isfinite(prices) | missing
    inconsistent = ((prices['high'] < prices['low']) |
                    (prices['open'] > prices['high']) | (prices['open'] < prices['low']) |
                    (prices['close'] > prices['high']) | (prices['close'] < prices['low']))
    outside = (ts < pd.Timestamp(REQUEST['start'], tz='UTC')) | (ts >= pd.Timestamp(REQUEST['end'], tz='UTC'))
    report = dict(rows=len(frame), first_timestamp=str(ts.min()) if len(ts) else None,
                  last_timestamp=str(ts.max()) if len(ts) else None,
                  file_size_bytes=path.stat().st_size, output_path=str(path.resolve()),
                  duplicate_timestamp_rows=int(ts.duplicated(keep=False).sum()),
                  duplicate_timestamp_excess=int(ts.duplicated().sum()),
                  missing_ohlc_values={c: int(missing[c].sum()) for c in prices},
                  invalid_ohlc_rows=int((invalid.any(axis=1) | inconsistent).sum()),
                  missing_timestamps=int(ts.isna().sum()),
                  timestamps_outside_request=int(outside.sum()),
                  timestamps_monotonic=bool(ts.is_monotonic_increasing),
                  price_encoding='int64; divide by 1,000,000,000 for USD',
                  timestamp_encoding='timestamp[ns, UTC]')
    report['quality_passed'] = bool(len(frame) and not any([
        report['duplicate_timestamp_rows'], report['invalid_ohlc_rows'],
        report['missing_timestamps'], report['timestamps_outside_request'],
        not report['timestamps_monotonic']]))
    return report


def run(env_file, overwrite=False):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = DATA_DIR / (NAME + '.parquet')
    # Exclusive lock protects against concurrent billable requests.
    with (DATA_DIR / (NAME + '.lock')).open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another downloader is active') from None
        if target.exists() and not overwrite:
            print('Existing file found; no download requested.')
            report = inspect_file(target)
        else:
            cached = DATA_DIR / (NAME + '.complete.dbn.zst')
            partial = DATA_DIR / (NAME + '.partial.dbn.zst')
            staging = DATA_DIR / (NAME + '.partial.parquet')
            if overwrite or not cached.exists():
                if not env_file.is_file():
                    raise FileNotFoundError('Local .env file is missing')
                key = dotenv_values(env_file, interpolate=False).get('DATABENTO_API_KEY')
                if not key or not key.strip() or key.strip() == 'your_key':
                    raise ValueError('DATABENTO_API_KEY is missing from local .env')
                partial.unlink(missing_ok=True)
                # Never emit SDK logs, warnings, exception messages or credentials.
                logging.disable(logging.CRITICAL)
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    client = db.Historical(key.strip())
                    del key
                    client.timeseries.get_range(**REQUEST, path=partial)
                os.replace(partial, cached)
            else:
                print('Reusing completed local DBN download; no network request.')
            staging.unlink(missing_ok=True)
            db.DBNStore.from_bytes(cached.read_bytes()).to_parquet(staging, price_type='fixed', pretty_ts=True,
                                         map_symbols=False, mode='x', compression='zstd')
            report = inspect_file(staging)
            # Verify timestamps/encoding before atomically publishing the result.
            os.replace(staging, target)
            report['output_path'] = str(target.resolve())
            cached.unlink()
        print(json.dumps(report, indent=2))
        return 0 if report['quality_passed'] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env')
    parser.add_argument('--overwrite', action='store_true', help='Explicitly authorize a new billable download')
    args = parser.parse_args()
    try:
        return run(args.env_file.expanduser().resolve(), args.overwrite)
    except Exception as exc:
        # Exception text can include request headers; deliberately never print it.
        print(f'Download/validation failed ({type(exc).__name__}). No credentials logged. '
              'Check the local .env, network, account access and output files.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
