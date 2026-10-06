#!/usr/bin/env python3
"""Deterministic MNQ 5-minute FVG formation only; no trade or zone lifecycle logic."""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import os
from pathlib import Path
import tempfile

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
INPUT = HERE / 'data/MNQ_5m_2024-01-01_2026-10-06.parquet'
OUTPUT = HERE / 'data/MNQ_FVGs_2024-01-01_2026-10-06.parquet'
OHLC = ['open', 'high', 'low', 'close']
FIVE = pd.Timedelta(minutes=5)
SAMPLE_MONTHS = ['2024-01', '2024-02', '2024-03']
ID_VERSION = 'mnq-5m-fvg-v1'
SCHEMA = pa.schema([
    ('fvg_id', pa.string()), ('direction', pa.string()),
    ('formation_bar_start_utc', pa.timestamp('ns', tz='UTC')),
    ('formation_bar_start_ny', pa.timestamp('ns', tz='America/New_York')),
    ('formation_date_ny', pa.date32()),
    *[(f'candle{i}_start_utc', pa.timestamp('ns', tz='UTC')) for i in range(1, 4)],
    ('bottom', pa.decimal128(20, 9)), ('top', pa.decimal128(20, 9)),
    ('size_points', pa.decimal128(21, 9)), ('opening_exception', pa.bool_()),
    *[(f'candle{i}_{c}', pa.decimal128(20, 9)) for i in range(1, 4) for c in OHLC],
])
COLUMNS = SCHEMA.names


def stable_id(direction, starts):
    """Identity depends on definition version, symbol, direction, and UTC instants."""
    payload = '|'.join([ID_VERSION, 'MNQ.v.0', direction, *[str(pd.Timestamp(t).value) for t in starts]])
    return hashlib.sha256(payload.encode('ascii')).hexdigest()


def difference(top, bottom):
    with localcontext() as ctx:
        ctx.prec = 38
        return top - bottom


def prepare(bars):
    b = bars.copy(deep=True)
    required = {'timestamp_utc', 'timestamp_ny', 'is_complete_5m', *OHLC}
    if not required.issubset(b.columns):
        raise ValueError('Missing required five-minute columns')
    for col, zone in [('timestamp_utc', 'UTC'), ('timestamp_ny', 'America/New_York')]:
        if not isinstance(b[col].dtype, pd.DatetimeTZDtype) or str(b[col].dt.tz) != zone:
            raise ValueError(f'{col} must be timezone-aware {zone}')
        if b[col].isna().any():
            raise ValueError('Null source timestamp')
        b[col] = b[col].dt.as_unit('ns')
    if b.timestamp_utc.duplicated().any():
        raise ValueError('Duplicate source timestamps')
    if not b.timestamp_utc.eq(b.timestamp_utc.dt.floor('5min')).all():
        raise ValueError('Source timestamps must be on five-minute boundaries')
    if not b.timestamp_ny.dt.tz_convert('UTC').eq(b.timestamp_utc).all():
        raise ValueError('Source New York/UTC timestamps disagree')
    if not pd.api.types.is_bool_dtype(b.is_complete_5m) or b.is_complete_5m.isna().any():
        raise ValueError('Completeness must be non-null boolean')
    if 'minute_count' in b:
        if b.minute_count.isna().any() or not b.minute_count.between(1, 5).all():
            raise ValueError('Invalid source minute count')
        if not b.is_complete_5m.eq(b.minute_count.eq(5)).all():
            raise ValueError('Source minute count contradicts completeness')
    for c in OHLC:
        if not b[c].map(lambda v: isinstance(v, Decimal) and v.is_finite()).all():
            raise ValueError('OHLC must contain finite exact Decimal values')
    if ((b.high < b.open) | (b.high < b.close) | (b.low > b.open) |
            (b.low > b.close) | (b.high < b.low)).any():
        raise ValueError('Invalid source OHLC relationships')
    return b.sort_values('timestamp_utc', kind='stable').reset_index(drop=True)


