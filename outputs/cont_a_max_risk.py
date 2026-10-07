#!/usr/bin/env python3
"""One controlled variant: original risk strictly below 100 before daily selection."""
import argparse
from collections import Counter
from decimal import Decimal as D, localcontext
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
import cont_a_backtest as base
import cont_a_metrics as metrics
from cont_a_validate import validate

STEM='CONT_A_max_risk_100'
MAX_RISK=D('100.00')


def select(raw, dates):
    # Reuse baseline eligibility and ordering; discard its provisional daily selection.
    _, pre, original_audit=base.select(raw,dates,base.Config())
    rejected={s['signal_id'] for s in pre if base.levels(s,base.Config())['risk_points']>=MAX_RISK}
    allowed=[s for s in pre if s['signal_id'] not in rejected]
    selected, eligible, filtered_audit=base.select(allowed,dates,base.Config())
    updated={a['signal_id']:a for a in filtered_audit}
    source={s['signal_id']:s for s in pre}
    audit=[]
    for a in original_audit:
        a=dict(updated.get(a['signal_id'],a))
        if a['signal_id'] in rejected:a['reason']='MAX_RISK_FILTER'
        a['risk_points']=base.levels(source[a['signal_id']],base.Config())['risk_points'] if a['signal_id'] in source else None
        audit.append(a)
    return selected,eligible,audit,len(pre)


def replacements(trades, baseline):
    old={t['formation_date']:t for t in baseline}
    result=[]
    for t in trades:
        prior=old.get(t['formation_date'])
        if prior and prior['signal_id']!=t['signal_id']:
            if prior['risk_points']<MAX_RISK:raise ValueError('Unexpected replacement of eligible baseline trade')
            result.append({**t,'rejected_baseline_trade_id':prior['trade_id'],
                           'rejected_baseline_signal_id':prior['signal_id'],
                           'rejected_baseline_entry_time_ny':prior['entry_time_ny'],
                           'rejected_baseline_risk_points':prior['risk_points'],
                           'rejected_baseline_net_pnl_usd':prior['net_pnl_usd']})
    return result


def underwater(trades):
    """Calendar elapsed time from prior peak to recovery; open spells end at last close."""
    rows=sorted(trades,key=lambda t:t['exit_time_utc'])
    if not rows:return None
    peak=equity=D(0);peak_at=rows[0]['entry_time_utc'];start=None;spells=[]
    for t in rows:
        equity+=t['net_pnl_usd'];at=t['exit_time_utc']
        if equity>=peak:
            if start is not None:spells.append((start,at,True));start=None
            peak=equity;peak_at=at
        elif start is None:start=peak_at
    if start is not None:spells.append((start,rows[-1]['exit_time_utc'],False))
    if not spells:return {'calendar_days':0,'recovered':True}
    a,b,recovered=max(spells,key=lambda v:v[1]-v[0])
    return {'start_utc':a.isoformat(),'end_utc':b.isoformat(),'calendar_days':(b-a).total_seconds()/86400,
            'recovered':recovered,'observation_end':'last recorded trade close; no mark-to-market'}


def enrich(trades,eligible,baseline):
    r=metrics.summary(trades,eligible)
    subset=[t for t in baseline if t['risk_points']<MAX_RISK]
    replacement=replacements(trades,baseline)
    same={t['trade_id']:t for t in trades}
    for old in subset:
        if old['trade_id'] not in same:raise ValueError('Eligible original trade missing')
        if any(same[old['trade_id']][k]!=v for k,v in old.items()):raise ValueError('Original eligible trade changed')
    if len(trades)!=len(subset)+len(replacement):raise ValueError('Replacement partition mismatch')
    r['comparison']={'baseline':metrics.performance(baseline),'historical_under_100_subset':metrics.performance(subset),
                     'replacement_trades':metrics.performance(replacement)}
    bins=[('0-25',0,25),('25-50',25,50),('50-75',50,75),('75-100',75,100),('100+',100,float('inf'))]
    r['entry_distance_buckets']={k:metrics.performance([t for t in trades if a<=t['entry_distance_from_fvg_points']<b]) for k,a,b in bins}
    for field in ['mfe_r','mae_r']:r['excursions']['average_'+field]=sum(t[field] for t in trades)/len(trades)
    months=r['monthly'];active={k:v for k,v in months.items() if v['trades']}
    longest=streak=0
    for v in months.values():
        streak=streak+1 if v['net_pnl_usd']<0 else 0;longest=max(longest,streak)
    r['month_statistics']={'best_month':max(active,key=lambda k:active[k]['net_pnl_usd']),
        'worst_month':min(active,key=lambda k:active[k]['net_pnl_usd']),
        'profitable_months':sum(v['net_pnl_usd']>0 for v in months.values()),
        'losing_months':sum(v['net_pnl_usd']<0 for v in months.values()),
        'zero_pnl_months':sum(v['net_pnl_usd']==0 for v in months.values()),'longest_losing_month_sequence':longest}
    r['longest_time_below_peak']=underwater(trades)
    return r,replacement


