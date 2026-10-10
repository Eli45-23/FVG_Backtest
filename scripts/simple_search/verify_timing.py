"""Artifact-level invariants and independent signal reconstruction for timing test."""
import sys,json
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.simple_discovery.run import sha,storage
P=ROOT/'work/simple-timing-followup-v1'

def main():
    t=pd.read_csv(P/'trades.csv');d=pd.read_csv(P/'daily.csv');raw=pd.read_csv(P/'raw_signals.csv')
    ident=json.loads((ROOT/'work/eight-level-reaction-entry-study-v1/source_identity.json').read_text())
    lo=pd.Timestamp('2020-01-01',tz='America/New_York').tz_convert('UTC');hi=pd.Timestamp('2024-01-01',tz='America/New_York').tz_convert('UTC')
    b=pq.read_table(ROOT/'outputs/data'/ident['dataset']['files']['bars']['name'],filters=[('timestamp_utc','>=',lo),('timestamp_utc','<',hi)]).to_pandas()
    if 'timestamp_utc' not in b:b=b.reset_index()
    expected=[];previous=None
    for date,pair in sorted(ident['calendar']['sessions'].items()):
        if not '2020-01-01'<=date<'2024-01-01':continue
        op,cl=map(pd.Timestamp,pair);g=b[(b.timestamp_utc>=op)&(b.timestamp_utc<cl)].set_index('timestamp_utc')
        if cl-op==pd.Timedelta(minutes=390):
            morning=pd.date_range(op,periods=6,freq='5min');late=pd.date_range(cl-pd.Timedelta(minutes=60),periods=6,freq='5min')
            ix=morning.union(late)
            if ix.isin(g.index).all() and g.loc[ix,'is_complete_5m'].all():
                for name,v in [('LAST30_RTH',g.loc[op,'open']),('LAST30_OVERNIGHT',previous)]:
                    if v is None:continue
                    diff=g.loc[morning[-1],'close']-v
                    if diff:expected.append((name,date,'LONG' if diff>0 else 'SHORT',float(g.loc[late,'low'].min() if diff>0 else g.loc[late,'high'].max())))
        last=cl-pd.Timedelta(minutes=5);previous=g.loc[last,'close'] if last in g.index and g.loc[last,'is_complete_5m'] else None
    actual=[(r.hypothesis,r.date,r.direction,r.stop_anchor) for r in raw.itertuples()]
    assert sorted(actual)==sorted(expected) and raw.signal_id.is_unique
    assert d.groupby(['hypothesis','ticks']).size().eq(1000).all()
    assert t.groupby(['hypothesis','ticks','date']).size().eq(1).all()
    assert t.target_price.isna().all() and t.management_event_count.eq(0).all()
    assert pd.to_datetime(t.entry_time_ny,utc=True).dt.tz_convert('America/New_York').dt.strftime('%H:%M').eq('15:30').all()
    assert (pd.to_datetime(t.exit_time_utc,utc=True)<=pd.to_datetime(t.session_close,utc=True)).all()
    s=t.direction.map({'LONG':1,'SHORT':-1})
    assert ((t.exit_price-t.entry_price)*s*2-1.46-t.net_pnl_usd).abs().lt(1e-7).all()
    gap=t.exit_reason.eq('STOP') & (t.exit_price+s*t.ticks*.25-t.stop_price).abs().gt(1e-8)
    assert gap.eq(t.adverse_stop_gap).all()
    for (h,k),g in t.groupby(['hypothesis','ticks']):
        days=d[(d.hypothesis==h)&(d.ticks==k)];assert abs(g.net_pnl_usd.sum()-days.net_pnl_usd.sum())<1e-7
    checks=json.loads((P/'checks.json').read_text());assert checks['storage_metadata_sha256']==storage()
    for f,h in checks['source_hashes'].items():assert sha(ROOT/f)==h
    assert json.loads((P/'manifest.json').read_text())['byte_identical_rerun']
    print('PASS timing: exact independent signals, fees, no target/management, position timing, zero stop gaps, preserved sources/storage, exact rerun')
if __name__=='__main__':main()
