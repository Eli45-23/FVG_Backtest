"""Closed-trade metrics for CONT-A; no selection or parameter optimization."""
from itertools import groupby
import numpy as np


def drawdown(trades):
    equity=peak=0.0
    peak_time=None;max_dd=0.0;dd_peak=None;bottom=None;old_peak_value=0.0;bottom_idx=None
    curve=[]
    for i,t in enumerate(trades):
        equity+=float(t['net_pnl_usd'])
        if equity>=peak:
            peak=equity;peak_time=t['exit_time_utc'].isoformat()
        depth=peak-equity
        curve.append({'exit_time_utc':t['exit_time_utc'].isoformat(),'trade_id':t['trade_id'],
                      'cumulative_net_pnl_usd':equity,'peak_equity_usd':peak,'drawdown_usd':depth})
        if depth>max_dd:
            max_dd=depth;dd_peak=peak_time;bottom=t['exit_time_utc'].isoformat();old_peak_value=peak;bottom_idx=i
    recovery=next((x['exit_time_utc'] for x in curve[(bottom_idx+1):] if x['cumulative_net_pnl_usd']>=old_peak_value),None) if bottom_idx is not None else None
    return {'peak_equity_usd':peak,'max_closed_trade_drawdown_usd':max_dd,
            'max_drawdown_peak_time_utc':dd_peak,'max_drawdown_peak_is_initial_zero':bool(max_dd and dd_peak is None),
            'max_drawdown_bottom_time_utc':bottom,'peak_recovered':recovery is not None if max_dd else True,
            'recovery_time_utc':recovery},curve


def performance(trades):
    ts=sorted(trades,key=lambda t:(t['exit_time_utc'],t['trade_id']))
    pnl=[float(t['net_pnl_usd']) for t in ts];rs=[float(t['result_r']) for t in ts]
    wins=[x for x in pnl if x>0];losses=[x for x in pnl if x<0]
    avg=lambda v: float(np.mean(v)) if v else None
    med=lambda v: float(np.median(v)) if v else None
    gp=sum(wins);gl=-sum(losses)
    streaks=[(k,len(list(g))) for k,g in groupby(1 if x>0 else -1 if x<0 else 0 for x in pnl)]
    dd,_=drawdown(ts)
    return {'trades':len(ts),'long_trades':sum(t['direction']=='LONG' for t in ts),
            'short_trades':sum(t['direction']=='SHORT' for t in ts),'winners':len(wins),'losers':len(losses),
            'breakeven':len(ts)-len(wins)-len(losses),'session_close_trades':sum(t['exit_reason']=='SESSION_CLOSE' for t in ts),
            'win_rate_percent':100*len(wins)/len(ts) if ts else None,
            'gross_pnl_usd':sum(float(t['gross_pnl_usd']) for t in ts),
            'net_pnl_usd':sum(pnl),'net_pnl_points':sum(float(t['net_pnl_points']) for t in ts),
            'gross_profit_usd':gp,'gross_loss_usd':gl,'profit_factor':gp/gl if gl else None,
            'profit_factor_status':'finite' if gl else 'no_losses' if gp else 'undefined',
            'average_pnl_per_trade_usd':avg(pnl),'average_winner_usd':avg(wins),'average_loser_usd':avg(losses),
            'median_winner_usd':med(wins),'median_loser_usd':med(losses),'average_r':avg(rs),'median_r':med(rs),'total_r':sum(rs),
            'largest_winner_usd':max(wins) if wins else None,'largest_loser_usd':min(losses) if losses else None,
            'maximum_consecutive_wins':max([v for k,v in streaks if k==1],default=0),
            'maximum_consecutive_losses':max([v for k,v in streaks if k==-1],default=0),
            'average_risk_points':avg([float(t['risk_points']) for t in ts]),
            'median_risk_points':med([float(t['risk_points']) for t in ts]),
            'average_duration_minutes':avg([t['duration_minutes'] for t in ts]),
            'median_duration_minutes':med([t['duration_minutes'] for t in ts]),
            'same_minute_conflicts':sum(t['same_minute_stop_target_conflict'] for t in ts),**dd}


def summary(trades,eligible_signals):
    def split(values,key):return {str(v):performance([t for t in trades if key(t)==v]) for v in values}
    years=split([2024,2025,2026],lambda t:t['year'])
    months=split([f'{y}-{m:02}' for y in range(2024,2027) for m in range(1,13) if y<2026 or m<=10],lambda t:t['entry_time_ny'].strftime('%Y-%m'))
    for k,v in months.items():
        rows=[t for t in trades if t['entry_time_ny'].strftime('%Y-%m')==k]
        v['long_pnl_usd']=sum(float(t['net_pnl_usd']) for t in rows if t['direction']=='LONG')
        v['short_pnl_usd']=sum(float(t['net_pnl_usd']) for t in rows if t['direction']=='SHORT')
    timebins=[('09:30-09:59',570,600),('10:00-10:29',600,630),('10:30-10:59',630,660)]
    clock=lambda t:t['second_bar_time_ny'].hour*60+t['second_bar_time_ny'].minute
    times={k:{**performance([t for t in trades if a<=clock(t)<b]),
              'signals':sum(a<=clock(s)<b for s in eligible_signals)} for k,a,b in timebins}
    sizes=[('0-25',0,25),('25-50',25,50),('50-75',50,75),('75-100',75,100),('100-150',100,150),('150-200',150,200),('200+',200,float('inf'))]
    risks={k:performance([t for t in trades if a<=float(t['risk_points'])<b]) for k,a,b in sizes}
    def pct(field,level):return 100*sum(float(t[field])>=level for t in trades)/len(trades) if trades else None
    exc={'mfe_percent_at_least_points':{str(n):pct('mfe_points',n) for n in [25,50,75,100,150,200]},
         'mfe_percent_at_least_r':{str(n):pct('mfe_r',n) for n in [.5,1,1.5,2]},
         'stop_with_mfe_at_least_2r':sum(t['exit_reason']=='STOP' and t['mfe_r']>=2 for t in trades),
         'stop_conflict_with_mfe_at_least_2r':sum(t['exit_reason']=='STOP' and t['same_minute_stop_target_conflict'] and t['mfe_r']>=2 for t in trades),
         'average_mfe_points':float(np.mean([float(t['mfe_points']) for t in trades])) if trades else None,
         'median_mfe_points':float(np.median([float(t['mfe_points']) for t in trades])) if trades else None,
         'average_mae_points':float(np.mean([float(t['mae_points']) for t in trades])) if trades else None,
         'median_mae_points':float(np.median([float(t['mae_points']) for t in trades])) if trades else None}
    return {'overall':performance(trades),'direction':split(['LONG','SHORT'],lambda t:t['direction']),
            'yearly':years,'monthly':months,'trigger_time_bins':times,
            'weekday':split(['Monday','Tuesday','Wednesday','Thursday','Friday'],lambda t:t['weekday']),
            'risk_buckets_left_inclusive':risks,'excursions':exc}
