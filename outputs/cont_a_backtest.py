#!/usr/bin/env python3
"""CONT-A only: causal 5m signals, one MNQ/day, structural stop and fixed 2R."""
from __future__ import annotations
import argparse
from dataclasses import dataclass,asdict
from decimal import Decimal as D,localcontext,ROUND_HALF_UP,ROUND_FLOOR,ROUND_CEILING
import hashlib
import json
from pathlib import Path

import exchange_calendars as xc
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import cont_a_metrics as metrics

ROOT=Path(__file__).resolve().parent
INPUTS={
    'minutes':ROOT/'data/GLBX.MDP3_MNQ.v.0_ohlcv-1m_2024-01-01_2026-10-06.parquet',
    'bars':ROOT/'data/MNQ_5m_2024-01-01_2026-10-06.parquet',
    'fvgs':ROOT/'data/MNQ_FVGs_2024-01-01_2026-10-06.parquet',
    'lifecycle':ROOT/'data/MNQ_FVG_LIFECYCLE_2024-01-01_2026-10-06.parquet'}
TICK=D('0.25');VALUE=D(2);FIVE=pd.Timedelta(minutes=5);ONE=pd.Timedelta(minutes=1)

@dataclass(frozen=True)
class Config:
    commission_per_side_usd:D=D(0)
    slippage_ticks:int=0
    def __post_init__(self):
        if not self.commission_per_side_usd.is_finite() or self.commission_per_side_usd<0 or not isinstance(self.slippage_ticks,int) or self.slippage_ticks<0:
            raise ValueError('Costs must be finite and nonnegative; slippage ticks must be integer')


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def tick(price,rounding=ROUND_HALF_UP):
    return (price/TICK).to_integral_value(rounding=rounding)*TICK


def full_sessions(start='2024-01-01',end='2026-10-06'):
    schedule=xc.get_calendar('XNYS',start=start,end=end).schedule
    rows=[]
    for date,row in schedule.iterrows():
        op=row['open'].tz_convert('America/New_York');cl=row['close'].tz_convert('America/New_York')
        full=op.strftime('%H:%M')=='09:30' and cl.strftime('%H:%M')=='16:00' and (cl-op)==pd.Timedelta(minutes=390)
        rows.append({'date':date.date().isoformat(),'open_utc':row['open'].isoformat(),
                     'close_utc':row['close'].isoformat(),'full_session':full})
    return {r['date'] for r in rows if r['full_session']},rows


def ratio(bar):
    span=bar.high-bar.low
    return float(abs(bar.close-bar.open)/span) if span else None


def candle_direction(bar):return 'bullish' if bar.close>bar.open else 'bearish' if bar.close<bar.open else 'doji'


def signals(bars,fvgs):
    if bars.timestamp_utc.duplicated().any() or fvgs.fvg_id.duplicated().any():raise ValueError('Duplicate source keys')
    b=bars.sort_values('timestamp_utc').set_index('timestamp_utc',drop=False)
    # Optional, causal descriptive ATR(14): simple mean of true ranges. Never filters.
    prices=b[['high','low','close']].astype(float)
    tr=pd.concat([prices.high-prices.low,(prices.high-prices.close.shift()).abs(),(prices.low-prices.close.shift()).abs()],axis=1).max(axis=1)
    atr=tr.where(b.is_complete_5m).rolling(14,min_periods=14).mean()
    result=[]
    for f in fvgs.sort_values(['formation_bar_start_utc','fvg_id']).to_dict('records'):
        t=f['formation_bar_start_utc'];keys=[t-2*FIVE,t-FIVE,t,t+FIVE,t+2*FIVE]
        if any(k not in b.index for k in keys):continue
        candles=[b.loc[k] for k in keys]
        if not all(c.is_complete_5m for c in candles):continue
        if any(str(c.timestamp_ny.date())!=str(f['formation_date_ny']) for c in candles):continue
        first,second=candles[3:];up=f['direction']=='bullish'
        good=(first.low>f['top'] and second.low>f['top'] and second.close>first.high) if up else (first.high<f['bottom'] and second.high<f['bottom'] and second.close<first.low)
        entry=t+3*FIVE;ny=entry.tz_convert('America/New_York')
        if not good or ny.date()!=f['formation_date_ny']:continue
        r={'signal_id':f['fvg_id']+'@'+str(entry.value),'fvg_id':f['fvg_id'],
           'direction':'LONG' if up else 'SHORT','formation_date':f['formation_date_ny'],
           'formation_time_utc':t,'formation_time_ny':f['formation_bar_start_ny'],
           'opening_exception':f['opening_exception'],'fvg_top':f['top'],'fvg_bottom':f['bottom'],
           'fvg_size_points':f['size_points'],'entry_time_utc':entry,'entry_time_ny':ny,
           'signal_close_price':second.close,'atr14_simple_points':None if pd.isna(atr.loc[keys[-1]]) else float(atr.loc[keys[-1]])}
        for name,c in [('first',first),('second',second)]:
            r[f'{name}_bar_time_ny']=c.timestamp_ny;r[f'{name}_bar_time_utc']=c.timestamp_utc
            for col in ['open','high','low','close']:r[f'{name}_bar_{col}']=c[col]
            r[f'{name}_bar_body_ratio']=ratio(c);r[f'{name}_bar_direction']=candle_direction(c)
            r[f'{name}_bar_range']=c.high-c.low
        result.append(r)
    return sorted(result,key=lambda r:(r['entry_time_utc'],r['formation_time_utc'],r['fvg_id']))