def detect(bars):
    b = prepare(bars)
    # Never drop incomplete or premarket rows before constructing candidate triples.
    one, two = b.shift(2), b.shift(1)
    consecutive = (b.timestamp_utc - two.timestamp_utc).eq(FIVE) & (two.timestamp_utc - one.timestamp_utc).eq(FIVE)
    complete = b.is_complete_5m & two.is_complete_5m.eq(True) & one.is_complete_5m.eq(True)
    ny = b.timestamp_utc.dt.tz_convert('America/New_York')
    clock = ny.dt.hour * 60 + ny.dt.minute
    rth = clock.ge(570) & clock.lt(960)
    same_date = ny.dt.date.eq(ny.shift(1).dt.date) & ny.dt.date.eq(ny.shift(2).dt.date)
    normal = rth & rth.shift(1, fill_value=False) & rth.shift(2, fill_value=False)
    opening = clock.eq(575) & clock.shift(1).eq(570) & clock.shift(2).eq(565) & same_date
    eligible = consecutive & complete & same_date & (normal | opening)
    bullish = pd.Series(False, index=b.index)
    bearish = pd.Series(False, index=b.index)
    bullish.loc[eligible] = b.loc[eligible, 'low'].gt(one.loc[eligible, 'high'])
    bearish.loc[eligible] = b.loc[eligible, 'high'].lt(one.loc[eligible, 'low'])
    records = []
    for idx in b.index[bullish | bearish]:
        direction = 'bullish' if bullish.loc[idx] else 'bearish'
        candles = [b.iloc[idx - 2], b.iloc[idx - 1], b.iloc[idx]]
        c1, _, c3 = candles
        bottom, top = (c1.high, c3.low) if direction == 'bullish' else (c3.high, c1.low)
        starts = [c.timestamp_utc for c in candles]
        record = dict(fvg_id=stable_id(direction, starts), direction=direction,
                      formation_bar_start_utc=starts[2], formation_bar_start_ny=ny.iloc[idx],
                      formation_date_ny=ny.iloc[idx].date(),
                      bottom=bottom, top=top, size_points=difference(top, bottom),
                      opening_exception=bool(opening.iloc[idx]))
        for i, c in enumerate(candles, 1):
            record[f'candle{i}_start_utc'] = c.timestamp_utc
            record.update({f'candle{i}_{p}': c[p] for p in OHLC})
        records.append(record)
    # Explicit schema preserves an identical contract even for zero detected gaps.
    return pa.Table.from_pylist(records, schema=SCHEMA).to_pandas()


def validate(bars, fvgs):
    """Independent sequential oracle: check all source triples, including non-events."""
    source = prepare(bars)
    rows = list(source.itertuples(index=False))
    expected = []
    for idx in range(2, len(rows)):
        a, b, c = rows[idx-2:idx+1]
        if not (a.is_complete_5m and b.is_complete_5m and c.is_complete_5m):
            continue
        if b.timestamp_utc - a.timestamp_utc != FIVE or c.timestamp_utc - b.timestamp_utc != FIVE:
            continue
        local = [x.timestamp_utc.tz_convert('America/New_York') for x in (a, b, c)]
        dates = [t.date() for t in local]
        times = [(t.hour, t.minute) for t in local]
        if len(set(dates)) != 1:
            continue
        opening = times == [(9, 25), (9, 30), (9, 35)]
        normal = all((9, 30) <= t < (16, 0) for t in times)
        if not normal and not opening:
            continue
        if c.low > a.high:
            direction, bottom, top = 'bullish', a.high, c.low
        elif c.high < a.low:
            direction, bottom, top = 'bearish', c.high, a.low
        else:
            continue
        starts = [x.timestamp_utc for x in (a, b, c)]
        record = {'fvg_id': stable_id(direction, starts), 'direction': direction,
                  'formation_bar_start_utc': c.timestamp_utc, 'formation_bar_start_ny': local[2],
                  'formation_date_ny': dates[2], 'bottom': bottom, 'top': top,
                  'size_points': difference(top, bottom), 'opening_exception': opening}
        for i, candle in enumerate((a, b, c), 1):
            record[f'candle{i}_start_utc'] = candle.timestamp_utc
            record.update({f'candle{i}_{p}': getattr(candle, p) for p in OHLC})
        expected.append(record)
    if len(fvgs) != len(expected):
        raise ValueError('Oracle and detector FVG counts disagree')
    if fvgs.fvg_id.duplicated().any():
        raise ValueError('Duplicate FVG IDs')
    for actual, reference in zip(fvgs.to_dict('records'), expected):
        if any(actual[k] != reference[k] for k in COLUMNS):
            raise ValueError('FVG record does not match independent source oracle')
    return {'independent_oracle_matches_all_records': True,
            'no_incomplete_bar_participation': True, 'no_missing_interval_bridged': True,
            'no_duplicate_fvg_ids': True, 'all_bullish_inequalities_valid': True,
            'all_bearish_inequalities_valid': True, 'all_session_rules_valid': True,
            'all_zones_and_embedded_candles_match_source': True}


def decimal_stat(values, kind):
    if not values:
        return None
    with localcontext() as ctx:
        ctx.prec = 38
        ctx.rounding = ROUND_HALF_EVEN
        if kind == 'average':
            value = sum(values, Decimal(0)) / len(values)
        else:
            values = sorted(values)
            mid = len(values) // 2
            value = values[mid] if len(values) % 2 else (values[mid-1] + values[mid]) / 2
        return str(value.quantize(Decimal('0.000000001')))


