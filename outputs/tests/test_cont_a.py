import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from decimal import Decimal as D
import copy
import tempfile
import unittest
import pandas as pd
import pyarrow.parquet as pq
import cont_a_backtest as m
import cont_a_metrics as metrics
from test_detect_fvgs import fixture
import detect_fvgs as det


def setup(direction='bullish',start='2024-02-05T14:30Z'):
    b=fixture(direction,start);f=det.detect(b)
    prices=[[108,112,106,110],[110,115,108,114]] if direction=='bullish' else [[102,105,98,99],[99,101,95,96]]
    rows=[]
    for i,px in enumerate(prices):
        t=b.timestamp_utc.iloc[-1]+(i+1)*m.FIVE
        rows.append({'timestamp_utc':t,'timestamp_ny':t.tz_convert('America/New_York'),
                     **{k:D(v) for k,v in zip(det.OHLC,px)},'is_complete_5m':True,'minute_count':5})
    return pd.concat([b,pd.DataFrame(rows)],ignore_index=True),f


def signal(direction='bullish'):
    b,f=setup(direction);s=m.signals(b,f)[0]
    return {**s,**m.levels(s,m.Config())}


def minutes(s,ohlc,at=None):
    ts=at if at is not None else s['entry_time_utc']
    return pd.DataFrame([{'ts_event':ts+i*m.ONE,**{k:D(str(v)) for k,v in zip(det.OHLC,px)}} for i,px in enumerate(ohlc)])


