"""Create new local protocol; never overwrite an existing protocol or user records."""
import sys,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.structure_continuation.run import P,sha

def main():
    P.mkdir(parents=True,exist_ok=True)
    spec=ROOT/'docs/STRUCTURE_CONTINUATION_2R_V1.md'
    v=dict(status='DEVELOPMENT_ONLY_NOT_VALIDATED',dataset='research_2020_2026',start_inclusive='2020-01-01',end_exclusive='2024-01-01',target_r=2,quantity=1,primary_slippage_ticks_per_side=1,commission_per_side=.73,specification_sha256=sha(spec),detector_sha256=sha(ROOT/'scripts/structure_continuation/core.py'),selection='one_position_both_directions_no_daily_cap',signal_rules=spec.read_text())
    path=P/'protocol.json'
    if path.exists(): assert json.loads(path.read_text())==v
    else:path.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
    con=sqlite3.connect('file:'+str(ROOT/'storage/app.db')+'?mode=ro',uri=True)
    q={'runs':'id,status','event_studies':'id,status,config_hash','strategies':'id,current_version,updated_at','strategy_versions':'id,source_hash','variants':'id','schema_migrations':'version','research_splits':'id','experiment_snapshots':'id,snapshot_hash'}
    state={k:con.execute(f'SELECT {cols} FROM {k} ORDER BY 1').fetchall() for k,cols in q.items()};state['reveals']=con.execute('SELECT * FROM event_study_reveals ORDER BY 1').fetchall()
    serialized=json.dumps(state,sort_keys=True,default=str);path=P/'storage_before.json'
    if path.exists():assert path.read_text()==serialized
    else:path.write_text(serialized)
if __name__=='__main__':main()
