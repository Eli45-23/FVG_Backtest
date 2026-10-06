#!/usr/bin/env python3
"""Deterministic, start-labeled MNQ bars; no trading logic or data downloads."""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
RAW = HERE / 'data/GLBX.MDP3_MNQ.v.0_ohlcv-1m_2024-01-01_2026-10-06.parquet'
OUTPUT = HERE / 'data/MNQ_5m_2024-01-01_2026-10-06.parquet'
PRICE_COLUMNS = ['open', 'high', 'low', 'close']
SCALE = 1_000_000_000
UNDEF_PRICE = 2**63 - 1
CONVENTION_URL = 'https://databento.com/docs/schemas-and-data-formats/ohlcv'
SPOT_DATES = ['2024-02-05', '2024-02-06', '2024-02-07']


def fixed_to_decimal(value: int) -> Decimal:
    """Exact conversion, independent of the caller's decimal context."""
    with localcontext() as ctx:
        ctx.prec = 38
        return Decimal(int(value)).scaleb(-9)


def invalid_ohlc(frame: pd.DataFrame) -> pd.Series:
    p = frame[PRICE_COLUMNS]
    return (p.isna().any(axis=1) | (p.high < p.open) | (p.high < p.close) |
            (p.low > p.open) | (p.low > p.close) | (p.high < p.low))


def normalize_raw(raw: pd.DataFrame) -> pd.DataFrame:
    """Fail closed on ambiguous/invalid minutes; sorting never changes the raw file."""
    f = raw.copy()
    if 'ts_event' not in f and f.index.name == 'ts_event':
        f = f.reset_index()
    required = ['ts_event', *PRICE_COLUMNS, 'volume', 'instrument_id']
    if not set(required).issubset(f.columns):
        raise ValueError('Missing required source columns')
    if f.empty:
        raise ValueError('Source has no rows')
    ts = f.ts_event
    if not isinstance(ts.dtype, pd.DatetimeTZDtype) or str(ts.dt.tz) != 'UTC':
        raise ValueError('Source ts_event must be timezone-aware UTC')
    f['ts_event'] = ts.dt.as_unit('ns')
    if ts.isna().any() or ts.duplicated().any():
        raise ValueError('Source has null or duplicate minute timestamps')
    if not ts.eq(ts.dt.floor('min')).all():
        raise ValueError('Source timestamps are not on minute boundaries')
    for c in [*PRICE_COLUMNS, 'volume', 'instrument_id']:
        if not pd.api.types.is_integer_dtype(f[c].dtype) or f[c].isna().any():
            raise ValueError(f'Source {c} must be non-null integers')
    if f[PRICE_COLUMNS].eq(UNDEF_PRICE).any().any() or invalid_ohlc(f).any():
        raise ValueError('Source has undefined or invalid OHLC')
    if f.volume.lt(0).any() or sum(map(int, f.volume)) > np.iinfo(np.uint64).max:
        raise ValueError('Negative volume or volume overflow risk')
    if 'rtype' in f and not f.rtype.eq(33).all():
        raise ValueError('Expected only OHLCV-1m records (rtype=33)')
    return f.sort_values('ts_event', kind='stable').reset_index(drop=True)


def build_bars(raw: pd.DataFrame) -> pd.DataFrame:
    f = normalize_raw(raw)
    # UTC floor defines [start, start+5m); groupby emits only observed buckets.
    # New York's offsets are whole hours, so these are also local :00/:05/... starts.
    f['timestamp_utc'] = f.ts_event.dt.floor('5min')
    b = f.groupby('timestamp_utc', sort=True).agg(
        open=('open', 'first'), high=('high', 'max'), low=('low', 'min'),
        close=('close', 'last'), volume=('volume', 'sum'),
        minute_count=('ts_event', 'size'), instrument_count=('instrument_id', 'nunique'),
    ).reset_index()
    for c in PRICE_COLUMNS:
        b[c] = b[c].map(fixed_to_decimal)
    b['volume'] = b.volume.astype('uint64')
    b['timestamp_ny'] = b.timestamp_utc.dt.tz_convert('America/New_York')
    b['ny_date'] = b.timestamp_ny.dt.date
    # Convenience wall-clock label only; timestamp_ny retains timezone + DST fold.
    b['ny_time'] = b.timestamp_ny.dt.strftime('%H:%M:%S')
    minute = b.timestamp_ny.dt.hour * 60 + b.timestamp_ny.dt.minute
    b['is_rth'] = (minute >= 570) & (minute < 960)
    b['is_premarket'] = minute < 570
    b['is_postmarket'] = minute >= 960
    b['is_complete_5m'] = b.minute_count.eq(5)
    b['is_mixed_contract'] = b.instrument_count.gt(1)
    return b[['timestamp_utc', 'timestamp_ny', *PRICE_COLUMNS, 'volume',
              'ny_date', 'ny_time', 'is_rth', 'is_premarket', 'is_postmarket',
              'minute_count', 'is_complete_5m', 'instrument_count', 'is_mixed_contract']]


