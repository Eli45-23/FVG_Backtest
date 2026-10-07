"""Independent array-based verification of each saved CONT-A execution."""
from decimal import Decimal as D
import numpy as np
import pandas as pd


def validate(trades,minutes):
    if 'ts_event' in minutes:minutes=minutes.set_index('ts_event')
    checks=0
    for t in trades:
        start=t['entry_time_utc'];end=pd.Timestamp(t['formation_date'],tz='America/New_York')+pd.Timedelta(hours=16)
        session=minutes.loc[(minutes.index>=start)&(minutes.index<end.tz_convert('UTC'))]
        # Raw fixed-point source is checked without calling the execution simulator.
        op=session.open.to_numpy(dtype=np.int64);hi=session.high.to_numpy(dtype=np.int64)
        lo=session.low.to_numpy(dtype=np.int64);cl=session.close.to_numpy(dtype=np.int64)
        scale=1_000_000_000
        entry=int(t['entry_price']*scale);stop=int(t['stop_price']*scale);target=int(t['target_price']*scale)
        long=t['direction']=='LONG'
        sh=(lo<=stop) if long else (hi>=stop);th=(hi>=target) if long else (lo<=target)
        hits=np.flatnonzero(sh|th)
        if len(hits):
            idx=int(hits[0]);reason='STOP' if sh[idx] else 'TARGET'
            px=(min(stop,op[idx]) if long else max(stop,op[idx])) if sh[idx] else target
        else:idx=len(session)-1;reason='SESSION_CLOSE';px=cl[idx]
        if idx<0:raise ValueError('No execution observations')
        actual_times=session.index[:idx+1]
        expected_times=pd.date_range(start,periods=idx+1,freq='min')
        if not actual_times.equals(expected_times):raise ValueError('Execution missing-minute integrity failed')
        if reason=='SESSION_CLOSE' and actual_times[-1]+pd.Timedelta(minutes=1)!=end:raise ValueError('Session close minute missing')
        expected_mfe=max(0,int(hi[:idx+1].max())-entry if long else entry-int(lo[:idx+1].min()))
        expected_mae=max(0,entry-int(lo[:idx+1].min()) if long else int(hi[:idx+1].max())-entry)
        sign=1 if long else -1
        if reason!=t['exit_reason'] or D(int(px))/scale!=t['exit_price']:raise ValueError('Independent fill mismatch')
        if session.index[idx]!=t['exit_bar_start_utc']:raise ValueError('Exit minute mismatch')
        if D(expected_mfe)/scale!=t['mfe_points'] or D(expected_mae)/scale!=t['mae_points']:raise ValueError('Excursion mismatch')
        if bool(sh[idx] and th[idx])!=t['same_minute_stop_target_conflict']:raise ValueError('Conflict mismatch')
        if (D(int(px))-entry)*sign/scale*2!=t['net_pnl_usd']:raise ValueError('Baseline P&L mismatch')
        checks+=1
    return {'independent_integer_execution_replay_trades':checks,
            'fills_excursions_pnl_match_independent_replay':True,'owned_execution_minutes_complete':True}
