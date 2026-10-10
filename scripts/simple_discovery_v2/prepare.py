import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.simple_discovery.run import sha
from scripts.simple_discovery_v2.run import P
files=['docs/SIMPLE_STRATEGY_DISCOVERY_V2.md','scripts/simple_discovery_v2/core.py','scripts/simple_discovery_v2/run.py','scripts/simple_discovery/run.py','scripts/simple_discovery/core.py']
v=dict(status='PREREGISTERED_DEVELOPMENT_ONLY',hashes={s:sha(ROOT/s) for s in files},primary_family_size=6,seed=1729)
P.mkdir(parents=True,exist_ok=True)
p=P/'protocol.json'
if p.exists(): assert json.loads(p.read_text())==v
else: p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
