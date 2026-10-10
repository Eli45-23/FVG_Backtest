"""Post-hoc data-quality/complete-day diagnostics; cannot override primary gates."""
import sys,json
from pathlib import Path
import pandas as pd
import databento as db
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.simple_search.run import P
from scripts.simple_discovery.run import sha
from scripts.simple_discovery.report import block_evidence

def main():
    out=P/'diagnostics';out.mkdir(exist_ok=True)
    raw=ROOT/'outputs/data/GLBX.MDP3_MNQ.v.0_ohlcv-1m_2020.dbn.zst'
    before=sha(raw);g=db.DBNStore.from_file(raw).to_df()
    assert g.index.min()>=pd.Timestamp('2020-01-01',tz='UTC') and g.index.max()<pd.Timestamp('2021-01-01',tz='UTC')
    start=pd.Timestamp('2020-03-18 16:58',tz='UTC');next_at=g.index[g.index>=start].min()
    assert not (g.index==start).any() and next_at==pd.Timestamp('2020-03-18 17:11',tz='UTC')
    gap=dict(status='UNRESOLVED_INSTRUMENT_HALT_TREATMENT',raw_source=str(raw.relative_to(ROOT)),raw_sha256=before,raw_rows=len(g),missing_start_ny=start.tz_convert('America/New_York').isoformat(),next_observed_ny=next_at.tz_convert('America/New_York').isoformat(),production_semantics_changed=False,source_data_changed=False)
    (out/'raw_gap_review.json').write_text(json.dumps(gap,sort_keys=True,indent=2)+'\n')
    d=pd.read_csv(P/'daily.csv');rows=[]
    for h,grp in d[d.ticks==1].groupby('hypothesis'):
        usable=grp[grp.net_pnl_usd.notna()]
        rows.append(dict(hypothesis=h,status='POST_HOC_COMPLETE_DAY_SENSITIVITY_NOT_PRIMARY',excluded_unknown_days=len(grp)-len(usable),days=len(usable),known_mean=float(usable.net_pnl_usd.mean()),**block_evidence(usable)))
    previous=pd.read_csv(ROOT/'work/simple-strategy-discovery-v2/combined_evidence.csv')
    pvals=[r['p_value'] for r in rows]+previous.p_value.tolist();last=0
    for rank,i in enumerate(sorted(range(18),key=lambda i:pvals[i])):
        last=max(last,min(1,(18-rank)*pvals[i]))
        if i<len(rows):rows[i]['holm_p_18_sensitivity']=last
    pd.DataFrame(rows).to_csv(out/'complete_day_sensitivity.csv',index=False,float_format='%.12g',lineterminator='\n')
    assert sha(raw)==before
    m=dict(status='POST_HOC_DIAGNOSTIC_ONLY',primary_gate_changed=False,raw_sha256=before,daily_sha256=sha(P/'daily.csv'),script_sha256=sha(Path(__file__)),artifacts={p.name:sha(p) for p in sorted(out.iterdir()) if p.suffix in ['.json','.csv'] and p.name!='manifest.json'})
    mp=out/'manifest.json'
    if mp.exists():assert json.loads(mp.read_text())==m,'Diagnostic repeat mismatch'
    else:mp.write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
    print('Raw archive gap confirmed; post-hoc sensitivity recorded separately from primary gates.')
if __name__=='__main__':main()
