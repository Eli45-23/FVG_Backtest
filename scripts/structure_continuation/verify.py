"""Independent pivot reduction, no future eligibility, deterministic artifact check."""
import sys,json,hashlib,sqlite3
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.structure_continuation.run import P,sha,save

def independent(g):
    """Independent list reduction; never calls Structure or Detector."""
    window=[];high=low=None;broken=set();out=[];prev=None
    for b in g.itertuples():
        at=b.timestamp_utc
        if not b.is_complete_5m:
            window=[];high=low=None;broken=set();prev=None;continue
        if prev is not None and at-prev.timestamp_utc!=pd.Timedelta(minutes=5):
            window=[];high=low=None;broken=set();prev=None
        for side,level,pull,progress in [(1,high,low,'HL'),(-1,low,high,'LH')]:
            if level and (side,level['formed']) not in broken and (float(b.close)-level['price'])*side>0:
                broken.add((side,level['formed']))
                if (pull and pull['progress']==progress and level['formed']<pull['formed']
                    and max(level['known'],pull['known'])<=at and prev is not None
                    and (float(prev.close)-level['price'])*side<=0):
                    out.append((at+pd.Timedelta(minutes=5),'LONG' if side==1 else 'SHORT',level['price'],pull['price']))
        window=(window+[b])[-5:]
        if len(window)==5:
            p=window[2];others=window[:2]+window[3:]
            if all(p.high>x.high for x in others):
                high=dict(price=float(p.high),formed=p.timestamp_utc,known=at+pd.Timedelta(minutes=5),progress=None if high is None else 'HH' if p.high>high['price'] else 'LH' if p.high<high['price'] else 'EH')
            if all(p.low<x.low for x in others):
                low=dict(price=float(p.low),formed=p.timestamp_utc,known=at+pd.Timedelta(minutes=5),progress=None if low is None else 'HL' if p.low>low['price'] else 'LL' if p.low<low['price'] else 'EL')
        prev=b
    return out

def main():
    raw=pd.read_csv(P/'all_breakouts.csv');t=pd.read_csv(P/'all_scenario_trades.csv');a=pd.read_csv(P/'signal_audit.csv')
    bars=pd.read_parquet(P/'chart_bars.parquet')
    expected=[]
    for _,g in bars.groupby('date',sort=True):expected+=independent(g)
    actual=[(pd.Timestamp(r.entry_time_utc),r.direction,r.swing_price,r.pullback_price) for r in raw.itertuples()]
    assert expected==actual
    assert raw.signal_id.is_unique and raw.date.between('2020-01-01','2023-12-31').all()
    assert (pd.to_datetime(raw.pullback_available,utc=True)<=pd.to_datetime(raw.trigger_bar_start,utc=True)).all()
    assert len(a)==len(raw)*3
    for ticks,g in t.groupby('ticks'):
        assert g.signal_id.is_unique
        g=g.sort_values('entry_time_utc')
        starts=pd.to_datetime(g.entry_time_utc,utc=True).to_numpy();ends=pd.to_datetime(g.exit_time_utc,utc=True).to_numpy()
        assert (starts[1:]>=ends[:-1]).all()
        sign=g.direction.map({'LONG':1,'SHORT':-1})
        assert ((g.entry_price-g.stop_price)*sign==g.risk_points).all()
        assert ((g.target_price-g.entry_price)*sign==2*g.risk_points).all()
        assert ((g.stop_price*4)%1==0).all()
        assert ((g.net_pnl_usd-(g.gross_pnl_usd-1.46)).abs()<1e-8).all()
        assert g.reached_2r.eq(g.exit_reason.eq('TARGET')).all()
    con=sqlite3.connect('file:'+str(ROOT/'storage/app.db')+'?mode=ro',uri=True)
    queries={'runs':'id,status','event_studies':'id,status,config_hash','strategies':'id,current_version,updated_at','strategy_versions':'id,source_hash','variants':'id','schema_migrations':'version','research_splits':'id','experiment_snapshots':'id,snapshot_hash'}
    state={k:con.execute(f'SELECT {cols} FROM {k} ORDER BY 1').fetchall() for k,cols in queries.items()};state['reveals']=con.execute('SELECT * FROM event_study_reveals ORDER BY 1').fetchall()
    assert json.dumps(state,sort_keys=True,default=str)==(P/'storage_before.json').read_text()
    protocol=json.loads((P/'protocol.json').read_text())
    assert protocol['detector_sha256']==sha(ROOT/'scripts/structure_continuation/core.py')
    assert protocol['specification_sha256']==sha(ROOT/'docs/STRUCTURE_CONTINUATION_2R_V1.md')
    snapshots={f.name:sha(f) for f in P.iterdir() if f.suffix in ['.csv','.parquet','.html','.md','.json'] and f.name not in ['reproducibility_manifest.json','determinism_first.json']}
    prior=P/'determinism_first.json'
    if not prior.exists():
        prior.write_text(json.dumps(snapshots,sort_keys=True,indent=2)+'\n');print('First verification PASS; rerun execution and report before final manifest.');return
    assert json.loads(prior.read_text())==snapshots,'Nonidentical artifacts'
    save('reproducibility_manifest.json',dict(status='PASS',segment='development',performance_completeness='INCOMPLETE_EXECUTION',entry_records=len(raw),completed_primary_trades=int(t.ticks.eq(1).sum()),native_independent_checks=len(t),independent_signal_count=len(expected),byte_identical_rerun=True,storage_metadata_sha256=sha(P/'storage_before.json'),validation_oos_outcomes_read=False,production_execution_changed=False,code_hashes={str(f.relative_to(ROOT)):sha(f) for f in sorted((ROOT/'scripts/structure_continuation').glob('*')) if f.is_file()},artifacts={name:dict(sha256=h,bytes=(P/name).stat().st_size) for name,h in snapshots.items()}))
    print('PASS: independent signals, native fills, deterministic artifacts, preserved storage')
if __name__=='__main__':main()
