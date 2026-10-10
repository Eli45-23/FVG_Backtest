"""Independent vector signal checks plus unchanged full account verification."""
import sys,json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.simple_discovery import run,verify
from scripts.simple_discovery_v2.run import P

def independent(g):
    p,b,a=g.shift(1),g.shift(2),g.shift(3)
    ok=g.is_complete_5m & p.is_complete_5m.eq(True) & b.is_complete_5m.eq(True) & a.is_complete_5m.eq(True)
    for x,y in [(g,p),(p,b),(b,a)]:
        ok &= (x.timestamp_utc-y.timestamp_utc).eq(pd.Timedelta(minutes=5))
    low=pd.concat([a.low,b.low,p.low],axis=1).min(axis=1)
    high=pd.concat([a.high,b.high,p.high],axis=1).max(axis=1)
    masks={
        ('PULLBACK_RESUME','LONG'):(b.close>a.high)&(p.close<p.open)&(p.low>b.low)&(g.close>p.high),
        ('PULLBACK_RESUME','SHORT'):(b.close<a.low)&(p.close>p.open)&(p.high<b.high)&(g.close<p.low),
        ('RANGE_FAILURE','LONG'):(g.low<low)&(g.close>low)&(g.close<high)&(g.high<=high),
        ('RANGE_FAILURE','SHORT'):(g.high>high)&(g.close>low)&(g.close<high)&(g.low>=low),
        ('THREE_BAR_BREAK','LONG'):g.close>high,
        ('THREE_BAR_BREAK','SHORT'):g.close<low,
    }
    out=[]
    for (h,s),mask in masks.items():
        anchors=(pd.concat([p.low,g.low],axis=1).min(axis=1) if s=='LONG' else pd.concat([p.high,g.high],axis=1).max(axis=1)) if h=='PULLBACK_RESUME' else (g.low if s=='LONG' else g.high) if h=='RANGE_FAILURE' else low if s=='LONG' else high
        for i in g.index[ok & mask]:
            out.append((g.loc[i,'timestamp_utc']+pd.Timedelta(minutes=5),h,s,float(anchors.loc[i])))
    return out

if __name__=='__main__':
    run.P=P
    verify.P=P
    verify.independent=independent
    verify.main()
    path=P/'reproducibility_manifest.json'
    if path.exists():
        m=json.loads(path.read_text())
        m['code_hashes'].update({str(p.relative_to(ROOT)):run.sha(p) for p in (ROOT/'scripts/simple_discovery_v2').glob('*.py')})
        run.save(path.name,m)
