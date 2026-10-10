"""Independent vector detector and chronological position ledger checks."""
import sys,json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.simple_search.run import P,save
from scripts.simple_discovery.run import sha,storage
from scripts.simple_discovery.verify import independent as first
from scripts.simple_discovery_v2.verify import independent as second
NY='America/New_York'

def extra(g):
    out=[]
    # A separate vector formulation, split into complete contiguous segments.
    valid=g[g.is_complete_5m].copy()
    cuts=valid.timestamp_utc.diff().ne(pd.Timedelta(minutes=5)).cumsum()
    for _,q in valid.groupby(cuts):
        p=q.shift(1)
        ema=q.close.astype(float).ewm(span=20,adjust=False).mean()
        old=ema.shift(1)
        warm=pd.Series(range(1,len(q)+1),index=q.index)>=21
        low=q.low.shift(1).rolling(12).min();high=q.high.shift(1).rolling(12).max()
        masks={
            ('EMA20_CROSS','LONG'):warm&(p.close<=old)&(q.close>ema),
            ('EMA20_CROSS','SHORT'):warm&(p.close>=old)&(q.close<ema),
            ('EMA20_PULLBACK','LONG'):warm&(p.close>old)&(q.low<=old)&(q.close>ema)&(q.close>q.open)&(ema>old),
            ('EMA20_PULLBACK','SHORT'):warm&(p.close<old)&(q.high>=old)&(q.close<ema)&(q.close<q.open)&(ema<old),
            ('CHANNEL12_BREAK','LONG'):q.close>high,
            ('CHANNEL12_BREAK','SHORT'):q.close<low,
            ('CHANNEL12_RECLAIM','LONG'):(q.low<low)&(q.close>low)&(q.close<high)&(q.high<=high),
            ('CHANNEL12_RECLAIM','SHORT'):(q.high>high)&(q.close>low)&(q.close<high)&(q.low>=low),
        }
        for (h,s),mask in masks.items():
            anchor=(low if s=='LONG' else high) if h=='CHANNEL12_BREAK' else q.low if s=='LONG' else q.high
            for i in q.index[mask]:out.append((q.loc[i,'timestamp_utc']+pd.Timedelta(minutes=5),h,s,float(anchor.loc[i])))
    opening=g[g.timestamp_utc.dt.tz_convert(NY).dt.strftime('%H:%M').isin(['09:30','09:35','09:40'])]
    if len(opening)==3 and opening.is_complete_5m.all():
        o=opening.open.iloc[0];c=opening.close.iloc[-1]
        if c!=o:
            side='LONG' if c>o else 'SHORT'
            for h,s in [('OPEN_MOMENTUM_15',side),('OPEN_FADE_15','SHORT' if side=='LONG' else 'LONG')]:
                out.append((opening.timestamp_utc.iloc[-1]+pd.Timedelta(minutes=5),h,s,float(opening.low.min() if s=='LONG' else opening.high.max())))
    return out

def main():
    raw=pd.read_csv(P/'raw_signals.csv');t=pd.read_csv(P/'trades.csv');a=pd.read_csv(P/'signal_audit.csv');d=pd.read_csv(P/'daily.csv')
    bars=pd.read_parquet(P/'chart_bars.parquet');expected=[]
    for _,g in bars.groupby('date'):expected+=first(g)+second(g)+extra(g)
    actual=[(pd.Timestamp(r.entry_time_utc),r.hypothesis,r.direction,r.stop_anchor) for r in raw.itertuples()]
    assert sorted(expected)==sorted(actual),f'Signal mismatch: expected {len(expected)}, actual {len(actual)}; missing {set(expected)-set(actual)}; extra {set(actual)-set(expected)}'
    assert raw.signal_id.is_unique and raw.date.between('2020-01-01','2023-12-31').all()
    assert len(a)==3*len(raw)
    assert d.groupby(['hypothesis','ticks']).size().eq(1000).all()
    assert t.quantity.eq(1).all() and t.risk_points.gt(0).all()
    sign=t.direction.map({'LONG':1,'SHORT':-1})
    assert ((t.entry_price-t.close)*sign-.25*t.ticks).abs().lt(1e-8).all()
    assert ((t.stop_anchor-t.stop_price)*sign-.25).abs().lt(1e-8).all()
    assert ((t.entry_price-t.stop_price)*sign-t.risk_points).abs().lt(1e-8).all()
    assert ((t.target_price-t.entry_price)*sign-2*t.risk_points).abs().lt(1e-8).all()
    assert ((t.exit_price-t.entry_price)*sign*2-1.46-t.net_pnl_usd).abs().lt(1e-7).all()
    assert t.commission_usd.sub(1.46).abs().lt(1e-9).all()
    assert (pd.to_datetime(t.entry_time_utc,utc=True)==pd.to_datetime(t.trigger_start,utc=True)+pd.Timedelta(minutes=5)).all()
    assert (pd.to_datetime(t.exit_time_utc,utc=True)<=pd.to_datetime(t.session_close,utc=True)).all()
    lookup={(r.hypothesis,r.ticks,r.signal_id):r for r in t.itertuples()}
    for (h,k,date),g in a.groupby(['hypothesis','ticks','date']):
        flat=None;unknown=False;n=0;net=0
        for r in g.sort_values('entry_time_utc').itertuples():
            at=pd.Timestamp(r.entry_time_utc)
            if unknown:reason='POSITION_STATE_UNKNOWN'
            elif flat is not None and at<flat:reason='POSITION_OPEN'
            elif at>=pd.Timestamp(r.session_close):reason='AT_SESSION_CLOSE'
            elif r.risk_points<=0:reason='NON_POSITIVE_RISK'
            else:reason=None
            if reason:assert r.selection_status==reason;continue
            n+=1
            if r.selection_status=='EXECUTION_DATA_UNAVAILABLE':
                unknown=True;assert pd.Timestamp(r.first_missing_owned_minute)>=at;continue
            assert r.selection_status=='TRADE_COMPLETE'
            tr=lookup[(h,k,r.signal_id)];flat=pd.Timestamp(tr.exit_time_utc);net+=tr.net_pnl_usd
        day=d[(d.hypothesis==h)&(d.ticks==k)&(d.date==date)].iloc[0]
        assert day.selected==n and abs(day.known_completed_net-net)<1e-7
        assert pd.isna(day.net_pnl_usd)==unknown
    v=json.loads((P/'execution_verification.json').read_text());assert storage()==v['storage_metadata_sha256']
    for f,h in v['source_hashes'].items():assert sha(ROOT/f)==h
    for f,h in json.loads((P/'protocol.json').read_text())['hashes'].items():assert sha(ROOT/f)==h
    files={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(P.iterdir()) if p.suffix in ['.json','.csv','.md','.html','.parquet'] and p.name not in ['reproducibility_manifest.json','determinism_first.json']}
    fp=P/'determinism_first.json'
    if not fp.exists():save(fp.name,files);print('First independent verification passed; repeat.');return
    assert json.loads(fp.read_text())==files,'Artifact determinism mismatch'
    save('reproducibility_manifest.json',dict(status='PASS',segment='development',raw_signals=len(raw),completed_scenario_trades=len(t),native_checks=v['independent_native_fill_checks'],byte_identical_rerun=True,validation_oos_outcomes_read=False,storage_metadata_sha256=storage(),artifacts=files,code_hashes={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'scripts/simple_search').glob('*.py')}))
    print('PASS: independent signals, position selection, native fills, byte-identical repeat, preserved sources/storage')
if __name__=='__main__':main()
