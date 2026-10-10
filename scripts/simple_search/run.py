"""All frozen policies, chronological one-position execution; unchanged native fills."""
import sys,json
from pathlib import Path
from decimal import Decimal as D
import pandas as pd
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.simple_search.core import Detector,HYPOTHESES,bracket,NY
from scripts.simple_discovery.run import sha,storage
from scripts.swing_low_feasibility.core import independent_fill
from scripts.pml_feasibility.core import short_fill
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref
P=ROOT/'work/simple-strategy-unrestricted-v1'
SOURCE=ROOT/'work/eight-level-reaction-entry-study-v1'

def write(name,rows):
    (rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)).to_csv(P/name,index=False,float_format='%.12g',lineterminator='\n')
def save(name,obj):
    (P/name).write_text(json.dumps(obj,sort_keys=True,indent=2,default=str,allow_nan=False)+'\n')

def main():
    protocol=json.loads((P/'protocol.json').read_text())
    for f,h in protocol['hashes'].items():assert sha(ROOT/f)==h
    before=storage()
    identity=json.loads((SOURCE/'source_identity.json').read_text())
    manifest=json.loads((SOURCE/'reproducibility_manifest.json').read_text())
    assert manifest['segment']=='development' and manifest['status']=='PASS'
    assert sha(SOURCE/'source_identity.json')==manifest['artifacts']['source_identity.json']['sha256']
    for f,h in identity['source_hashes'].items():assert sha(ROOT/f)==h
    frames={};lo=pd.Timestamp('2020-01-01',tz=NY).tz_convert('UTC');hi=pd.Timestamp('2024-01-01',tz=NY).tz_convert('UTC')
    for kind,key in [('bars','timestamp_utc'),('minutes','ts_event')]:
        path=ROOT/'outputs/data'/identity['dataset']['files'][kind]['name']
        g=pq.read_table(path,filters=[(key,'>=',lo),(key,'<',hi)]).to_pandas()
        if key not in g:g=g.reset_index()
        assert g[key].is_unique and g[key].between(lo,hi,inclusive='left').all()
        if kind=='minutes':
            for c in ['open','high','low','close']:g[c]=g[c].map(lambda x:D(int(x)).scaleb(-9))
        g['date']=g[key].dt.tz_convert(NY).dt.strftime('%Y-%m-%d')
        frames[kind]=g.sort_values(key)
    days={}
    for date,g in frames['minutes'].groupby('date'):
        g=g.set_index('ts_event');g.index=g.index.as_unit('ns');days[date]=g
    sessions={d:tuple(map(pd.Timestamp,v)) for d,v in identity['calendar']['sessions'].items() if '2020-01-01'<=d<'2024-01-01' and pd.Timestamp(v[1])-pd.Timestamp(v[0])==pd.Timedelta(minutes=390)}
    bar_days=dict(tuple(frames['bars'].groupby('date')))
    signals=[];chart=[]
    for date,(op,cl) in sorted(sessions.items()):
        g=bar_days.get(date,frames['bars'].iloc[:0]);g=g[(g.timestamp_utc>=op)&(g.timestamp_utc<cl)]
        detector=Detector()
        for b in g.itertuples(): signals.extend(dict(**s,session_close=cl) for s in detector.update(b))
        chart.extend(g.to_dict('records'))
    assert len({s['signal_id'] for s in signals})==len(signals)
    write('raw_signals.csv',signals);pd.DataFrame(chart).to_parquet(P/'chart_bars.parquet',index=False)
    by={}
    for s in signals:by.setdefault((s['hypothesis'],s['date']),[]).append(s)
    print('SIGNALS',pd.DataFrame(signals).hypothesis.value_counts().to_dict(),flush=True)
    cache={};check=0
    def fill(s,b,ticks):
        nonlocal check
        at=s['entry_time_utc'];end=s['session_close'];day=days[s['date']]
        key=(at,s['direction'],b['entry_price'],b['stop_price'],b['target_price'],ticks)
        if key in cache:return cache[key]
        ix=pd.date_range(at,end,freq='min',inclusive='left');missing=ix.difference(day.index)
        cutoff=missing[0] if len(missing) else end
        arr=day.loc[(day.index>=at)&(day.index<cutoff),['open','high','low','close']].to_numpy(float)
        ind=(independent_fill if s['direction']=='LONG' else short_fill)(arr,float(b['entry_price']),float(b['stop_price']),float(b['target_price']),ticks,len(ix))
        try:
            native,_=execute(dict(**s,**b),day,ref.Config(D('.73'),ticks),1,Entry(s['direction'],b['stop_price'],D(2)),None,{},{},end)
        except ValueError as e:
            assert 'Missing execution minute' in str(e) and ind is None
            result=dict(status='EXECUTION_DATA_UNAVAILABLE',first_missing_owned_minute=cutoff)
            cache[key]=result;return result
        assert ind is not None
        i,reason,price,conflict=ind
        sign=1 if s['direction']=='LONG' else -1
        assert native['exit_reason']==reason and float(native['exit_price'])==price
        assert native['exit_time_utc']==at+pd.Timedelta(minutes=i+1)
        assert native['same_minute_stop_target_conflict']==conflict
        assert native['net_pnl_usd']==(D(str(price))-b['entry_price'])*sign*2-D('1.46')
        assert native['management_event_count']==0 and native['final_stop_price']==b['stop_price']
        result={k:native[k] for k in ['exit_time_utc','exit_time_ny','exit_reason','exit_price','gross_pnl_usd','commission_usd','net_pnl_usd','result_r','mfe_points','mae_points','mfe_r','mae_r','duration_minutes','same_minute_stop_target_conflict']}
        result.update(status='COMPLETE',adverse_stop_gap=reason=='STOP' and (arr[i,0]<float(b['stop_price']) if sign==1 else arr[i,0]>float(b['stop_price'])))
        cache[key]=result;check+=1;return result
    audits=[];trades=[];daily=[]
    for hyp in HYPOTHESES:
        for ticks in [0,1,2]:
            for date,(op,cl) in sorted(sessions.items()):
                flat=op;unknown=False;net=D(0);n=0
                for s in by.get((hyp,date),[]):
                    b=bracket(s,ticks);record=dict(**s,**b,ticks=ticks)
                    at=s['entry_time_utc']
                    if unknown:reason='POSITION_STATE_UNKNOWN'
                    elif at<flat:reason='POSITION_OPEN'
                    elif at>=cl:reason='AT_SESSION_CLOSE'
                    elif b['risk_points']<=0:reason='NON_POSITIVE_RISK'
                    else:reason=None
                    if reason:
                        audits.append(dict(**record,selection_status=reason));continue
                    n+=1;f=fill(s,b,ticks)
                    if f['status']!='COMPLETE':
                        unknown=True
                        audits.append(dict(**record,selection_status=f['status'],first_missing_owned_minute=f['first_missing_owned_minute']))
                        continue
                    flat=f['exit_time_utc'];net+=f['net_pnl_usd']
                    trades.append(dict(**record,quantity=1,**{k:v for k,v in f.items() if k!='status'}))
                    audits.append(dict(**record,selection_status='TRADE_COMPLETE'))
                daily.append(dict(hypothesis=hyp,ticks=ticks,date=date,year=int(date[:4]),month=date[:7],selected=n,status='UNKNOWN' if unknown else 'COMPLETE',net_pnl_usd=None if unknown else net,known_completed_net=net))
            print(hyp,ticks,'completed',sum(t['hypothesis']==hyp and t['ticks']==ticks for t in trades),flush=True)
    write('trades.csv',trades);write('signal_audit.csv',audits);write('daily.csv',daily)
    for f,h in identity['source_hashes'].items():assert sha(ROOT/f)==h
    assert storage()==before
    save('execution_verification.json',dict(source_hashes=identity['source_hashes'],storage_metadata_sha256=before,raw_signals=len(signals),independent_native_fill_checks=check,full_sessions=len(sessions),validation_oos_outcomes_read=False,production_execution_changed=False))
if __name__=='__main__':main()