def levels(signal,config):
    long=signal['direction']=='LONG';sign=D(1) if long else D(-1)
    entry=tick(signal['signal_close_price'])+sign*TICK*config.slippage_ticks
    stop=tick(signal['first_bar_low']-TICK,ROUND_FLOOR) if long else tick(signal['first_bar_high']+TICK,ROUND_CEILING)
    risk=(entry-stop)*sign
    if risk<=0:return None
    target=tick(entry+sign*2*risk)
    return {'entry_price':entry,'stop_price':stop,'target_price':target,'risk_points':risk,'risk_usd':risk*VALUE}


def select(raw,dates,config):
    selected=[];audit=[];locked=set();eligible=[]
    for s in sorted(raw,key=lambda s:(s['entry_time_utc'],s['formation_time_utc'],s['fvg_id'])):
        date=s['entry_time_ny'].date().isoformat();trigger=s['second_bar_time_ny']
        reason=None;lv=None
        if s['formation_date']!=s['entry_time_ny'].date():reason='WRONG_NY_DATE'
        elif trigger.hour>=11:reason='TRIGGER_AT_OR_AFTER_1100'
        elif date not in dates:reason='NOT_FULL_XNYS_SESSION'
        else:
            lv=levels(s,config)
            if lv is None:reason='NON_POSITIVE_RISK'
            else:
                eligible.append(s)
                if date in locked:reason='DAILY_LOCK_COMPETING_SIGNAL'
                else:
                    locked.add(date);selected.append({**s,**lv});reason='SELECTED'
        audit.append({'signal_id':s['signal_id'],'fvg_id':s['fvg_id'],'direction':s['direction'],
                      'entry_time_utc':s['entry_time_utc'],'entry_time_ny':s['entry_time_ny'],
                      'formation_time_utc':s['formation_time_utc'],'reason':reason})
    return selected,eligible,audit


