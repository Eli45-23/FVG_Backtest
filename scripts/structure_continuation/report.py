"""Read-only aggregate report; no parameter selection or market source reads."""
import sys,json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.structure_continuation.run import P,write,save
from scripts.structure_continuation.core import BINS
from scripts.opening15_breakout.report import stats,cluster_intervals
from scripts.zone_reaction_backtest.report import table

def main():
    t=pd.read_csv(P/'all_scenario_trades.csv'); a=pd.read_csv(P/'signal_audit.csv'); raw=pd.read_csv(P/'all_breakouts.csv')
    p=t[t.ticks==1].copy();p['month']=p.date.str[:7]
    costs=[]
    for k,g in t.groupby('ticks'):
        costs.append(dict(ticks=int(k),**stats(g),**{str(x):int(y) for x,y in a[a.ticks==k].selection_status.value_counts().items()}))
    write('cost_sensitivity.csv',costs)
    groups={}
    for name,cols in [('yearly',['year']),('direction',['direction']),('yearly_direction',['year','direction']),('monthly',['month']),('time_yearly',['time_bucket','year','direction'])]:
        groups[name]=[dict(zip(cols,key if isinstance(key,tuple) else (key,)),**stats(g)) for key,g in p.groupby(cols)]
        write(name+'.csv',groups[name])
    timing=[]
    for side in ['ALL','LONG','SHORT']:
        for w in BINS:
            g=p[(p.time_bucket==w)&((p.direction==side) if side!='ALL' else True)]
            ar=a[(a.ticks==1)&(a.time_bucket==w)&((a.direction==side) if side!='ALL' else True)]
            annual=g.groupby('year').agg(net=('net_pnl_usd','sum'),r=('result_r','mean'))
            timing.append(dict(direction=side,time_bucket=w,raw_breakouts=len(ar),position_open_skips=int(ar.selection_status.eq('POSITION_OPEN').sum()),**stats(g),**cluster_intervals(g),positive_dollar_years=int((annual.net>0).sum()),positive_r_years=int((annual.r>0).sum())))
    write('time_of_day.csv',timing)
    moves=[]
    for side in ['ALL','LONG','SHORT']:
        g=p if side=='ALL' else p[p.direction==side]
        for r in [.5,1,1.5,2]:
            key=str(r).replace('.','p');h=g['reached_'+key+'r'];amb=g['ambiguous_'+key+'r']
            moves.append(dict(direction=side,threshold_r=r,trades=len(g),reached=int(h.sum()),reached_pct=float(h.mean()*100) if len(g) else None,ambiguous=int(amb.sum())))
    write('milestones.csv',moves)
    excursions=[]
    for side in ['ALL','LONG','SHORT']:
        g=p if side=='ALL' else p[p.direction==side]
        v=dict(direction=side,trades=len(g))
        for field in ['mfe_points','mae_points','mfe_r','mae_r','risk_points','conservative_max_r']:
            for q,name in [(0,'min'),(.25,'q25'),(.5,'median'),(.75,'q75'),(.9,'q90'),(1,'max')]:v[field+'_'+name]=float(g[field].quantile(q)) if len(g) else None
            v[field+'_mean']=float(g[field].mean()) if len(g) else None
        excursions.append(v)
    write('excursions_risk.csv',excursions)
    p=p.sort_values(['entry_time_utc','signal_id']);eq=p[['signal_id','exit_time_ny','net_pnl_usd','result_r']].copy()
    eq['equity_usd']=p.net_pnl_usd.cumsum();eq['drawdown_usd']=eq.equity_usd.cummax().clip(lower=0)-eq.equity_usd;write('equity.csv',eq)
    summary=dict(status='DEVELOPMENT_ONLY_NOT_VALIDATED',segment='development',raw_breakouts=len(raw),raw_dates=raw.date.nunique(),primary=next(x for x in costs if x['ticks']==1),unresolved_execution=int(a.selection_status.eq('EXECUTION_DATA_UNAVAILABLE').sum()),mean_r_interval=cluster_intervals(p),session_quality=pd.read_csv(P/'session_coverage.csv').status.value_counts().to_dict())
    summary['performance_completeness']='INCOMPLETE_EXECUTION' if summary['unresolved_execution'] else 'COMPLETE'
    unavailable=a[(a.ticks==1)&a.selection_status.eq('EXECUTION_DATA_UNAVAILABLE')]
    write('unresolved_execution.csv',unavailable)
    blocked_dates=set(unavailable.date)
    write('affected_date_signal_audit.csv',a[(a.ticks==1)&a.date.isin(blocked_dates)])
    save('study_summary.json',summary)
    cols=['trades','unique_dates','win_pct','net_usd','profit_factor','avg_net_r','max_dd_usd','max_dd_r']
    report=['# Market-structure continuation · fixed 2R','', '**DEVELOPMENT_ONLY_NOT_VALIDATED** · 2020–2023 · Standalone 5-minute structure, no key levels.','', (ROOT/'docs/STRUCTURE_CONTINUATION_2R_V1.md').read_text(), '\n## Signal accounting\n',f'{len(raw):,} causal signals across {raw.date.nunique():,} dates. Every scenario retains selected and skipped reasons. Missing owned minutes invalidate execution reporting, not signal eligibility.','\n**Execution coverage: '+summary['performance_completeness']+'**. One primary trade has an unknown outcome because the March 18, 2020 12:58 New York source minute is absent. It entered at 12:50; the missing minute is owned by the still-open trade. It remains in the signal audit, is excluded from completed-trade performance, and conservatively blocks further entries until session close. Tables and milestone denominators describe completed trades only, not a fully observed full-period result. No data was fabricated.\n','\n## Costs and overall results\n',table(costs,['ticks']+cols+['gross_usd','fees_usd','target_exits','stop_exits','session_exits','POSITION_OPEN','AT_SESSION_CLOSE','conflicts','adverse_stop_gaps']), '\n## Yearly\n',table(groups['yearly'],['year']+cols),'\n## Direction\n',table(groups['direction'],['direction']+cols),'\n## Year and direction\n',table(groups['yearly_direction'],['year','direction']+cols),'\n## How far trades get before exit\n',table(moves,['direction','threshold_r','trades','reached','reached_pct','ambiguous']), '\nStop-first counts exclude threshold touches in a stop minute unless already reached earlier. Ambiguous rows are not added to successes. Native MFE includes the complete exit minute; it is not evidence of an executable fill beyond 2R. No post-exit continuation study has been performed.\n','\n## Excursions and risk\n',table(excursions,['direction','trades','mfe_points_mean','mfe_points_median','mae_points_mean','mae_points_median','mfe_r_mean','mae_r_mean','risk_points_q25','risk_points_median','risk_points_q75','risk_points_max']), '\n## Time of day — descriptive, not filters\n',table(timing,['direction','time_bucket']+cols),'\n## Monthly\n',table(groups['monthly'],['month']+cols),'\n## Uncertainty and limitations\n',json.dumps(summary['mean_r_interval'],sort_keys=True),'\n95% exploratory confidence intervals resample NY trading dates (5,000 draws, seed 1729). No target/stop/swing settings optimized. No starting-equity or margin model. Drawdown is closed-trade drawdown. Sensitivity can change selected trades through position occupancy. This is an isolated Lab research adapter using the unchanged production executor, not a saved strategy version or normal database run. Existing records remain untouched. Validation and OOS have not been read for this experiment. All subgroup findings remain Development-only.']
    (P/'STRUCTURE_CONTINUATION_REPORT.md').write_text('\n'.join(report)+'\n')
    data=dict(summary=summary,costs=costs,yearly=groups['yearly'],direction=groups['direction'],monthly=groups['monthly'],time=timing,time_yearly=groups['time_yearly'],equity=json.loads(eq.to_json(orient='records')),trades=json.loads(p.to_json(orient='records')),milestones=moves)
    (P/'study.html').write_text((ROOT/'scripts/structure_continuation/viewer.html').read_text().replace('/*DATA*/',json.dumps(data,separators=(',',':'),allow_nan=False).replace('</','<\\/')))
    print(json.dumps(summary,sort_keys=True),flush=True)
if __name__=='__main__':main()