def validate_all(raw: pd.DataFrame, bars: pd.DataFrame) -> dict:
    """Independently reconcile EVERY bar using integer epoch buckets / numpy reductions."""
    f = normalize_raw(raw)
    key = f.ts_event.array.as_unit('ns').asi8 // (300 * 1_000_000_000)
    starts = np.r_[0, np.flatnonzero(np.diff(key)) + 1]
    ends = np.r_[starts[1:], len(f)]
    expected_ts = pd.to_datetime(key[starts] * 300 * 1_000_000_000, utc=True)
    if list(bars.timestamp_utc) != list(expected_ts):
        raise ValueError('Output bucket keys do not match source')
    expected = {
        'open': f.open.to_numpy()[starts],
        'high': np.maximum.reduceat(f.high.to_numpy(), starts),
        'low': np.minimum.reduceat(f.low.to_numpy(), starts),
        'close': f.close.to_numpy()[ends - 1],
    }
    for c, values in expected.items():
        if list(bars[c]) != [fixed_to_decimal(v) for v in values]:
            raise ValueError(f'Full source reconciliation failed for {c}')
    volumes = np.add.reduceat(f.volume.to_numpy(dtype=np.uint64), starts)
    if not np.array_equal(bars.volume, volumes):
        raise ValueError('Volume reconciliation failed')
    if not np.array_equal(bars.minute_count, ends - starts):
        raise ValueError('Minute counts do not match source')
    if not bars.minute_count.between(1, 5).all():
        raise ValueError('Invalid minute count')
    if not bars.is_complete_5m.eq(bars.minute_count.eq(5)).all():
        raise ValueError('Completeness flags do not match counts')
    if not bars.timestamp_utc.eq(bars.timestamp_ny.dt.tz_convert('UTC')).all():
        raise ValueError('Timezone conversion changed an instant')
    if not bars[['is_rth', 'is_premarket', 'is_postmarket']].sum(axis=1).eq(1).all():
        raise ValueError('Session flags are not mutually exclusive and exhaustive')
    duplicates = int(bars.timestamp_utc.duplicated().sum())
    bad = int(invalid_ohlc(bars).sum())
    if duplicates or bad:
        raise ValueError('Duplicate timestamps or invalid output OHLC')
    return {
        'total_1m_rows_read': len(f), 'total_5m_bars': len(bars),
        'first_5m_timestamp_utc': bars.timestamp_utc.iloc[0].isoformat(),
        'last_5m_timestamp_utc': bars.timestamp_utc.iloc[-1].isoformat(),
        'complete_5m_bars': int(bars.is_complete_5m.sum()),
        'incomplete_5m_bars': int((~bars.is_complete_5m).sum()),
        'duplicate_5m_timestamps': duplicates, 'invalid_ohlc_bars': bad,
        'rth_bar_count': int(bars.is_rth.sum()),
        'premarket_bar_count': int(bars.is_premarket.sum()),
        'postmarket_bar_count': int(bars.is_postmarket.sum()),
        'minute_count_distribution': {str(k): int(v) for k, v in bars.minute_count.value_counts().sort_index().items()},
        'missing_minutes_inside_observed_buckets': int((5 - bars.minute_count).sum()),
        'mixed_contract_buckets': int(bars.is_mixed_contract.sum()),
        'source_volume': sum(map(int, f.volume)),
        'output_volume': sum(map(int, bars.volume)),
        'all_bars_reconciled_to_source': True,
    }


