"""External-rationale, frozen two-policy follow-up; native no-target execution."""
import sys,json,hashlib
from pathlib import Path
from decimal import Decimal as D
import pandas as pd
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.simple_discovery.run import sha,storage
from engine.partial_execution import execute
from engine.position import PositionPlan,TargetLeg
from engine.legacy import reference as ref
from scripts.simple_search.report import metrics
from scripts.simple_discovery.report import block_evidence
from scripts.zone_reaction_backtest.report import table
P=ROOT/'work/simple-timing-followup-v1'
H=('LAST30_RTH','LAST30_OVERNIGHT')

def signal(g,previous_close):
    g=g.set_index(g.timestamp_utc.dt.tz_convert('America/New_York').dt.strftime('%H:%M'))
    morning=['09:30','09:35','09:40','09:45','09:50','09:55'];late=['15:00','15:05','15:10','15:15','15:20','15:25']
    if not set(morning+late).issubset(g.index):return []
    if not g.loc[morning+late,'is_complete_5m'].all():return []
    c=g.loc['15:25'];out=[]
    for name,reference in [(H[0],g.loc['09:30','open']),(H[1],previous_close)]:
        if reference is None:continue
        move=D(str(g.loc['09:55','close']))-D(str(reference))
        if not move:continue
        side='LONG' if move>0 else 'SHORT';at=c.timestamp_utc+pd.Timedelta(minutes=5)
        date=str(at.tz_convert('America/New_York').date())
        out.append(dict(hypothesis=name,date=date,year=int(date[:4]),direction=side,entry_time_utc=at,entry_time_ny=at.tz_convert('America/New_York'),close=c.close,stop_anchor=g.loc[late,'low'].min() if side=='LONG' else g.loc[late,'high'].max(),signal_id=hashlib.sha256(f'timing-v1|{name}|{at}'.encode()).hexdigest()))
    return out

