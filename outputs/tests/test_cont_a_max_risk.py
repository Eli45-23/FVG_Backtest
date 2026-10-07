"""Controlled selection tests plus shared-execution and persistence invariants."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import copy
import json
import tempfile
import unittest
from decimal import Decimal as D
import pandas as pd
import pyarrow.parquet as pq
import cont_a_backtest as base
import cont_a_max_risk as variant
from test_cont_a import signal,minutes

DATES={'2024-02-05'}
def candidate(risk='20',offset=0,name='a',direction='bullish'):
    s=signal(direction)
    for k in ['entry_time_utc','entry_time_ny','formation_time_utc','formation_time_ny',
              'first_bar_time_utc','first_bar_time_ny','second_bar_time_utc','second_bar_time_ny']:
        s[k]+=offset*base.FIVE
    if direction=='bullish':s['signal_close_price']=s['first_bar_low']-base.TICK+D(risk)
    else:s['signal_close_price']=s['first_bar_high']+base.TICK-D(risk)
    s['fvg_id']=name;s['signal_id']=name+'@'+str(s['entry_time_utc'].value)
    s.update(base.levels(s,base.Config()))
    return s

class MaxRiskTests(unittest.TestCase):
    def test_9975_allowed(self):
        self.assertEqual(len(variant.select([candidate('99.75')],DATES)[0]),1)
    def test_100_rejected(self):
        self.assertEqual(variant.select([candidate('100')],DATES)[2][0]['reason'],'MAX_RISK_FILTER')
    def test_10025_rejected(self):
        self.assertFalse(variant.select([candidate('100.25')],DATES)[0])
    def test_rejected_does_not_lock(self):
        a=candidate('100');b=candidate('25',1,'b')
        chosen,_,audit,_=variant.select([a,b],DATES)
        self.assertEqual(chosen[0]['signal_id'],b['signal_id'])
        self.assertEqual([x['reason'] for x in audit],['MAX_RISK_FILTER','SELECTED'])
    def test_several_rejections_then_later_entry(self):
        raw=[candidate('100'),candidate('150',1,'b'),candidate('30',2,'c')]
        self.assertEqual(variant.select(raw,DATES)[0][0]['fvg_id'],'c')
    def test_earliest_eligible_wins(self):
        a=candidate();b=candidate('10',1,'b')
        chosen,_,audit,_=variant.select([b,a],DATES)
        self.assertEqual(chosen[0]['fvg_id'],'a');self.assertEqual(audit[-1]['reason'],'DAILY_LOCK_COMPETING_SIGNAL')
    def test_tie_breaking_preserved(self):
        a=candidate(name='a');z=candidate(name='z')
        self.assertEqual(variant.select([z,a],DATES)[0][0]['fvg_id'],'a')
        z['formation_time_utc']-=base.FIVE
        self.assertEqual(variant.select([a,z],DATES)[0][0]['fvg_id'],'z')
    def test_long_structural_risk_unchanged(self):
        s=signal();t=variant.select([s],DATES)[0][0]
        self.assertEqual(t['stop_price'],D('105.75'));self.assertEqual(t['risk_points'],D('8.25'))
    def test_short_structural_risk_unchanged(self):
        s=signal('bearish');t=variant.select([s],DATES)[0][0]
        self.assertEqual(t['stop_price'],D('105.25'));self.assertEqual(t['risk_points'],D('9.25'))
    def test_targets_unchanged_both_directions(self):
        for direction,target in [('bullish','130.5'),('bearish','77.5')]:
            self.assertEqual(variant.select([signal(direction)],DATES)[0][0]['target_price'],D(target))
    def test_no_management_after_favorable_excursion(self):
        s=variant.select([signal()],DATES)[0][0]
        rows=minutes(s,[[114,125,113,124],[124,125,105,106]])
        t=base.execute(s,rows,base.Config())
        self.assertEqual(t['exit_reason'],'STOP');self.assertEqual(t['exit_price'],s['stop_price']);self.assertEqual(t['result_r'],-1)
    def test_no_entry_after_cutoff(self):
        s=candidate();delta=pd.Timestamp('2024-02-05 11:00',tz='America/New_York')-s['second_bar_time_ny']
        for k in ['entry_time_utc','entry_time_ny','second_bar_time_utc','second_bar_time_ny']:s[k]+=delta
        self.assertEqual(variant.select([s],DATES)[2][0]['reason'],'TRIGGER_AT_OR_AFTER_1100')
    def test_1055_allowed(self):
        s=candidate();delta=pd.Timestamp('2024-02-05 10:55',tz='America/New_York')-s['second_bar_time_ny']
        for k in ['entry_time_utc','entry_time_ny','second_bar_time_utc','second_bar_time_ny']:s[k]+=delta
        t=variant.select([s],DATES)[0][0];self.assertEqual(t['entry_time_ny'].hour,11)
    def test_calendar_unchanged(self):
        self.assertEqual(variant.select([candidate()],set())[2][0]['reason'],'NOT_FULL_XNYS_SESSION')
    def test_repeat_selection_and_serialization(self):
        raw=[candidate('100'),candidate('20',1,'b'),candidate('10',2,'c')]
        a=variant.select(raw,DATES);self.assertEqual(a,variant.select(list(reversed(raw)),DATES))
        with tempfile.TemporaryDirectory() as d:
            tab=base.frame_table(a[0]);p=Path(d)/'a.parquet';q=Path(d)/'b.parquet'
            pq.write_table(tab,p);pq.write_table(tab,q);self.assertEqual(p.read_bytes(),q.read_bytes())
    def test_replacement_accounting(self):
        old=candidate('100');old['trade_id']='old'
        new=candidate('25',1,'new');new['trade_id']='new'
        old['net_pnl_usd']=D(-200)
        rep=variant.replacements([new],[old]);self.assertEqual(len(rep),1)
        self.assertEqual(rep[0]['rejected_baseline_trade_id'],'old')
    def test_cannot_filter_baseline_to_obtain_new_trade(self):
        raw=[candidate('100'),candidate('20',1,'later')]
        old=base.select(raw,DATES,base.Config())[0]
        historical=[t for t in old if t['risk_points']<100]
        true=variant.select(raw,DATES)[0]
        self.assertEqual(historical,[]);self.assertEqual(len(true),1)
    def test_risk_rejections_counted_even_after_lock(self):
        _,eligible,audit,pre=variant.select([candidate(),candidate('100',1,'b')],DATES)
        self.assertEqual(pre,2);self.assertEqual(len(eligible),1)
        self.assertEqual(audit[1]['reason'],'MAX_RISK_FILTER')
    def test_input_signals_not_mutated(self):
        raw=[candidate('100'),candidate('20',1,'b')];original=copy.deepcopy(raw)
        variant.select(raw,DATES);self.assertEqual(raw,original)
    def test_underwater_recovery_and_censoring(self):
        rows=[]
        for i,pnl in enumerate([100,-50,-25,100,-50]):
            rows.append({'entry_time_utc':pd.Timestamp('2024-01-01T14:00Z')+pd.Timedelta(days=i),
                         'exit_time_utc':pd.Timestamp('2024-01-01T15:00Z')+pd.Timedelta(days=i),'net_pnl_usd':D(pnl)})
        r=variant.underwater(rows);self.assertEqual(r['calendar_days'],3);self.assertTrue(r['recovered'])
    def test_protected_baseline_files_unchanged(self):
        # Local integration receipt from the actual run; portable test environments may lack market data.
        path=base.ROOT/'results/CONT_A_max_risk_100_summary.json'
        if not path.exists():self.skipTest('Actual-run results unavailable')
        receipt=json.loads(path.read_text())
        for name,digest in receipt['protected_sha256'].items():
            self.assertEqual(base.sha(base.ROOT/name),digest,name)
    def test_actual_trade_partition_and_execution_identity(self):
        path=base.ROOT/'results/CONT_A_max_risk_100_trades.parquet'
        if not path.exists():self.skipTest('Actual-run results unavailable')
        old=pq.read_table(base.ROOT/'results/CONT_A_second_candle_baseline_trades.parquet').to_pylist()
        new=pq.read_table(path).to_pylist();lookup={t['trade_id']:t for t in new}
        self.assertEqual(len(new),len({t['formation_date'] for t in new}))
        for t in old:
            if t['risk_points']<100:
                self.assertIn(t['trade_id'],lookup)
                for k,v in t.items():self.assertEqual(v,lookup[t['trade_id']][k],k)
        self.assertTrue(all(0<t['risk_points']<100 for t in new))
        self.assertGreater(len(new),sum(t['risk_points']<100 for t in old))

if __name__=='__main__':unittest.main()