def write_parquet(bars: pd.DataFrame, path: Path, source_hash: str):
    schema = pa.schema([
        ('timestamp_utc', pa.timestamp('ns', tz='UTC')),
        ('timestamp_ny', pa.timestamp('ns', tz='America/New_York')),
        *[(c, pa.decimal128(20, 9)) for c in PRICE_COLUMNS],
        ('volume', pa.uint64()), ('ny_date', pa.date32()), ('ny_time', pa.string()),
        ('is_rth', pa.bool_()), ('is_premarket', pa.bool_()), ('is_postmarket', pa.bool_()),
        ('minute_count', pa.int64()), ('is_complete_5m', pa.bool_()),
        ('instrument_count', pa.int64()), ('is_mixed_contract', pa.bool_()),
    ], metadata={
        b'timestamp_convention': b'Bar start; inclusive left, exclusive right; UTC clock-aligned 5 minutes',
        b'convention_source': CONVENTION_URL.encode(),
        b'source_sha256': source_hash.encode(),
        b'price_encoding': b'Exact decimal128(20,9), source int64 divided by 1e9',
        b'session_labels': b'New York calendar date; time-only masks, not exchange holiday schedule',
        b'missing_minutes': b'No fill; only observed buckets; complete iff 5 distinct source minutes',
    })
    table = pa.Table.from_pandas(bars, schema=schema, preserve_index=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(suffix='.parquet', dir=path.parent)
    os.close(fd)
    try:
        pq.write_table(table, temp, compression='zstd')
        restored = pq.read_table(temp)
        if not table.equals(restored):
            raise ValueError('Parquet round-trip mismatch')
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def sha256(path: Path) -> str:
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=RAW)
    p.add_argument('--output', type=Path, default=OUTPUT)
    args = p.parse_args()
    source, target = args.input.resolve(), args.output.resolve()
    if source == target:
        p.error('Output must differ from raw input')
    before = sha256(source)
    raw = pq.read_table(source).to_pandas()
    bars = build_bars(raw)
    report = validate_all(raw, bars)
    after = sha256(source)
    if before != after:
        raise RuntimeError('Raw file changed during build')
    write_parquet(bars, target, before)
    report.update(source_path=str(source), output_path=str(target), raw_sha256=before,
                  raw_file_unchanged=True, timestamp_convention='Bar start, [t,t+5min)',
                  convention_source=CONVENTION_URL)
    sample = bars[bars.ny_date.astype(str).isin(SPOT_DATES)]
    sample.to_csv(target.parent / 'MNQ_5m_sample.csv', index=False)
    spots = sample[sample.ny_time.between('09:20:00', '10:00:00')]
    required = {(d, t) for d in SPOT_DATES for t in ['09:25:00', '09:30:00', '09:35:00']}
    actual = set(zip(spots.ny_date.astype(str), spots.ny_time))
    if not required.issubset(actual):
        raise ValueError('Required morning spot-check bars are missing')
    source_minutes = pd.DatetimeIndex(normalize_raw(raw).ts_event)
    report['incomplete_buckets'] = [
        {'timestamp_utc': row.timestamp_utc.isoformat(),
         'timestamp_ny': row.timestamp_ny.isoformat(),
         'minute_count': int(row.minute_count),
         'absent_source_minutes_utc': [t.isoformat() for t in
             pd.date_range(row.timestamp_utc, periods=5, freq='min').difference(
                 source_minutes)]}
        for row in bars.loc[~bars.is_complete_5m].itertuples()
    ]
    report['spot_check_dates'] = SPOT_DATES
    report['spot_check_required_bars_present'] = True
    report['sample_rows'] = len(sample)
    report_path = target.parent / 'MNQ_5m_validation.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    columns = ['timestamp_ny', *PRICE_COLUMNS, 'volume', 'minute_count', 'is_complete_5m']
    spot_text = spots[columns].to_string(index=False)
    (target.parent / 'MNQ_5m_spot_checks.txt').write_text(spot_text + '\n')
    print('\n09:20 through 10:00 America/New_York (bar-start labels):\n' + spot_text)


if __name__ == '__main__':
    main()
