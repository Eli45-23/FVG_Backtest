"""All registered policies, losses included; no post-outcome rule selection."""
import sys,json,html
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.simple_search.run import P,write,save
from scripts.simple_search.core import HYPOTHESES
from scripts.simple_discovery.report import block_evidence
from scripts.zone_reaction_backtest.report import table

def metrics(d,t):
    t=t.sort_values('entry_time_utc');n=len(t);v=t.net_pnl_usd
    eq=np.r_[0,v.cumsum()];dd=float((np.maximum.accumulate(eq)-eq).max())
    neg=-v[v<0].sum();complete=bool(d.net_pnl_usd.notna().all());pnl=float(v.sum())
    return dict(days=len(d),trades=n,dates=t.date.nunique(),unknown_days=int(d.net_pnl_usd.isna().sum()),complete=complete,
        net_usd=pnl if complete else None,known_trade_net=pnl,average_daily_net=float(d.net_pnl_usd.mean()) if complete else None,
        pf=float(v[v>0].sum()/neg) if neg else None,win_pct=float((v>0).mean()*100) if n else None,
        avg_net_r=float(t.result_r.mean()) if n else None,median_r=float(t.result_r.median()) if n else None,
        fees=float(t.commission_usd.sum()),max_dd=dd if complete else None,known_trade_dd=dd,
        worst_day=float(d.known_completed_net.min()),best_day=float(d.known_completed_net.max()),
        net_without_best_five_dates=float(d.known_completed_net.sum()-d.known_completed_net.nlargest(5).sum()) if complete else None,
        average_risk_points=float(t.risk_points.mean()) if n else None,max_risk_points=float(t.risk_points.max()) if n else None,
        same_minute_conflicts=int(t.same_minute_stop_target_conflict.sum()),adverse_stop_gaps=int(t.adverse_stop_gap.sum()))

