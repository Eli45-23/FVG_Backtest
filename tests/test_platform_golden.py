"""Full-local-data equivalence. No downloaded records are committed as fixtures."""
import json
from pathlib import Path
import pytest
from engine.runner import run
from engine.canonical import digest
from engine.legacy import ROOT,reference

@pytest.mark.parametrize('name,params',[
 ('CONT_A_second_candle_baseline',{}),
 ('CONT_A_max_risk_100',{'max_risk':100}),
 ('CONT_A_risk100_no_1000_1029',{'max_risk':100,'exclude_middle':True}),
])
def test_full_golden(name,params):
    if not all(p.exists() for p in reference.INPUTS.values()):pytest.skip('Local MNQ Parquet required')
    manifest=json.loads((ROOT/'tests/fixtures/golden_manifest.json').read_text())
    result=run((ROOT/'strategies/builtins/cont_a.py').read_text(),params)
    actual=digest([{k:t[k] for k in manifest['fields']} for t in result['trades']])
    expected=manifest['references'][name]
    assert actual==expected['trade_sha256']
    for k,v in expected['overall'].items():assert result['summary']['overall'][k]==v,k