def statistics(bars, fvgs):
    bullish = list(fvgs.loc[fvgs.direction.eq('bullish'), 'size_points'])
    bearish = list(fvgs.loc[fvgs.direction.eq('bearish'), 'size_points'])
    dates = fvgs.formation_date_ny.astype(str)
    local_dates = bars.timestamp_utc.dt.tz_convert('America/New_York').dt.date
    months = pd.period_range(str(local_dates.min())[:7], str(local_dates.max())[:7], freq='M') if len(bars) else []
    by_month = dates.str.slice(0, 7).value_counts()
    return dict(total_bullish_fvgs=len(bullish), total_bearish_fvgs=len(bearish), total_fvgs=len(fvgs),
                total_opening_exception_fvgs=int(fvgs.opening_exception.sum()),
                fvg_count_by_year={str(y): int(dates.str.startswith(str(y)).sum()) for y in sorted(set(t.year for t in local_dates))},
                fvg_count_by_month={str(m): int(by_month.get(str(m), 0)) for m in months},
                average_bullish_size=decimal_stat(bullish, 'average'), average_bearish_size=decimal_stat(bearish, 'average'),
                median_bullish_size=decimal_stat(bullish, 'median'), median_bearish_size=decimal_stat(bearish, 'median'),
                minimum_size=str(min(bullish + bearish)) if len(fvgs) else None,
                maximum_size=str(max(bullish + bearish)) if len(fvgs) else None)


def fingerprint(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write_output(fvgs, target, source_hash):
    table = pa.Table.from_pandas(fvgs, schema=SCHEMA, preserve_index=False)
    metadata = {**(table.schema.metadata or {}), b'source_sha256': source_hash.encode(),
                b'definition': b'Strict 3-candle wick gap; complete consecutive 5m bars; RTH or 09:25/09:30/09:35 NY',
                b'id_version': ID_VERSION.encode(), b'symbol': b'MNQ.v.0',
                b'timestamps': b'Bar starts. Formation is observable only at candle3 start plus 5 minutes.'}
    table = table.replace_schema_metadata(metadata)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=target.parent, suffix='.parquet')
    os.close(fd)
    try:
        pq.write_table(table, name, compression='zstd')
        if not table.equals(pq.read_table(name)):
            raise ValueError('Output Parquet round-trip mismatch')
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)


def price_text(value):
    text = format(value, 'f')
    return text.rstrip('0').rstrip('.') if '.' in text else text


def readable(records):
    if records.empty:
        return '(none)'
    display = pd.DataFrame({'formation_bar_start_ET': records.formation_bar_start_ny,
                            'direction': records.direction})
    for i in range(1, 4):
        display[f'C{i} OHLC (O/H/L/C)'] = records.apply(
            lambda r: '/'.join(price_text(r[f'candle{i}_{c}']) for c in OHLC), axis=1)
    for c in ['bottom', 'top', 'size_points', 'opening_exception']:
        display[c] = records[c]
    return display.to_string(index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    source, target = args.input.resolve(), args.output.resolve()
    if source == target:
        parser.error('Input and output must differ')
    before = fingerprint(source)
    bars = pq.read_table(source).to_pandas()
    fvgs = detect(bars)
    checks = validate(bars, fvgs)
    if fingerprint(source) != before:
        raise RuntimeError('Input changed during detection')
    write_output(fvgs, target, before)
    report = {**statistics(bars, fvgs), 'validation': checks, 'source_sha256': before,
              'source_unchanged': True, 'source_bars': len(bars),
              'source_path': str(source), 'output_path': str(target)}
    sample = pd.concat([fvgs[fvgs.direction.eq(d)].head(5) for d in ['bullish', 'bearish']], ignore_index=True)
    sample.to_csv(target.parent / 'MNQ_FVGs_sample.csv', index=False)
    spot_text = readable(sample)
    (target.parent / 'MNQ_FVGs_spot_checks.txt').write_text(spot_text + '\n')
    openings = []
    report['opening_exception_sample_months'] = {}
    for month in SAMPLE_MONTHS:
        selected = fvgs[fvgs.opening_exception & fvgs.formation_date_ny.astype(str).str.startswith(month)]
        report['opening_exception_sample_months'][month] = len(selected)
        openings.append(f'{month}: EVERY opening-exception FVG ({len(selected)})\n' + readable(selected))
    opening_text = '\n\n'.join(openings)
    (target.parent / 'MNQ_FVGs_opening_exceptions_sample_months.txt').write_text(opening_text + '\n')
    (target.parent / 'MNQ_FVGs_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    print('\nManual spot checks (five bullish, five bearish):\n' + spot_text)
    print('\n' + opening_text)


if __name__ == '__main__':
    main()
