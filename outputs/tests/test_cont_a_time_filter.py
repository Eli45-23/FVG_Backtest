import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest,json,tempfile
from decimal import Decimal as D
import pandas as pd
import pyarrow.parquet as pq
import cont_a_time_filter as v
import cont_a_backtest as base
import cont_a_max_risk as control
from test_cont_a_max_risk import candidate,DATES
from test_cont_a import signal,minutes

def at(clock,risk='20',name='a'):
    s=candidate(risk,name=name)
    delta=pd.Timestamp('2024-02-05 '+clock,tz='America/New_York')-s['second_bar_time_ny']
    for k in ['entry_time_utc','entry_time_ny','formation_time_utc','formation_time_ny','first_bar_time_utc','first_bar_time_ny','second_bar_time_utc','second_bar_time_ny']:s[k]+=delta
    s['signal_id']=name+'@'+str(s['entry_time_utc'].value)
    return s

class TimeFilterTests(unittest.TestCase):
    def test_0955_allowed(self):self.assertEqual(len(v.select([at('09:55')],DATES)[0]),1)
    def test_1000_rejected(self):self.assertEqual(v.select([at('10:00')],DATES)[2][0]['reason'],'TIME_WINDOW_FILTER')
    def test_1025_rejected(self):self.assertFalse(v.select([at('10:25')],DATES)[0])
    def test_1030_allowed(self):self.assertEqual(len(v.select([at('10:30')],DATES)[0]),1)
    def test_rejected_does_not_lock(self):
        raw=[at('10:00'),at('10:30',name='b')];t,_,a,_=v.select(raw,DATES)
        self.assertEqual(t[0]['fvg_id'],'b');self.assertEqual([x['reason'] for x in a],['TIME_WINDOW_FILTER','SELECTED'])
    def test_later_signal_replaces(self):
        raw=[at('10:10'),at('10:35',name='b')]
        self.assertEqual(v.select(raw,DATES)[0][0]['fvg_id'],'b')
        self.assertEqual(control.select(raw,DATES)[0][0]['fvg_id'],'a')
    def test_earlier_allowed_locks(self):
        t,_,a,_=v.select([at('09:55'),at('10:00',name='b'),at('10:30',name='c')],DATES)
        self.assertEqual(t[0]['fvg_id'],'a');self.assertEqual(a[-1]['reason'],'DAILY_LOCK_COMPETING_SIGNAL')
    def test_risk_priority_unchanged(self):self.assertEqual(v.select([at('10:00','100')],DATES)[2][0]['reason'],'MAX_RISK_FILTER')
    def test_risk_9975(self):self.assertEqual(len(v.select([at('10:30','99.75')],DATES)[0]),1)
    def test_risk_100(self):self.assertFalse(v.select([at('10:30','100')],DATES)[0])
    def test_structural_stop_unchanged(self):
        for d in ['bullish','bearish']:
            s=signal(d);t=v.select([s],DATES)[0][0]
            self.assertEqual(t['stop_price'],base.levels(s,base.Config())['stop_price'])
    def test_2r_unchanged(self):
        for d in ['bullish','bearish']:
            t=v.select([signal(d)],DATES)[0][0];self.assertEqual(abs(t['target_price']-t['entry_price']),2*t['risk_points'])
    def test_execution_identical(self):
        s=signal();chosen=v.select([s],DATES)[0][0];rows=minutes(s,[[114,125,113,124],[124,125,105,106]])
        self.assertEqual(base.execute(chosen,rows,base.Config()),base.execute(s,rows,base.Config()))
        self.assertEqual(base.execute(chosen,rows,base.Config())['result_r'],-1)
    def test_cutoff_preserved(self):
        self.assertTrue(v.select([at('10:55')],DATES)[0]);self.assertFalse(v.select([at('11:00')],DATES)[0])
    def test_calendar_preserved(self):self.assertFalse(v.select([at('09:55')],set())[0])
    def test_deterministic_order_and_bytes(self):
        raw=[at('10:00'),at('10:30',name='b'),at('10:35',name='c')]
        result=v.select(raw,DATES);self.assertEqual(result,v.select(list(reversed(raw)),DATES))
        with tempfile.TemporaryDirectory() as root:
            a=Path(root)/'a';b=Path(root)/'b';tab=base.frame_table(result[0]);pq.write_table(tab,a);pq.write_table(tab,b);self.assertEqual(a.read_bytes(),b.read_bytes())
    def test_replacement_audit(self):
        old=at('10:00');new=at('10:30',name='b');old['net_pnl_usd']=D(-40)
        r=v.replacements([new],[old]);self.assertEqual(len(r),1);self.assertEqual(r[0]['rejected_trigger_time_ny'],old['second_bar_time_ny'])
    def test_identical_trade_not_replacement(self):
        s=at('09:55');self.assertEqual(v.replacements([s],[s]),[])
    def test_actual_receipt_and_partition(self):
        p=base.ROOT/'results'/f'{v.STEM}_summary.json'
        if not p.exists():self.skipTest('Local full-run receipt unavailable')
        r=json.loads(p.read_text())
        for name,h in r['protected_sha256'].items():self.assertEqual(base.sha(base.ROOT/name),h,name)
        a=r['signal_accounting'];self.assertEqual(a['final_eligible_signals'],a['actual_trades']+a['competing_after_actual_entry'])
        self.assertEqual(a['time_filter_replacement_days'],r['comparison']['replacement_trades']['trades'])
        trades=pq.read_table(base.ROOT/'results'/f'{v.STEM}_trades.parquet').to_pylist()
        self.assertTrue(all(not v.banned(t) and t['risk_points']<100 for t in trades))
        self.assertEqual(len(trades),len({t['formation_date'] for t in trades}))
        audit=pd.read_csv(base.ROOT/'results'/f'{v.STEM}_signal_audit.csv')
        rejected=pd.to_datetime(audit.loc[audit.reason=='TIME_WINDOW_FILTER','entry_time_utc'],utc=True)
        days={t['formation_date'] for t in trades if any(x.tz_convert('America/New_York').date()==t['formation_date'] and x<t['entry_time_utc'] for x in rejected)}
        self.assertEqual(len(days),a['time_filter_replacement_days'])

if __name__=='__main__':unittest.main()
