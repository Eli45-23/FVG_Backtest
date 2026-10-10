import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.simple_discovery.run import sha
P=ROOT/'work/simple-strategy-unrestricted-v1';P.mkdir(parents=True,exist_ok=True)
files=['docs/SIMPLE_UNRESTRICTED_SEARCH_V1.md','scripts/simple_search/core.py','scripts/simple_discovery/core.py','scripts/simple_discovery_v2/core.py']
v=dict(status='PREREGISTERED_DEVELOPMENT_ONLY',hashes={s:sha(ROOT/s) for s in files},primary_family_size=18,seed=1729)
p=P/'protocol.json'
if p.exists(): assert json.loads(p.read_text())==v
else:p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
