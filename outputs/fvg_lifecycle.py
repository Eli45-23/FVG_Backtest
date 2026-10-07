#!/usr/bin/env python3
"""Same-NY-date FVG observations and descriptive research; no trade simulation."""
from __future__ import annotations
import argparse
from datetime import timedelta
from decimal import Decimal, localcontext
import json
import os
from pathlib import Path
import tempfile

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import detect_fvgs as detection
from lifecycle_stats import summary

HERE=Path(__file__).resolve().parent
BARS=HERE/'data/MNQ_5m_2024-01-01_2026-10-06.parquet'
FVGS=HERE/'data/MNQ_FVGs_2024-01-01_2026-10-06.parquet'
OUTPUT=HERE/'data/MNQ_FVG_LIFECYCLE_2024-01-01_2026-10-06.parquet'
FIVE=pd.Timedelta(minutes=5)
ZERO=Decimal(0)
KINDS=['no_new_extreme','opposite_close']


def delta(a,b):
    with localcontext() as ctx:
        ctx.prec=38
        return a-b


def overlaps(bar, f):
    return bar.low<=f['top'] and bar.high>=f['bottom']


def mfe(rows, after, reference, bullish):
    # Trigger candle's high/low may precede its close: always exclude it.
    future=[b for b in rows if b.timestamp_utc>after]
    if not future:
        return None
    return max(ZERO,delta(max(b.high for b in future),reference) if bullish
               else delta(reference,min(b.low for b in future)))


def candle_fields(prefix, bar, f, previous):
    fields={f'{prefix}_bar_start_utc':None,f'{prefix}_bar_start_ny':None,
            **{f'{prefix}_bar_{c}':None for c in detection.OHLC},
            f'{prefix}_bar_direction':None,
            **{f'{prefix}_{name}':None for name in [
                'is_bullish_candle','is_bearish_candle','is_directional_candle',
                'remained_above_fvg','remained_below_fvg','remained_completely_outside_fvg',
                'remained_favorable_side','touched_fvg','closed_above_reference_high',
                'closed_below_reference_low','closed_beyond_reference_favorable','closed_beyond_reference_adverse']}}
    if bar is None:
        return fields
    bullish=f['direction']=='bullish'
    up=bar.close>bar.open
    down=bar.close<bar.open
    above=bar.low>f['top'];below=bar.high<f['bottom']
    fields.update({f'{prefix}_bar_start_utc':bar.timestamp_utc,
                   f'{prefix}_bar_start_ny':bar.timestamp_utc.tz_convert('America/New_York'),
                   **{f'{prefix}_bar_{c}':getattr(bar,c) for c in detection.OHLC},
                   f'{prefix}_bar_direction':'bullish' if up else 'bearish' if down else 'doji',
                   f'{prefix}_is_bullish_candle':up,f'{prefix}_is_bearish_candle':down,
                   f'{prefix}_is_directional_candle':up if bullish else down,
                   f'{prefix}_remained_above_fvg':above,f'{prefix}_remained_below_fvg':below,
                   f'{prefix}_remained_completely_outside_fvg':above or below,
                   f'{prefix}_remained_favorable_side':above if bullish else below,
                   f'{prefix}_touched_fvg':overlaps(bar,f)})
    if previous is not None:
        ch=bar.close>previous.high;cl=bar.close<previous.low
        fields.update({f'{prefix}_closed_above_reference_high':ch,
                       f'{prefix}_closed_below_reference_low':cl,
                       f'{prefix}_closed_beyond_reference_favorable':ch if bullish else cl,
                       f'{prefix}_closed_beyond_reference_adverse':cl if bullish else ch})
    return fields