def protected_files():
    return sorted(set(base.INPUTS.values())|set(base.ROOT.glob('cont_a_*.py'))- {Path(__file__).resolve()} |
                  set((base.ROOT/'results').glob('CONT_A_second_candle_baseline*')) |
                  {base.ROOT/'CONT_A_SECOND_CANDLE_BASELINE.md'})


def run(destination=base.ROOT/'results'):
    protected=protected_files();hashes={str(p.relative_to(base.ROOT)):base.sha(p) for p in protected}
    data={k:pq.read_table(p).to_pandas() for k,p in base.INPUTS.items()}
    baseline=pq.read_table(base.ROOT/'results/CONT_A_second_candle_baseline_trades.parquet').to_pylist()
    # Arrow timestamps become pandas Timestamps at nanosecond precision.
    raw=base.signals(data['bars'],data['fvgs']);cross=base.reconcile(raw,data['lifecycle'])
    dates,calendar=base.full_sessions();chosen,eligible,audit,pre_count=select(raw,dates)
    raw_minutes=data['minutes']
    m=raw_minutes.copy()
    if 'ts_event' not in m:m=m.reset_index()
    if m.ts_event.duplicated().any():raise ValueError('Duplicate execution minute')
    for col in ['open','high','low','close']:m[col]=m[col].map(lambda x:D(int(x)).scaleb(-9))
    groups={day:g.set_index('ts_event',drop=False) for day,g in m.groupby(m.ts_event.dt.tz_convert('America/New_York').dt.date)}
    trades=[]
    for s in chosen:
        t=base.execute(s,groups[s['formation_date']],base.Config())
        t['entry_distance_from_fvg_points']=t['entry_price']-t['fvg_top'] if t['direction']=='LONG' else t['fvg_bottom']-t['entry_price']
        trades.append(t)
    if len({t['formation_date'] for t in trades})!=len(trades):raise ValueError('Daily lock failure')
    for t in trades:
        assert D(0)<t['risk_points']<MAX_RISK
        assert t['second_bar_time_ny'].hour<11 and t['entry_time_ny'].strftime('%H:%M')<='11:00'
        assert t['formation_date']==t['entry_time_ny'].date()==t['exit_time_ny'].date()
        assert all(t[k]%base.TICK==0 for k in ['entry_price','stop_price','target_price','exit_price'])
        assert abs(t['target_price']-t['entry_price'])==2*t['risk_points']
    validation=validate(trades,raw_minutes)
    r,replacement=enrich(trades,eligible,baseline)
    counts=dict(sorted(Counter(a['reason'] for a in audit).items()))
    r.update(strategy='CONT-A — Second-Candle Continuation — Max Risk <100',
        config={'maximum_original_risk_points_exclusive':'100.00','commission_per_side_usd':'0','slippage_ticks':0},
        signal_reconciliation=cross,signal_audit_counts=counts,
        signal_accounting={'raw_signals':len(raw),'calendar_cutoff_positive_risk_eligible':pre_count,
            'max_risk_rejections':counts.get('MAX_RISK_FILTER',0),'eligible_after_max_risk':len(eligible),
            'competing_after_actual_entry':counts.get('DAILY_LOCK_COMPETING_SIGNAL',0),
            'actual_trades':len(trades),'replacement_trade_days':len(replacement)},
        protected_sha256=hashes,validation=validation)
    assert pre_count==counts.get('MAX_RISK_FILTER',0)+len(eligible)
    assert len(eligible)==len(trades)+counts.get('DAILY_LOCK_COMPETING_SIGNAL',0)
    for key in ['direction','yearly','monthly','trigger_time_bins','entry_distance_buckets']:
        assert sum(x['trades'] for x in r[key].values())==len(trades)
        assert sum(x['net_pnl_usd'] for x in r[key].values())==r['overall']['net_pnl_usd']
    if hashes!={str(p.relative_to(base.ROOT)):base.sha(p) for p in protected}:raise RuntimeError('Protected file changed')
    r['validation'].update(protected_files_unchanged=True,all_retained_baseline_trades_identical=True,group_totals_reconcile=True)
    destination.mkdir(parents=True,exist_ok=True);stem=destination/STEM
    table=base.frame_table(trades);pq.write_table(table,str(stem)+'_trades.parquet',compression='zstd')
    table.to_pandas().to_csv(str(stem)+'_trades.csv',index=False)
    pd.DataFrame(audit).to_csv(str(stem)+'_signal_audit.csv',index=False)
    pd.DataFrame(replacement).to_csv(str(stem)+'_replacement_trades.csv',index=False)
    _,curve=metrics.drawdown(sorted(trades,key=lambda t:t['exit_time_utc']))
    pd.DataFrame(curve).to_csv(str(stem)+'_equity.csv',index=False)
    Path(str(stem)+'_summary.json').write_text(json.dumps(r,sort_keys=True,indent=2,allow_nan=False)+'\n')
    if not table.equals(pq.read_table(str(stem)+'_trades.parquet')):raise ValueError('Parquet roundtrip mismatch')
    print(json.dumps({'signals':r['signal_accounting'],'overall':r['overall']},indent=2))
    return r


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,default=base.ROOT/'results')
    with localcontext() as ctx:
        ctx.prec=38;run(parser.parse_args().output_dir)