def execute(s,minute_frame,config):
    entry=s['entry_price'];stop=s['stop_price'];target=s['target_price'];long=s['direction']=='LONG';sign=D(1) if long else D(-1)
    at=s['entry_time_utc'];end=pd.Timestamp(s['entry_time_ny'].date(),tz='America/New_York')+pd.Timedelta(hours=16)
    end=end.tz_convert('UTC')
    minutes=minute_frame.set_index('ts_event',drop=False) if 'ts_event' in minute_frame.columns else minute_frame
    peak=entry;trough=entry;conflict=False;gap=False;bars=0
    while at<end:
        if at not in minutes.index:raise ValueError(f'Missing execution minute {at}; no synthetic fill or silent skip')
        row=minutes.loc[at]
        if isinstance(row,pd.DataFrame):raise ValueError('Duplicate execution minute')
        # Exits and excursions only from the owned interval, including the exit minute.
        high=row.high;low=row.low;op=row.open;cl=row.close
        if high<max(op,cl) or low>min(op,cl) or high<low:raise ValueError('Invalid execution OHLC')
        peak=max(peak,high);trough=min(trough,low);bars+=1
        hit_stop=low<=stop if long else high>=stop
        hit_target=high>=target if long else low<=target
        conflict=hit_stop and hit_target
        if hit_stop:
            # Adverse gap stop executes at worse open; same-minute stop priority is unconditional.
            base=min(stop,op) if long else max(stop,op);gap=base!=stop;reason='STOP'
        elif hit_target:base=target;reason='TARGET'
        elif at+ONE==end:base=cl;reason='SESSION_CLOSE'
        else:at+=ONE;continue
        exit_price=tick(base)-sign*TICK*config.slippage_ticks
        break
    else:raise ValueError('Entry is outside allowed execution session')
    gross_points=(exit_price-entry)*sign;gross_usd=gross_points*VALUE
    commission=config.commission_per_side_usd*2;net=gross_usd-commission
    mfe=max(D(0),peak-entry if long else entry-trough);mae=max(D(0),entry-trough if long else peak-entry)
    exit_time=at+ONE # OHLC reveals an interval, not an exact intraminute fill instant.
    r={**s,'trade_id':hashlib.sha256(('CONT-A-v1|'+s['signal_id']).encode()).hexdigest(),
       'quantity':1,'exit_bar_start_utc':at,'exit_bar_start_ny':at.tz_convert('America/New_York'),
       'exit_time_utc':exit_time,'exit_time_ny':exit_time.tz_convert('America/New_York'),
       'exit_price':exit_price,'exit_reason':reason,'pnl_points':gross_points,'pnl_usd':net,
       'gross_pnl_points':gross_points,'net_pnl_points':net/VALUE,'gross_pnl_usd':gross_usd,'net_pnl_usd':net,
       'commission_usd':commission,'result_r':float(net/s['risk_usd']),'gross_result_r':float(gross_points/s['risk_points']),
       'mfe_points':mfe,'mae_points':mae,'mfe_r':float(mfe/s['risk_points']),'mae_r':float(mae/s['risk_points']),
       'duration_minutes':int((exit_time-s['entry_time_utc']).total_seconds()/60),'duration_1m_bars':bars,
       'same_minute_stop_target_conflict':conflict,'adverse_stop_gap':gap,
       'exit_minute_extrema_order_unknown':reason!='SESSION_CLOSE',
       'entry_hour':s['entry_time_ny'].hour,'entry_minute':s['entry_time_ny'].minute,
       'weekday':s['entry_time_ny'].day_name(),'month':s['entry_time_ny'].month,'year':s['entry_time_ny'].year}
    return r


def reconcile(raw,life):
    ids={s['fvg_id'] for s in raw}
    events=life[life.second_candle_research_trigger]
    life_ids=set(events.fvg_id)
    if ids!=life_ids:raise ValueError('Raw CONT-A signals differ from lifecycle events; inspect before continuing')
    qualified=events[events.research_day_eligible]
    if len(qualified)!=1639:raise ValueError('Qualified lifecycle count no longer equals prior validated 1639')
    return {'raw_signal_count':len(raw),'lifecycle_raw_count':len(events),'qualified_lifecycle_count':len(qualified),
            'exact_raw_fvg_id_set_match':True,'excluded_from_prior_research_censored':int(events.observation_censored.sum()),
            'excluded_from_prior_research_incomplete_later_bars':int(events.incomplete_bars_skipped.gt(0).sum()),
            'raw_events_not_used_as_causal_filters':'research_day_eligible is used only for reconciliation, never for trade selection',
            'qualified_lifecycle_mfe_average':float(qualified.second_candle_mfe_points.astype(float).mean()),
            'qualified_lifecycle_mfe_median':float(qualified.second_candle_mfe_points.astype(float).median())}


def frame_table(rows):
    if not rows:raise ValueError('No rows to write')
    fields=[]
    for k in rows[0]:
        value=next((r[k] for r in rows if r[k] is not None),None)
        if isinstance(value,pd.Timestamp):typ=pa.timestamp('ns',tz=str(value.tz))
        elif isinstance(value,D):typ=pa.decimal128(24,9)
        elif isinstance(value,bool):typ=pa.bool_()
        elif isinstance(value,int):typ=pa.int64()
        elif isinstance(value,float) or value is None:typ=pa.float64()
        elif k=='formation_date':typ=pa.date32()
        else:typ=pa.string()
        fields.append((k,typ))
    return pa.Table.from_pylist(rows,schema=pa.schema(fields))