def evaluate_one(f, day_rows, coverage_end):
    f=dict(f)
    bullish=f['direction']=='bullish'
    formed=f['formation_bar_start_utc']
    observable=formed+FIVE
    date=f['formation_date_ny']
    midnight=pd.Timestamp(date+timedelta(days=1),tz='America/New_York')
    horizon=min(midnight.tz_convert('UTC'),coverage_end)
    source=[b for b in day_rows if b.timestamp_utc>=observable and b.timestamp_utc+FIVE<=horizon
            and b.timestamp_utc.tz_convert('America/New_York').date()==date]
    rows=[b for b in source if b.is_complete_5m]
    incomplete=sum(not b.is_complete_5m for b in source)
    by_time={b.timestamp_utc:b for b in rows}
    c3=next((b for b in day_rows if b.timestamp_utc==formed),None)
    if c3 is None or not c3.is_complete_5m:
        raise ValueError('Candle 3 missing or incomplete')
    r={**f,'observable_from_utc':observable,'observable_from_ny':observable.tz_convert('America/New_York'),
       'observation_end_utc':horizon,'observation_censored':coverage_end<midnight.tz_convert('UTC'),
       'calendar_expiration_boundary_ny':midnight,'evaluated_complete_bars':len(rows),
       'incomplete_bars_skipped':incomplete,
       'empty_clock_buckets':max(0,int((horizon-observable)//FIVE)-len(source)),
       'research_day_eligible':coverage_end>=midnight.tz_convert('UTC') and incomplete==0}

    def first(predicate):
        return next((b for b in rows if predicate(b)),None)
    touch=first(lambda b:overlaps(b,f))
    fill=first(lambda b:b.low<=f['bottom'] if bullish else b.high>=f['top'])
    close=first(lambda b:b.close<f['bottom'] if bullish else b.close>f['top'])
    wick=first(lambda b:b.low<f['bottom'] if bullish else b.high>f['top'])
    for name,event in [('first_touch',touch),('first_full_fill',fill),('close_invalidation',close),('wick_invalidation',wick)]:
        t=event.timestamp_utc if event is not None else None
        r[f'{name}_time']=t
        r[f'{name}_time_ny']=t.tz_convert('America/New_York') if t is not None else None
        r[f'{name}_confirmed_at_utc']=t+FIVE if t is not None else None
    r.update(touched=touch is not None,untouched=touch is None,fully_filled=fill is not None,
             close_invalidated=close is not None,wick_invalidated=wick is not None,
             first_touch_bar_start_utc=r['first_touch_time'],first_touch_bar_start_ny=r['first_touch_time_ny'],
             bars_until_first_touch=int((touch.timestamp_utc-formed)//FIVE) if touch is not None else None,
             gap_through_without_overlap=bool(fill is not None and not overlaps(fill,f)))
    before=[b for b in rows if touch is None or b.timestamp_utc<touch.timestamp_utc]
    r.update(highest_high_before_touch=max((b.high for b in before),default=None) if bullish else None,
             highest_close_before_touch=max((b.close for b in before),default=None) if bullish else None,
             lowest_low_before_touch=min((b.low for b in before),default=None) if not bullish else None,
             lowest_close_before_touch=min((b.close for b in before),default=None) if not bullish else None,
             bars_untouched=len(before),minutes_untouched=5*len(before),
             elapsed_minutes_until_touch_or_horizon=int(((touch.timestamp_utc if touch is not None else horizon)-observable).total_seconds()/60))
    extreme=r['highest_high_before_touch'] if bullish else r['lowest_low_before_touch']
    r['maximum_points_away_before_touch']=max(ZERO,delta(extreme,f['top']) if bullish else delta(f['bottom'],extreme)) if extreme is not None else ZERO
    for method,event in [('close',close),('wick',wick)]:
        expired=event is None and not r['observation_censored']
        state='invalidated' if event is not None else 'expired_same_day' if expired else 'fully_filled' if fill is not None else 'touched' if touch is not None else 'untouched'
        r.update({f'{method}_terminal_state':state,f'{method}_expired_same_day':expired,
                  f'{method}_expired_untouched':expired and touch is None,
                  f'{method}_expired_after_touch':expired and touch is not None,
                  f'{method}_terminal_time_utc':event.timestamp_utc+FIVE if event is not None else midnight.tz_convert('UTC') if expired else None})
    # Conservative shared alias; method-specific flags are authoritative alternatives.
    r['expired_same_day']=r['close_expired_same_day'] and r['wick_expired_same_day']
    r['expiration_time_ny']=midnight if r['expired_same_day'] else None
    r['expired_untouched']=r['expired_same_day'] and touch is None
    r['expired_after_touch']=r['expired_same_day'] and touch is not None

    nxt=by_time.get(observable);second=by_time.get(observable+FIVE)
    r.update(candle_fields('next',nxt,f,c3))
    r.update(candle_fields('second',second,f,nxt))
    r['second_bar_start']=r['second_bar_start_utc']
    r['first_two_bars_untouched']=bool(nxt is not None and second is not None and not overlaps(nxt,f) and not overlaps(second,f))
    r['second_candle_research_trigger']=r['first_two_bars_untouched'] and bool(r['second_closed_beyond_reference_favorable'])
    r['second_candle_mfe_points']=mfe(rows,second.timestamp_utc,second.close,bullish) if r['second_candle_research_trigger'] else None

    # First comparisons may reference Candle 3, but it never contributes to touch,
    # distance or MFE. Seed pause threshold with C3 solely as the prior reference.
    previous=c3
    running=c3.high if bullish else c3.low
    for kind in KINDS:
        r.update({f'{kind}_pause_time':None,f'{kind}_pause_time_ny':None,
                  f'{kind}_pre_pause_extreme':None,f'{kind}_trigger_time':None,
                  f'{kind}_trigger_time_ny':None,f'{kind}_trigger_close':None,f'{kind}_mfe_points':None})
    for bar in before:
        adjacent=bar.timestamp_utc-previous.timestamp_utc==FIVE
        conditions={
            'no_new_extreme':(bar.high<=previous.high if bullish else bar.low>=previous.low),
            'opposite_close':(bar.close<previous.close if bullish else bar.close>previous.close)}
        for kind in KINDS:
            pause=r[f'{kind}_pause_time']
            # Test an already known pause threshold; never trigger on the pause bar.
            if pause is not None and r[f'{kind}_trigger_time'] is None:
                threshold=r[f'{kind}_pre_pause_extreme']
                if bar.close>threshold if bullish else bar.close<threshold:
                    r[f'{kind}_trigger_time']=bar.timestamp_utc
                    r[f'{kind}_trigger_time_ny']=bar.timestamp_utc.tz_convert('America/New_York')
                    r[f'{kind}_trigger_close']=bar.close
                    r[f'{kind}_mfe_points']=mfe(rows,bar.timestamp_utc,bar.close,bullish)
            if adjacent and conditions[kind] and pause is None:
                r[f'{kind}_pause_time']=bar.timestamp_utc
                r[f'{kind}_pause_time_ny']=bar.timestamp_utc.tz_convert('America/New_York')
                r[f'{kind}_pre_pause_extreme']=running
        running=max(running,bar.high) if bullish else min(running,bar.low)
        previous=bar
    r.update(first_no_new_extreme_time=r['no_new_extreme_pause_time'],
             first_opposite_close_time=r['opposite_close_pause_time'],
             pre_pause_extreme=r['no_new_extreme_pre_pause_extreme'],
             pre_pause_high=r['no_new_extreme_pre_pause_extreme'] if bullish else None,
             pre_pause_low=r['no_new_extreme_pre_pause_extreme'] if not bullish else None)
    return r


def build(bars,fvgs,coverage_end):
    if coverage_end.tzinfo is None or str(coverage_end.tzinfo)!='UTC':
        raise ValueError('Coverage end must be timezone-aware UTC')
    b=detection.prepare(bars)
    if fvgs.fvg_id.duplicated().any():
        raise ValueError('Duplicate input FVG IDs')
    if len(b) and (b.timestamp_utc+FIVE>coverage_end).any():
        raise ValueError('Source bars extend beyond declared coverage')
    groups={date:list(day.itertuples(index=False)) for date,day in b.groupby(b.timestamp_ny.dt.date)}
    records=[]
    for f in fvgs.sort_values(['formation_bar_start_utc','fvg_id']).to_dict('records'):
        records.append(evaluate_one(f,groups.get(f['formation_date_ny'],[]),coverage_end))
    return records


def validate_records(bars,fvgs,records):
    """Independent source joins for event predicates, earliest time, slots and MFE."""
    if len(records)!=len(fvgs) or {r['fvg_id'] for r in records}!=set(fvgs.fvg_id):
        raise ValueError('One record per FVG invariant failed')
    if len({r['fvg_id'] for r in records})!=len(records):
        raise ValueError('Duplicate lifecycle IDs')
    indexed=bars.set_index('timestamp_utc')
    original=fvgs.set_index('fvg_id',drop=False)
    days={d:day for d,day in bars.groupby(bars.timestamp_ny.dt.date)}
    for r in records:
        f=original.loc[r['fvg_id']]
        for col in fvgs.columns:
            if r[col]!=f[col]:raise ValueError('Original FVG field changed')
        day=days[r['formation_date_ny']]
        candidates=day[(day.timestamp_utc>=r['observable_from_utc']) &
                       (day.timestamp_utc+FIVE<=r['observation_end_utc']) & day.is_complete_5m]
        up=r['direction']=='bullish'
        mask_touch=(candidates.low<=r['top']) & (candidates.high>=r['bottom'])
        masks={'first_touch':mask_touch,
               'first_full_fill':candidates.low<=r['bottom'] if up else candidates.high>=r['top'],
               'close_invalidation':candidates.close<r['bottom'] if up else candidates.close>r['top'],
               'wick_invalidation':candidates.low<r['bottom'] if up else candidates.high>r['top']}
        for name,mask in masks.items():
            expected=candidates.loc[mask,'timestamp_utc'].min() if mask.any() else None
            if r[f'{name}_time']!=expected:raise ValueError('First event mismatch')
        for prefix,offset in [('next',1),('second',2)]:
            t=r['formation_bar_start_utc']+offset*FIVE
            valid=candidates.timestamp_utc.eq(t).any()
            if (r[f'{prefix}_bar_start_utc'] is not None)!=valid:raise ValueError('Post-bar slot mismatch')
            if valid:
                for col in detection.OHLC:
                    if r[f'{prefix}_bar_{col}']!=indexed.loc[t,col]:raise ValueError('Post-bar OHLC mismatch')
        touch=r['first_touch_time']
        pre=candidates if touch is None else candidates[candidates.timestamp_utc<touch]
        if len(pre)!=r['bars_untouched'] or r['minutes_untouched']!=5*len(pre):raise ValueError('Untouched counts mismatch')
        distance=max(ZERO,delta(pre.high.max(),r['top']) if up else delta(r['bottom'],pre.low.min())) if len(pre) else ZERO
        if distance!=r['maximum_points_away_before_touch']:raise ValueError('Untouched extreme mismatch')
        # Independent vector reference for pause first-occurrence and running threshold.
        seed=day[day.timestamp_utc.eq(r['formation_bar_start_utc'])]
        trail=pd.concat([seed,pre]).reset_index(drop=True)
        adjacent=trail.timestamp_utc.diff().eq(FIVE)
        conditions={
            'no_new_extreme':(trail.high.le(trail.high.shift().fillna(trail.high.iloc[0])) if up
                              else trail.low.ge(trail.low.shift().fillna(trail.low.iloc[0]))),
            'opposite_close':(trail.close.lt(trail.close.shift().fillna(trail.close.iloc[0])) if up
                              else trail.close.gt(trail.close.shift().fillna(trail.close.iloc[0])))}
        for kind in KINDS:
            matches=trail.index[adjacent & conditions[kind]]
            expected_pause=trail.loc[matches[0],'timestamp_utc'] if len(matches) else None
            if r[f'{kind}_pause_time']!=expected_pause:raise ValueError('First pause predicate mismatch')
            threshold=None;expected_trigger=None
            if expected_pause is not None:
                preceding=trail[trail.timestamp_utc<expected_pause]
                threshold=preceding.high.max() if up else preceding.low.min()
                later=pre[pre.timestamp_utc>expected_pause]
                breaks=later.close.gt(threshold) if up else later.close.lt(threshold)
                expected_trigger=later.loc[breaks,'timestamp_utc'].min() if breaks.any() else None
            if r[f'{kind}_pre_pause_extreme']!=threshold:raise ValueError('Pre-pause extreme mismatch')
            if r[f'{kind}_trigger_time']!=expected_trigger:raise ValueError('First pause trigger mismatch')
        for method in ['close','wick']:
            invalid=r[f'{method}_invalidation_time'] is not None
            expired=not invalid and not r['observation_censored']
            if r[f'{method}_expired_same_day']!=expired:raise ValueError('Method expiration mismatch')
        for col in ['highest_high_before_touch','highest_close_before_touch','lowest_low_before_touch','lowest_close_before_touch']:
            expected=None
            if len(pre) and (col.startswith('highest')==up):
                price=col.split('_')[1]
                expected=pre[price].max() if up else pre[price].min()
            if r[col]!=expected:raise ValueError('Directional untouched extreme mismatch')
        for prefix,trigger in [('second_candle',r['second_bar_start_utc'] if r['second_candle_research_trigger'] else None),
                               *[(kind,r[f'{kind}_trigger_time']) for kind in KINDS]]:
            if trigger is None:continue
            tail=candidates[candidates.timestamp_utc>trigger]
            reference=indexed.loc[trigger,'close']
            expected=max(ZERO,delta(tail.high.max(),reference) if up else delta(reference,tail.low.min())) if len(tail) else None
            if expected!=r[f'{prefix}_mfe_points']:raise ValueError('MFE mismatch or trigger-bar lookahead')
    return {'exactly_one_record_per_fvg':True,'original_fvg_fields_preserved':True,
            'no_candle3_or_prior_day_interactions':True,'earliest_events_match_complete_source_bars':True,
            'exact_first_second_slots_verified':True,'untouched_extrema_verified':True,
            'first_pause_and_trigger_predicates_and_thresholds_verified':True,'mfe_excludes_trigger_candle':True}


def output_schema(records):
    # Explicit null-capable types even when a direction-specific field is all null.
    original={f.name:f.type for f in detection.SCHEMA}
    if not records:raise ValueError('No FVG records supplied')
    fields=[]
    for key in records[0]:
        vals=[r[key] for r in records if r[key] is not None]
        value=vals[0] if vals else None
        if key in original:typ=original[key]
        elif key.endswith('_ny'):typ=pa.timestamp('ns',tz='America/New_York')
        elif '_time' in key or key.endswith('_utc') or key in ['second_bar_start']:
            typ=pa.timestamp('ns',tz='UTC')
        elif key=='bars_until_first_touch':typ=pa.int64()
        elif isinstance(value,bool):typ=pa.bool_()
        elif isinstance(value,int):typ=pa.int64()
        elif isinstance(value,str):typ=pa.string()
        elif isinstance(value,Decimal) or any(s in key for s in ['extreme','mfe_points','trigger_close','before_touch','pre_pause','bar_open','bar_high','bar_low','bar_close']):typ=pa.decimal128(21,9)
        elif value is None and (key.startswith('next_') or key.startswith('second_')):
            typ=pa.string() if key.endswith('_direction') else pa.bool_()
        else:raise ValueError(f'Cannot infer explicit schema for {key}')
        fields.append(pa.field(key,typ))
    return pa.schema(fields)


def write_output(records,path,hashes):
    table=pa.Table.from_pylist(records,schema=output_schema(records))
    table=table.replace_schema_metadata({b'input_sha256':json.dumps(hashes,sort_keys=True).encode(),
        b'event_times':b'Bar starts; confirmed at start+5m. C3 excluded; full NY-day descriptive events.',
        b'policy':b'Complete bars only; exact +5/+10 slots; separate close/wick terminal states; partial dates censored.',
        b'mfe':b'From research trigger close; strictly later complete bars through same NY date; not trade P&L.'})
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(dir=path.parent,suffix='.parquet');os.close(fd)
    try:
        pq.write_table(table,temp,compression='zstd')
        if not table.equals(pq.read_table(temp)):raise ValueError('Parquet roundtrip failed')
        os.replace(temp,path)
    finally:Path(temp).unlink(missing_ok=True)
    return table


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bars',type=Path,default=BARS)
    parser.add_argument('--fvgs',type=Path,default=FVGS)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--coverage-end',default='2026-10-06T00:00:00Z',help='Exclusive provider request end, UTC')
    args=parser.parse_args()
    if args.output.resolve() in [args.bars.resolve(),args.fvgs.resolve()]:parser.error('Output cannot replace input')
    paths=[args.bars,args.fvgs]
    hashes={p.name:detection.fingerprint(p) for p in paths}
    bars=pq.read_table(args.bars).to_pandas();fvgs=pq.read_table(args.fvgs).to_pandas()
    detection.validate(bars,fvgs)
    records=build(bars,fvgs,pd.Timestamp(args.coverage_end))
    checks=validate_records(bars,fvgs,records)
    if hashes!={p.name:detection.fingerprint(p) for p in paths}:raise RuntimeError('Input changed')
    table=write_output(records,args.output,hashes)
    report={**summary(records),'validation':checks,'inputs_unchanged':True,'input_sha256':hashes}
    data=args.output.parent
    (data/'MNQ_FVG_LIFECYCLE_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    # 20 records: compact CSV, original fields plus all lifecycle columns.
    sample=table.slice(0,min(20,len(records)))
    sample.to_pandas().to_csv(data/'MNQ_FVG_LIFECYCLE_sample.csv',index=False)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
