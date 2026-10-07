#!/usr/bin/env python3
"""Controlled time exclusion after strict risk <100 and before daily selection."""
import argparse
from collections import Counter
from decimal import Decimal as D, localcontext
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
import cont_a_backtest as base
import cont_a_metrics as metrics
import cont_a_max_risk as control
from cont_a_validate import validate

STEM='CONT_A_risk100_no_1000_1029'
MAX_RISK=D('100.00')


def banned(s):
    t=s['second_bar_time_ny']
    return 600 <= t.hour*60+t.minute < 630


def select(raw, dates):
    _, pre, old_audit, count=control.select(raw,dates)
    allowed=[s for s in pre if not banned(s)]
    selected,eligible,new_audit=base.select(allowed,dates,base.Config())
    updated={a['signal_id']:a for a in new_audit}
    rejected={s['signal_id'] for s in pre if banned(s)}
    audit=[]
    for old in old_audit:
        a={**old,**updated.get(old['signal_id'],{})}
        if a['signal_id'] in rejected:a['reason']='TIME_WINDOW_FILTER'
        audit.append(a)
    return selected,eligible,audit,count


def replacements(trades, baseline):
    old={t['formation_date']:t for t in baseline}
    result=[]
    for t in trades:
        prior=old.get(t['formation_date'])
        if prior and prior['signal_id']!=t['signal_id']:
            if not banned(prior) or prior['entry_time_utc']>=t['entry_time_utc']:
                raise ValueError('Unexpected time-filter replacement')
            result.append({**t,'rejected_signal_id':prior['signal_id'],
                'rejected_trigger_time_ny':prior['second_bar_time_ny'],
                'rejected_direction':prior['direction'],'rejected_risk_points':prior['risk_points'],
                'rejected_control_pnl_usd':prior['net_pnl_usd']})
    return result


def enrich(trades,eligible,baseline):
    r=metrics.summary(trades,eligible)
    subset=[t for t in baseline if not banned(t)]
    replacement=replacements(trades,baseline)
    same={t['trade_id']:t for t in trades}
    for old in subset:
        if old['trade_id'] not in same:raise ValueError('Eligible original trade missing')
        if any(same[old['trade_id']][k]!=v for k,v in old.items()):raise ValueError('Original eligible trade changed')
    if len(trades)!=len(subset)+len(replacement):raise ValueError('Replacement partition mismatch')
    r['comparison']={'baseline':metrics.performance(baseline),'historical_allowed_time_subset':metrics.performance(subset),
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
    r['longest_time_below_peak']=control.underwater(trades)
    return r,replacement


def protected_files():
    return sorted(set(base.INPUTS.values()) |
        {p for p in base.ROOT.glob('*.py') if p.name not in ['cont_a_time_filter.py','render_cont_a_time_filter.py']} |
        set((base.ROOT/'results').glob('CONT_A_second_candle_baseline*')) |
        set((base.ROOT/'results').glob('CONT_A_max_risk_100*')) |
        {base.ROOT/'CONT_A_SECOND_CANDLE_BASELINE.md',base.ROOT/'CONT_A_MAX_RISK_100.md'})


def run(destination=base.ROOT/'results'):
    protected=protected_files();hashes={str(p.relative_to(base.ROOT)):base.sha(p) for p in protected}
    data={k:pq.read_table(p).to_pandas() for k,p in base.INPUTS.items()}
    baseline=pq.read_table(base.ROOT/'results/CONT_A_max_risk_100_trades.parquet').to_pylist()
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
        assert D(0)<t['risk_points']<MAX_RISK and not banned(t)
        assert t['second_bar_time_ny'].hour<11 and t['entry_time_ny'].strftime('%H:%M')<='11:00'
        assert t['formation_date']==t['entry_time_ny'].date()==t['exit_time_ny'].date()
        assert all(t[k]%base.TICK==0 for k in ['entry_price','stop_price','target_price','exit_price'])
        assert abs(t['target_price']-t['entry_price'])==2*t['risk_points']
    validation=validate(trades,raw_minutes)
    r,replacement=enrich(trades,eligible,baseline)
    rejected_times=[a for a in audit if a['reason']=='TIME_WINDOW_FILTER']
    replacement_dates={t['formation_date'] for t in trades if any(
        a['entry_time_ny'].date()==t['formation_date'] and a['entry_time_utc']<t['entry_time_utc']
        for a in rejected_times)}
    if replacement_dates!={t['formation_date'] for t in replacement}:raise ValueError('Replacement audit mismatch')
    counts=dict(sorted(Counter(a['reason'] for a in audit).items()))
    r.update(strategy='CONT-A — Max Risk <100 — Exclude 10:00–10:29 ET',
        config={'maximum_original_risk_points_exclusive':'100.00','commission_per_side_usd':'0','slippage_ticks':0,'excluded_trigger_minutes_ny':[600,630]},
        signal_reconciliation=cross,signal_audit_counts=counts,
        signal_accounting={'raw_signals':len(raw),'calendar_cutoff_positive_risk_eligible':pre_count,
            'max_risk_rejections':counts.get('MAX_RISK_FILTER',0),'time_filter_rejections':counts.get('TIME_WINDOW_FILTER',0),'final_eligible_signals':len(eligible),
            'competing_after_actual_entry':counts.get('DAILY_LOCK_COMPETING_SIGNAL',0),
            'actual_trades':len(trades),'time_filter_replacement_days':len(replacement)},
        protected_sha256=hashes,validation=validation)
    assert pre_count==counts.get('MAX_RISK_FILTER',0)+counts.get('TIME_WINDOW_FILTER',0)+len(eligible)
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
    pd.DataFrame(replacement).to_csv(str(stem)+'_replacements.csv',index=False)
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