def run(config=Config(),destination=ROOT/'results'):
    hashes={k:sha(p) for k,p in INPUTS.items()}
    data={k:pq.read_table(p).to_pandas() for k,p in INPUTS.items()}
    raw=signals(data['bars'],data['fvgs']);cross=reconcile(raw,data['lifecycle'])
    dates,calendar=full_sessions()
    chosen,eligible,audit=select(raw,dates,config)
    m=data['minutes']
    if 'ts_event' not in m:m=m.reset_index()
    if m.ts_event.duplicated().any():raise ValueError('Duplicate raw minute timestamps')
    # Convert only price units; source UTC timestamps and files remain unchanged.
    for col in ['open','high','low','close']:m[col]=m[col].map(lambda x:D(int(x)).scaleb(-9))
    day_groups={d:g.set_index('ts_event',drop=False) for d,g in m.groupby(m.ts_event.dt.tz_convert('America/New_York').dt.date)}
    trades=[execute(s,day_groups[s['entry_time_ny'].date()],config) for s in chosen]
    if len({t['trade_id'] for t in trades})!=len(trades) or len({t['formation_date'] for t in trades})!=len(trades):raise ValueError('Duplicate trade or daily lock failure')
    for t in trades:
        if t['second_bar_time_ny'].hour>=11 or t['entry_time_ny'].strftime('%H:%M')>'11:00':raise ValueError('Late entry')
        if t['formation_date']!=t['entry_time_ny'].date() or t['exit_time_ny'].date()!=t['formation_date']:raise ValueError('Cross-date trade')
        for k in ['entry_price','stop_price','target_price','exit_price']:
            if t[k]%TICK!=0:raise ValueError('Off-tick executable price')
        if abs(t['target_price']-t['entry_price'])!=2*t['risk_points']:raise ValueError('Target moved from original 2R')
    independent={}
    if config==Config():
        from cont_a_validate import validate
        independent=validate(trades,data['minutes'])
    if hashes!={k:sha(p) for k,p in INPUTS.items()}:raise RuntimeError('Input file changed')
    from collections import Counter
    report={**metrics.summary(trades,eligible),'strategy':'CONT-A — Second-Candle FVG Continuation',
            'config':{k:str(v) for k,v in asdict(config).items()},'input_sha256':hashes,
            'signal_reconciliation':cross,'total_eligible_signals_before_daily_lock':len(eligible),
            'signal_audit_counts':dict(sorted(Counter(a['reason'] for a in audit).items())),
            'calendar':{'library':'exchange_calendars','version':xc.__version__,'name':'XNYS',
                        'start':'2024-01-01','end':'2026-10-06','full_session_dates':len(dates),
                        'schedule_sha256':hashlib.sha256(json.dumps(calendar,sort_keys=True).encode()).hexdigest()},
            'execution_assumptions':{'entry_minute_included':True,'exit_time_is_minute_end_confirmation':True,
                                    'exit_minute_full_extrema_included':True,'same_minute_order':'STOP_FIRST',
                                    'stop_gap_fill':'worse of stop and minute open','target_fill':'target; no favorable gap improvement',
                                    'missing_owned_minute':'fail run, never skip trade','slippage':'adverse ticks on entry and every exit; target based on executed entry',
                                    'drawdown':'closed-trade net USD from initial zero; no mark-to-market'},
            'validation':{'one_trade_per_date':True,'same_day_only':True,'no_late_entries':True,'tick_alignment':True,
                          'original_stop_and_2r_target_only':True,'inputs_unchanged':True,**independent}}
    destination.mkdir(parents=True,exist_ok=True)
    stem=destination/'CONT_A_second_candle_baseline'
    table=frame_table(trades)
    pq.write_table(table,str(stem)+'_trades.parquet',compression='zstd')
    table.to_pandas().to_csv(str(stem)+'_trades.csv',index=False)
    pd.DataFrame(audit).to_csv(str(stem)+'_signal_audit.csv',index=False)
    pd.DataFrame(calendar).to_csv(str(stem)+'_xnys_calendar.csv',index=False)
    _,curve=metrics.drawdown(sorted(trades,key=lambda t:t['exit_time_utc']))
    pd.DataFrame(curve).to_csv(str(stem)+'_equity.csv',index=False)
    Path(str(stem)+'_summary.json').write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    if not table.equals(pq.read_table(str(stem)+'_trades.parquet')):raise ValueError('Parquet roundtrip failed')
    print(json.dumps({'reconciliation':cross,'filters':report['signal_audit_counts'],'overall':report['overall']},indent=2))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--commission-per-side-usd',default='0')
    p.add_argument('--slippage-ticks',type=int,default=0)
    p.add_argument('--output-dir',type=Path,default=ROOT/'results')
    a=p.parse_args()
    with localcontext() as ctx:
        ctx.prec=38
        run(Config(D(a.commission_per_side_usd),a.slippage_ticks),a.output_dir)


if __name__=='__main__':main()