class ContATests(unittest.TestCase):
    def test_long_signal(self):
        b,f=setup();self.assertEqual(m.signals(b,f)[0]['direction'],'LONG')

    def test_short_signal(self):
        b,f=setup('bearish');self.assertEqual(m.signals(b,f)[0]['direction'],'SHORT')

    def test_wick_only_long_rejected(self):
        b,f=setup();b.loc[4,'close']=D(112)
        self.assertEqual(m.signals(b,f),[])

    def test_wick_only_short_rejected(self):
        b,f=setup('bearish');b.loc[4,'close']=D(98)
        self.assertEqual(m.signals(b,f),[])

    def test_first_touch_cancels_both(self):
        for d,c,p in [('bullish','low',105),('bearish','high',106)]:
            b,f=setup(d);b.loc[3,c]=D(p);self.assertEqual(m.signals(b,f),[])

    def test_second_touch_cancels_both(self):
        for d,c,p in [('bullish','low',105),('bearish','high',106)]:
            b,f=setup(d);b.loc[4,c]=D(p);self.assertEqual(m.signals(b,f),[])

    def test_missing_or_incomplete_bar_no_bridge(self):
        b,f=setup();self.assertEqual(m.signals(b.drop(index=3),f),[])
        b.loc[3,'is_complete_5m']=False;self.assertEqual(m.signals(b,f),[])

    def test_prior_date_rejected(self):
        b,f=setup();f.loc[0,'formation_date_ny']=pd.Timestamp('2024-02-04').date()
        self.assertEqual(m.signals(b,f),[])

    def test_1055_allowed_1100_not_allowed(self):
        for start,allowed in [('2024-02-05T15:35Z',True),('2024-02-05T15:40Z',False)]:
            b,f=setup(start=start);raw=m.signals(b,f)
            chosen,_,_=m.select(raw,{'2024-02-05'},m.Config())
            self.assertEqual(bool(chosen),allowed)
            if allowed:self.assertEqual(chosen[0]['entry_time_ny'].strftime('%H:%M'),'11:00')

    def test_one_trade_per_day(self):
        s=signal();later=copy.deepcopy(s);later['entry_time_utc']+=m.FIVE;later['fvg_id']='later'
        chosen,eligible,audit=m.select([later,s],{'2024-02-05'},m.Config())
        self.assertEqual(len(chosen),1);self.assertEqual(len(eligible),2)
        self.assertEqual(audit[1]['reason'],'DAILY_LOCK_COMPETING_SIGNAL')

    def test_tie_break_oldest_then_id(self):
        s=signal();a=copy.deepcopy(s);z=copy.deepcopy(s)
        a['fvg_id']='a';z['fvg_id']='z'
        chosen,_,_=m.select([z,a],{'2024-02-05'},m.Config());self.assertEqual(chosen[0]['fvg_id'],'a')
        z['formation_time_utc']-=m.FIVE
        chosen,_,_=m.select([a,z],{'2024-02-05'},m.Config());self.assertEqual(chosen[0]['fvg_id'],'z')

    def test_long_stop_target_and_risk(self):
        s=signal();self.assertEqual(s['stop_price'],D('105.75'))
        self.assertEqual(s['risk_points'],D('8.25'));self.assertEqual(s['target_price'],D('130.5'))

    def test_short_stop_target_and_risk(self):
        s=signal('bearish');self.assertEqual(s['stop_price'],D('105.25'))
        self.assertEqual(s['risk_points'],D('9.25'));self.assertEqual(s['target_price'],D('77.5'))

    def test_nonpositive_risk_skipped(self):
        s=signal();s['signal_close_price']=D(100)
        chosen,_,audit=m.select([s],{'2024-02-05'},m.Config())
        self.assertFalse(chosen);self.assertEqual(audit[0]['reason'],'NON_POSITIVE_RISK')

    def test_preentry_minute_excluded_entry_minute_included(self):
        s=signal();rows=minutes(s,[[114,200,50,114],[114,131,113,130]],s['entry_time_utc']-m.ONE)
        t=m.execute(s,rows,m.Config());self.assertEqual(t['exit_reason'],'TARGET')
        self.assertEqual(t['duration_1m_bars'],1);self.assertEqual(t['mfe_points'],D(17))

    def test_minute_stop_long(self):
        s=signal();t=m.execute(s,minutes(s,[[114,115,105,106]]),m.Config())
        self.assertEqual(t['exit_reason'],'STOP');self.assertEqual(t['exit_price'],s['stop_price'])

    def test_minute_target_long(self):
        s=signal();t=m.execute(s,minutes(s,[[114,131,113,130]]),m.Config())
        self.assertEqual(t['exit_reason'],'TARGET');self.assertEqual(t['exit_price'],s['target_price'])

    def test_minute_stop_short(self):
        s=signal('bearish');t=m.execute(s,minutes(s,[[96,106,95,105]]),m.Config())
        self.assertEqual(t['exit_reason'],'STOP')

    def test_minute_target_short(self):
        s=signal('bearish');t=m.execute(s,minutes(s,[[96,97,77,78]]),m.Config())
        self.assertEqual(t['exit_reason'],'TARGET')

    def test_same_minute_stop_priority(self):
        for d,px in [('bullish',[114,132,105,114]),('bearish',[96,106,77,96])]:
            s=signal(d);t=m.execute(s,minutes(s,[px]),m.Config())
            self.assertTrue(t['same_minute_stop_target_conflict']);self.assertEqual(t['exit_reason'],'STOP')
            self.assertGreaterEqual(t['mfe_r'],2)

    def test_session_close_and_final_minute_stop_priority(self):
        s=signal();start=s['entry_time_utc'];end=pd.Timestamp('2024-02-05T21:00Z')
        n=int((end-start)//m.ONE);rows=minutes(s,[[114,115,113,114]]*n)
        t=m.execute(s,rows,m.Config());self.assertEqual(t['exit_reason'],'SESSION_CLOSE')
        self.assertEqual(t['exit_time_ny'].strftime('%H:%M'),'16:00')
        rows.loc[n-1,'low']=D(100)
        self.assertEqual(m.execute(s,rows,m.Config())['exit_reason'],'STOP')

    def test_final_minute_target_before_close(self):
        s=signal();n=int((pd.Timestamp('2024-02-05T21:00Z')-s['entry_time_utc'])//m.ONE)
        rows=minutes(s,[[114,115,113,114]]*n);rows.loc[n-1,'high']=D(131)
        self.assertEqual(m.execute(s,rows,m.Config())['exit_reason'],'TARGET')

    def test_dollars_and_r(self):
        s=signal();t=m.execute(s,minutes(s,[[114,131,113,130]]),m.Config())
        self.assertEqual(t['pnl_points'],D('16.5'));self.assertEqual(t['pnl_usd'],D(33))
        self.assertEqual(t['result_r'],2);self.assertEqual(t['gross_pnl_usd'],t['net_pnl_usd'])

    def test_mfe_mae_long(self):
        s=signal();t=m.execute(s,minutes(s,[[114,120,110,118],[118,131,113,130]]),m.Config())
        self.assertEqual(t['mfe_points'],D(17));self.assertEqual(t['mae_points'],D(4))

    def test_mfe_mae_short(self):
        s=signal('bearish');t=m.execute(s,minutes(s,[[96,100,90,91],[91,95,77,78]]),m.Config())
        self.assertEqual(t['mfe_points'],D(19));self.assertEqual(t['mae_points'],D(4))

    def test_commission_and_slippage(self):
        b,f=setup();s=m.signals(b,f)[0];c=m.Config(D(1),1);s.update(m.levels(s,c))
        self.assertEqual(s['entry_price'],D('114.25'))
        t=m.execute(s,minutes(s,[[114,132,113,131]]),c)
        self.assertEqual(t['exit_price'],s['target_price']-D('.25'))
        self.assertEqual(t['gross_pnl_usd']-t['net_pnl_usd'],D(2))

    def test_adverse_gap_stop(self):
        s=signal();t=m.execute(s,minutes(s,[[104,105,103,104]]),m.Config())
        self.assertEqual(t['exit_price'],D(104));self.assertTrue(t['adverse_stop_gap'])

    def test_missing_owned_minute_fails_not_silent_skip(self):
        s=signal();rows=minutes(s,[[114,115,113,114],[114,115,113,114],[114,131,113,130]])
        with self.assertRaisesRegex(ValueError,'Missing'):m.execute(s,rows.drop(index=1),m.Config())

    def test_determinism_and_duplicate_protection(self):
        b,f=setup();a=m.signals(b,f);self.assertEqual(a,m.signals(b.sample(frac=1,random_state=2),f))
        with self.assertRaisesRegex(ValueError,'Duplicate'):m.signals(pd.concat([b,b.iloc[:1]]),f)
        s=signal();rows=minutes(s,[[114,131,113,130]])
        a=m.execute(s,rows,m.Config());self.assertEqual(a,m.execute(s,rows,m.Config()))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.parquet';q=Path(d)/'b.parquet';t=m.frame_table([a])
            pq.write_table(t,p);pq.write_table(t,q);self.assertEqual(p.read_bytes(),q.read_bytes())

    def test_no_holiday_or_halfday_or_carter_entries(self):
        dates,_=m.full_sessions()
        for d in ['2024-01-01','2024-07-04','2024-07-03','2024-11-29','2024-12-24','2025-01-09']:
            self.assertNotIn(d,dates)
        self.assertIn('2024-07-05',dates)
        s=signal();self.assertFalse(m.select([s],set(),m.Config())[0])

    def test_opening_exception(self):
        b,f=setup(start='2024-02-05T14:25Z');s=m.signals(b,f)[0]
        self.assertTrue(s['opening_exception']);self.assertEqual(s['entry_time_ny'].strftime('%H:%M'),'09:50')

    def test_no_strong_body_or_first_direction_filter(self):
        b,f=setup();b.loc[3,'open']=D(111);b.loc[3,'close']=D(108)
        b.loc[4,'open']=D('113.75')
        self.assertEqual(len(m.signals(b,f)),1)

    def test_future_prices_cannot_change_signal(self):
        b,f=setup();expected=m.signals(b,f)
        future=b.iloc[-1:].copy();future.timestamp_utc+=m.FIVE
        future.timestamp_ny=future.timestamp_utc.dt.tz_convert('America/New_York')
        for c in det.OHLC:future[c]=D(9999)
        self.assertEqual(expected,m.signals(pd.concat([b,future]),f))

    def test_drawdown_and_recovery(self):
        s=signal();t=m.execute(s,minutes(s,[[114,131,113,130]]),m.Config())
        trades=[]
        for i,p in enumerate([100,-50,-100,200]):
            v=dict(t);v.update(trade_id=str(i),net_pnl_usd=D(p),exit_time_utc=t['exit_time_utc']+i*pd.Timedelta(days=1))
            trades.append(v)
        dd,_=metrics.drawdown(trades)
        self.assertEqual(dd['max_closed_trade_drawdown_usd'],150)
        self.assertTrue(dd['peak_recovered']);self.assertEqual(dd['peak_equity_usd'],150)

    def test_tick_rounding(self):
        self.assertEqual(m.tick(D('100.12')),D(100))
        self.assertEqual(m.tick(D('100.13')),D('100.25'))

    def test_zero_range_ratio(self):
        row=pd.Series({'open':D(100),'high':D(100),'low':D(100),'close':D(100)})
        self.assertIsNone(m.ratio(row))


if __name__=='__main__':unittest.main()
