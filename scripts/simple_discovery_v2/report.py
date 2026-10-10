"""Full batch reporting with additive six-hypothesis evidence correction."""
import sys,json,html
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.simple_discovery.report import summary,block_evidence
from scripts.simple_discovery_v2.run import P
from scripts.simple_discovery_v2.core import HYPOTHESES
from scripts.zone_reaction_backtest.report import table

def write(name,x):
    pd.DataFrame(x).to_csv(P/name,index=False,float_format='%.12g',lineterminator='\n')
def save(name,x):
    (P/name).write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n')
def main():
    d=pd.read_csv(P/'daily.csv'); t=pd.read_csv(P/'trades.csv'); raw=pd.read_csv(P/'raw_signals.csv')
    rows=[]; years=[]
    for (h,k,m),g in d.groupby(['hypothesis','ticks','mode']):
        tr=t[(t.hypothesis==h)&(t.ticks==k)&(t['mode']==m)]
        rows.append(dict(hypothesis=h,ticks=int(k),mode=m,**summary(g,tr)))
        for y,yg in g.groupby('year'):
            years.append(dict(hypothesis=h,ticks=int(k),mode=m,year=int(y),**summary(yg,tr[tr.year==y])))
    write('scenario_summary.csv',rows);write('yearly.csv',years)
    previous=pd.read_csv(ROOT/'work/simple-strategy-discovery-v1/registered_evidence.csv').drop(columns=['holm_p']).to_dict('records')
    evidence=previous+[dict(hypothesis=h,**block_evidence(d[(d.hypothesis==h)&(d.ticks==1)&(d['mode']=='ONE_MICRO_DIAGNOSTIC')])) for h in HYPOTHESES]
    last=0
    for rank,i in enumerate(sorted(range(6),key=lambda i:evidence[i]['p_value'])):
        last=max(last,min(1,(6-rank)*evidence[i]['p_value'])); evidence[i]['holm_p_six']=last
    write('combined_evidence.csv',evidence)
    gates=[]
    for h in HYPOTHESES:
        r=next(x for x in rows if x['hypothesis']==h and x['ticks']==1 and x['mode']=='RISK_SIZED_200')
        ys=[x for x in years if x['hypothesis']==h and x['ticks']==1 and x['mode']=='RISK_SIZED_200']
        ev=next(x for x in evidence if x['hypothesis']==h)
        positive=[max(0,x['known_net_usd']) for x in ys]
        checks=dict(complete=r['complete'],positive_net=r['known_net_usd']>0,
            positive_r=r['avg_net_r'] is not None and r['avg_net_r']>0,
            pf_above_one=r['net_pf'] is not None and r['net_pf']>1,
            three_positive_years=sum(x['complete'] and x['known_net_usd']>0 for x in ys)>=3,
            no_year_dominance=sum(positive)>0 and max(positive)/sum(positive)<=.5,
            positive_ci=ev['ci_low'] is not None and ev['ci_low']>0,
            adjusted_evidence=ev['holm_p_six']<.05,no_margin_breach=r['margin_breaches']==0,no_lockout=r['lockout_days']==0)
        qualifies=all(checks.values())
        gates.append(dict(hypothesis=h,checks=checks,status='PROMISING_DEVELOPMENT_ONLY' if qualifies else 'DOES_NOT_QUALIFY',objective_met=qualifies and r['avg_daily_net']>=100))
    save('qualification.json',gates)
    write('signal_counts.csv',raw.groupby('hypothesis').agg(signals=('signal_id','size'),dates=('date','nunique')).reset_index())
    cols=['hypothesis','trades','known_net_usd','avg_daily_net','net_pf','avg_net_r','ending_balance','max_closed_dd','lockout_days']
    text=['# Simple strategy search — second batch','DEVELOPMENT_ONLY_NOT_VALIDATED. No tuning after results.']
    text+=['No new strategy passed the frozen evidence/account gate.' if not any(all(g['checks'].values()) for g in gates) else 'See qualification gates below; any pass is Development evidence only.']
    for mode in ['ONE_MICRO_DIAGNOSTIC','ONE_MICRO_200','RISK_SIZED_200']:
        text+=['\n## '+mode,table([x for x in rows if x['ticks']==1 and x['mode']==mode],cols)]
    text+=['\n## Every diagnostic year',table([x for x in years if x['ticks']==1 and x['mode']=='ONE_MICRO_DIAGNOSTIC'],['hypothesis','year','trades','known_net_usd','net_pf','avg_net_r']),
        '\n## Combined evidence across both batches',table(evidence,['hypothesis','ci_low','ci_high','p_value','holm_p_six']),
        '\nMonth-block bootstrap: mean net per all full sessions, 5,000 draws, seed1729. Six-hypothesis Holm correction. This does not correct for every historical research decision in this repository or make inspected Development data independent.',
        '\n## All cost and margin scenarios',table(rows,['hypothesis','mode','ticks','trades','known_net_usd','avg_daily_net','net_pf','lockout_days','unknown_days']),
        '\n## Frozen qualification checks','```json\n'+json.dumps(gates,indent=2)+'\n```',
        '\n## Method and limits',(ROOT/'docs/SIMPLE_STRATEGY_DISCOVERY_V2.md').read_text(),
        '\nThe diagnostic ignores capital restrictions and is not a feasible account result. Scenario profits must not be summed. $200 margin is an assumption, not broker approval. Actual losses can exceed planned stop losses. These three additional tests do not exhaust simple strategies. No Validation/OOS outcomes were queried; native engine unchanged. All raw outputs remain local and preserved separately from v1.']
    (P/'REPORT.md').write_text('\n\n'.join(text)+'\n')
    body=''.join('<h2>'+html.escape(mode)+'</h2>'+pd.DataFrame([x for x in rows if x['ticks']==1 and x['mode']==mode])[cols].to_html(index=False,float_format=lambda n:f'{n:,.2f}') for mode in ['ONE_MICRO_DIAGNOSTIC','ONE_MICRO_200','RISK_SIZED_200'])
    body+='<h2>Every Development year — one micro diagnostic</h2>'+pd.DataFrame([x for x in years if x['ticks']==1 and x['mode']=='ONE_MICRO_DIAGNOSTIC'])[['hypothesis','year','trades','known_net_usd','net_pf','avg_net_r']].to_html(index=False,float_format=lambda n:f'{n:,.3f}')
    (P/'study.html').write_text('<!doctype html><meta charset="utf-8"><title>Simple research: second batch</title><style>body{background:#111923;color:#e0e7ef;font:15px system-ui;margin:32px}table{border-collapse:collapse;font-size:13px}td,th{padding:9px;border:1px solid #425166}pre{white-space:pre-wrap}h2{margin-top:36px}</style><h1>Simple MNQ research — second batch</h1><p>2020–2023 only • 1,000 full sessions • $0.73 per side • 1 tick slippage per side • fixed 2R</p><p>'+html.escape(text[2])+'</p>'+body+'<h2>Complete report and limitations</h2><pre>'+html.escape('\n\n'.join(text))+'</pre>')
    save('summary.json',dict(scenarios=rows,yearly=years,evidence=evidence,gates=gates))
    print(json.dumps(gates))
if __name__=='__main__':main()