def write(name,x):pd.DataFrame(x).to_csv(P/name,index=False,float_format='%.12g',lineterminator='\n')
def save(name,x):(P/name).write_text(json.dumps(x,sort_keys=True,indent=2,default=str,allow_nan=False)+'\n')
def main():
    if '--freeze' in sys.argv:
        files=['docs/SIMPLE_TIMING_FOLLOWUP_V1.md','scripts/simple_search/timing.py']
        v=dict(hashes={f:sha(ROOT/f) for f in files},status='PREREGISTERED_DEVELOPMENT_ONLY',family=20)
        p=P/'protocol.json'
        if p.exists():assert json.loads(p.read_text())==v
        else:save(p.name,v)
        return
    for f,h in json.loads((P/'protocol.json').read_text())['hashes'].items():assert sha(ROOT/f)==h
    before=storage();source=ROOT/'work/eight-level-reaction-entry-study-v1/source_identity.json';identity=json.loads(source.read_text())
    for f,h in identity['source_hashes'].items():assert sha(ROOT/f)==h
    lo=pd.Timestamp('2020-01-01',tz='America/New_York').tz_convert('UTC');hi=pd.Timestamp('2024-01-01',tz='America/New_York').tz_convert('UTC')
    frames={}
    for kind,key in [('bars','timestamp_utc'),('minutes','ts_event')]:
        g=pq.read_table(ROOT/'outputs/data'/identity['dataset']['files'][kind]['name'],filters=[(key,'>=',lo),(key,'<',hi)]).to_pandas()
        if key not in g:g=g.reset_index()
        assert g[key].between(lo,hi,inclusive='left').all() and g[key].is_unique
        if kind=='minutes':
            for c in ['open','high','low','close']:g[c]=g[c].map(lambda x:D(int(x)).scaleb(-9))
        g['date']=g[key].dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d');frames[kind]=g
    all_sessions={d:tuple(map(pd.Timestamp,v)) for d,v in identity['calendar']['sessions'].items() if '2020-01-01'<=d<'2024-01-01'}
    bars=frames['bars'];mins={}
    for d,g in frames['minutes'].groupby('date'):
        g=g.set_index('ts_event');g.index=g.index.as_unit('ns');mins[d]=g
    raw=[];dates=[];previous=None
    for date,(op,cl) in sorted(all_sessions.items()):
        g=bars[(bars.timestamp_utc>=op)&(bars.timestamp_utc<cl)]
        if cl-op==pd.Timedelta(minutes=390):
            dates.append(date);raw.extend(dict(**s,session_close=cl) for s in signal(g,previous))
        last=g[g.timestamp_utc==cl-pd.Timedelta(minutes=5)]
        previous=last.iloc[0].close if len(last)==1 and last.iloc[0].is_complete_5m else None
    assert len(dates)==1000
    write('raw_signals.csv',raw);records=[];daily=[];audit=[]
    for h in H:
        for ticks in [0,1,2]:
            by={s['date']:s for s in raw if s['hypothesis']==h}
            for date in dates:
                net=D(0);s=by.get(date);unknown=False
                if s:
                    sign=1 if s['direction']=='LONG' else -1
                    en=D(str(s['close']))+sign*D('.25')*ticks;stop=D(str(s['stop_anchor']))-sign*D('.25');risk=(en-stop)*sign
                    s=dict(**s,entry_price=en,stop_price=stop,risk_points=risk,risk_usd=risk*2,target_price=None)
                    if risk<=0:audit.append(dict(**s,ticks=ticks,status='NON_POSITIVE_RISK'))
                    else:
                        day=mins[date];ind=None
                        for at in pd.date_range(s['entry_time_utc'],s['session_close'],freq='min',inclusive='left'):
                            if at not in day.index:break
                            r=day.loc[at]
                            hit=r.low<=stop if sign==1 else r.high>=stop
                            if hit or at+pd.Timedelta(minutes=1)==s['session_close']:
                                price=(min(stop,r.open) if sign==1 else max(stop,r.open)) if hit else r.close
                                ind=(at+pd.Timedelta(minutes=1),price-sign*D('.25')*ticks,'STOP' if hit else 'SESSION_CLOSE');break
                        try:
                            tr,_=execute(s,day,ref.Config(D('.73'),ticks),1,PositionPlan(s['direction'],stop,D(2),legs=(TargetLeg(1,None),)),None,{},{},s['session_close'])
                        except ValueError as e:
                            assert 'Missing execution minute' in str(e) and ind is None;unknown=True
                            audit.append(dict(**s,ticks=ticks,status='EXECUTION_DATA_UNAVAILABLE'))
                        else:
                            assert ind==(tr['exit_time_utc'],tr['exit_price'],tr['exit_reason'])
                            assert tr['net_pnl_usd']==(ind[1]-en)*sign*2-D('1.46')
                            net=tr['net_pnl_usd'];tr.update(ticks=ticks,adverse_stop_gap=False)
                            records.append({k:v for k,v in tr.items() if k not in ['partial_execution_history','target_legs']});audit.append(dict(**s,ticks=ticks,status='TRADE_COMPLETE'))
                daily.append(dict(hypothesis=h,ticks=ticks,date=date,year=int(date[:4]),month=date[:7],net_pnl_usd=None if unknown else net,known_completed_net=net))
    write('trades.csv',records);write('daily.csv',daily);write('audit.csv',audit)
    d=pd.DataFrame(daily);t=pd.DataFrame(records)
    for c in ['net_pnl_usd','commission_usd','risk_points']:t[c]=t[c].astype(float)
    for c in ['net_pnl_usd','known_completed_net']:d[c]=d[c].astype(float)
    rows=[];years=[]
    for (h,k),g in d.groupby(['hypothesis','ticks']):
        tr=t[(t.hypothesis==h)&(t.ticks==k)];rows.append(dict(hypothesis=h,ticks=int(k),**metrics(g,tr)))
        for y,yg in g.groupby('year'):years.append(dict(hypothesis=h,ticks=int(k),year=int(y),**metrics(yg,tr[tr.year==y])))
    evidence=pd.read_csv(ROOT/'work/simple-strategy-unrestricted-v1/all_trial_evidence.csv').to_dict('records')
    # Replace CSV NaNs with explicit nulls before serializing.
    evidence=[{k:(None if pd.isna(v) else v) for k,v in e.items()} for e in evidence]
    for h in H:evidence.append(dict(policy=h,hypothesis=h,**block_evidence(d[(d.hypothesis==h)&(d.ticks==1)])))
    last=0
    for rank,i in enumerate(sorted(range(20),key=lambda i:evidence[i]['p_value'])):
        last=max(last,min(1,(20-rank)*evidence[i]['p_value']));evidence[i]['holm_p_20']=last
    write('summary.csv',rows);write('yearly.csv',years);write('all_trial_evidence.csv',evidence)
    gates=[]
    for h in H:
        r=next(x for x in rows if x['hypothesis']==h and x['ticks']==1);st=next(x for x in rows if x['hypothesis']==h and x['ticks']==2)
        ys=[x for x in years if x['hypothesis']==h and x['ticks']==1];ev=next(x for x in evidence if x['policy']==h);pos=[max(0,x['known_trade_net']) for x in ys]
        checks=dict(complete=r['complete'],positive_net=r['net_usd'] is not None and r['net_usd']>0,positive_r=r['avg_net_r']>0,pf=r['pf']>1,sample=r['trades']>=200 and r['dates']>=200,years=sum(x['complete'] and x['known_trade_net']>0 for x in ys)>=3,concentration=sum(pos)>0 and max(pos)/sum(pos)<=.5,top5=r['net_without_best_five_dates'] is not None and r['net_without_best_five_dates']>0,stress=st['complete'] and st['net_usd']>0,ci=ev['ci_low'] is not None and ev['ci_low']>0,adjusted_p=ev['holm_p_20']<.05)
        gates.append(dict(hypothesis=h,status='PROMISING_DEVELOPMENT_ONLY' if all(checks.values()) else 'DOES_NOT_QUALIFY',checks=checks))
    save('qualification.json',gates)
    (P/'REPORT.md').write_text('# Separate timing follow-up\n\nDEVELOPMENT_ONLY_NOT_VALIDATED. Native fixed-stop/session-close exits; one micro.\n\n'+table(rows,['hypothesis','ticks','trades','net_usd','pf','avg_net_r','max_dd','unknown_days'])+'\n\n'+table([x for x in years if x['ticks']==1],['hypothesis','year','trades','net_usd','pf','avg_net_r'])+'\n\n'+table([x for x in evidence if x['policy'] in H],['policy','ci_low','ci_high','p_value','holm_p_20'])+'\n\n```json\n'+json.dumps(gates,indent=2)+'\n```\n\n'+(ROOT/'docs/SIMPLE_TIMING_FOLLOWUP_V1.md').read_text())
    assert storage()==before
    for f,h in identity['source_hashes'].items():assert sha(ROOT/f)==h
    save('checks.json',dict(native_independent_trades=len(records),source_hashes=identity['source_hashes'],storage_metadata_sha256=before,validation_oos_read=False))
    hashes={p.name:sha(p) for p in sorted(P.iterdir()) if p.suffix in ['.json','.csv','.md'] and p.name not in ['first.json','manifest.json']}
    if (P/'first.json').exists():assert json.loads((P/'first.json').read_text())==hashes;save('manifest.json',dict(status='PASS',byte_identical_rerun=True,artifacts=hashes))
    else:save('first.json',hashes)
    print(gates)
if __name__=='__main__':main()