def main():
    d=pd.read_csv(P/'daily.csv');t=pd.read_csv(P/'trades.csv');a=pd.read_csv(P/'signal_audit.csv');raw=pd.read_csv(P/'raw_signals.csv')
    rows=[];years=[];months=[];sides=[]
    for (h,k),g in d.groupby(['hypothesis','ticks']):
        tr=t[(t.hypothesis==h)&(t.ticks==k)]
        rows.append(dict(hypothesis=h,ticks=int(k),**metrics(g,tr)))
        for y,yg in g.groupby('year'):years.append(dict(hypothesis=h,ticks=int(k),year=int(y),**metrics(yg,tr[tr.year==y])))
        if k==1:
            for m,mg in g.groupby('month'):months.append(dict(hypothesis=h,month=m,**metrics(mg,tr[tr.date.str.startswith(m)])))
            for side,st in tr.groupby('direction'):
                loss=-st.loc[st.net_pnl_usd<0,'net_pnl_usd'].sum()
                sides.append(dict(hypothesis=h,direction=side,trades=len(st),net_usd=float(st.net_pnl_usd.sum()),avg_net_r=float(st.result_r.mean()),pf=float(st.loc[st.net_pnl_usd>0,'net_pnl_usd'].sum()/loss) if loss else None))
    write('summary.csv',rows);write('yearly.csv',years);write('monthly.csv',months);write('direction.csv',sides)
    evidence=pd.read_csv(ROOT/'work/simple-strategy-discovery-v2/combined_evidence.csv').drop(columns=['holm_p_six']).to_dict('records')
    for e in evidence:e['policy']='PREVIOUS_CAPPED_'+e['hypothesis']
    for h in HYPOTHESES:
        evidence.append(dict(policy='UNRESTRICTED_'+h,hypothesis=h,**block_evidence(d[(d.hypothesis==h)&(d.ticks==1)])))
    assert len(evidence)==18
    last=0
    for rank,i in enumerate(sorted(range(18),key=lambda i:evidence[i]['p_value'])):
        last=max(last,min(1,(18-rank)*evidence[i]['p_value']));evidence[i]['holm_p_18']=last
    write('all_trial_evidence.csv',evidence)
    gates=[]
    for h in HYPOTHESES:
        r=next(x for x in rows if x['hypothesis']==h and x['ticks']==1)
        stress=next(x for x in rows if x['hypothesis']==h and x['ticks']==2)
        yr=[x for x in years if x['hypothesis']==h and x['ticks']==1]
        ev=next(x for x in evidence if x['policy']=='UNRESTRICTED_'+h)
        pos=[max(0,x['known_trade_net']) for x in yr]
        checks=dict(complete=r['complete'],positive_net=r['net_usd'] is not None and r['net_usd']>0,
            positive_r=r['avg_net_r'] is not None and r['avg_net_r']>0,pf_above_one=r['pf'] is not None and r['pf']>1,
            sufficient_sample=r['trades']>=200 and r['dates']>=200,
            three_positive_years=sum(x['complete'] and x['known_trade_net']>0 for x in yr)>=3,
            no_year_dominance=sum(pos)>0 and max(pos)/sum(pos)<=.5,
            no_best_day_dependency=r['net_without_best_five_dates'] is not None and r['net_without_best_five_dates']>0,
            stress_positive=stress['complete'] and stress['net_usd'] is not None and stress['net_usd']>0,
            positive_ci=ev['ci_low'] is not None and ev['ci_low']>0,adjusted_significance=ev['holm_p_18']<.05)
        gates.append(dict(hypothesis=h,status='PROMISING_DEVELOPMENT_ONLY' if all(checks.values()) else 'DOES_NOT_QUALIFY',checks=checks))
    save('qualification.json',gates)
    write('signal_accounting.csv',a.groupby(['hypothesis','ticks','selection_status']).size().reset_index(name='signals'))
    write('signal_counts.csv',raw.groupby('hypothesis').agg(events=('signal_id','size'),dates=('date','nunique')).reset_index())
    primary=[r for r in rows if r['ticks']==1]
    passes=[g['hypothesis'] for g in gates if g['status']=='PROMISING_DEVELOPMENT_ONLY']
    answer='Development candidates passing the frozen screen: '+', '.join(passes) if passes else 'No policy passed the complete frozen screen. No validated strategy was found.'
    cols=['hypothesis','trades','dates','net_usd','known_trade_net','pf','avg_net_r','max_dd','unknown_days']
    text=['# Unrestricted simple MNQ strategy research',answer,
        '**DEVELOPMENT_ONLY_NOT_VALIDATED.** 2020–2023, one micro, repeated entries with one position at a time, $0.73/side and 1 adverse tick/side primary. No account, risk-budget, daily-profit or daily-trade-count constraint. Fixed original2R.',
        '\n## All twelve primary results',table(primary,cols),
        'Net and drawdown are unavailable for incomplete execution paths. Known completed-trade totals are partial and cannot establish total profitability. No unknown return is filled with zero.',
        '\n## Every year',table([r for r in years if r['ticks']==1],['hypothesis','year','trades','net_usd','known_trade_net','pf','avg_net_r','max_dd','unknown_days']),
        '\n## Direction, descriptive only',table(sides,['hypothesis','direction','trades','net_usd','pf','avg_net_r']),
        '\n## Stress and costs',table(rows,['hypothesis','ticks','trades','net_usd','pf','fees','same_minute_conflicts','adverse_stop_gaps','unknown_days']),
        '\n## Trial-aware evidence',table(evidence,['policy','ci_low','ci_high','p_value','holm_p_18','evidence_status']),
        'Confidence intervals use calendar-month blocks of all eligible daily returns. Holm includes18registered policies across the current and two prior searches; it cannot erase all prior Development inspection or quantify every historical research choice.',
        '\n## Predeclared gates','```json\n'+json.dumps(gates,indent=2)+'\n```',
        '\n## Frozen protocol',(ROOT/'docs/SIMPLE_UNRESTRICTED_SEARCH_V1.md').read_text(),
        '\n## Limits','A fixed stop does not guarantee its fill price. One-minute bars cannot establish intraminute order; stop-first assumptions apply. No margin or account feasibility is claimed. There is no independent unseen performance test in this search. Validation/OOS remain sealed. Do not turn a favorable subgroup into a strategy without a new frozen experiment. Missing execution prevents an unqualified result; original records are preserved. All failed policies remain in the trial ledger.']
    report='\n\n'.join(text)+'\n';(P/'REPORT.md').write_text(report)
    body=pd.DataFrame(primary)[cols].to_html(index=False,float_format=lambda x:f'{x:,.3f}')
    (P/'study.html').write_text('<!doctype html><meta charset="utf-8"><title>Unrestricted MNQ search</title><style>body{background:#111a24;color:#e4edf5;font:15px system-ui;margin:30px}table{border-collapse:collapse}td,th{border:1px solid #485969;padding:8px}pre{white-space:pre-wrap}</style><h1>Simple MNQ research — unrestricted</h1><p>'+html.escape(answer)+'</p><nav><a href="summary.csv" download>Summary CSV</a> · <a href="trades.csv" download>All trades CSV</a> · <a href="summary.json" download>Complete summary JSON</a> · <a href="yearly.csv" download>Yearly CSV</a></nav>'+body+'<pre>'+html.escape(report)+'</pre>')
    save('summary.json',dict(primary=primary,scenarios=rows,yearly=years,evidence=evidence,gates=gates))
    print(answer)
if __name__=='__main__':main()
