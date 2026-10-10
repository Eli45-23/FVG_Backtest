from tests.test_simple_discovery import bar
from scripts.simple_discovery_v2.core import Detector
import pytest

PATTERNS={
'PULLBACK_RESUME':[(100,102,99,101),(101,108,100,107),(107,107,103,104),(104,110,103,109)],
'RANGE_FAILURE':[(100,105,95,101),(101,104,96,102),(102,104,97,101),(101,104,94,100)],
'THREE_BAR_BREAK':[(100,105,95,101),(101,104,96,102),(102,104,97,101),(101,108,99,107)],
}
@pytest.mark.parametrize('name',PATTERNS)
@pytest.mark.parametrize('mirror',[False,True])
def test_rules_confirmation_and_mirrors(name,mirror):
    d=Detector()
    data=PATTERNS[name]
    if mirror: data=[(200-o,200-l,200-h,200-c) for o,h,l,c in data]
    for i,b in enumerate(data[:3]): assert d.update(bar(i,*b))==[]
    result=[s for s in d.update(bar(3,*data[3])) if s['hypothesis']==name]
    assert len(result)==1
    assert result[0]['direction']==('SHORT' if mirror else 'LONG')
    assert str(result[0]['entry_time_ny'].time())=='09:50:00'
    assert result[0]['stop_anchor']==({'PULLBACK_RESUME':103,'RANGE_FAILURE':94,'THREE_BAR_BREAK':95}[name] if not mirror else {'PULLBACK_RESUME':97,'RANGE_FAILURE':106,'THREE_BAR_BREAK':105}[name])

@pytest.mark.parametrize('missing',[False,True])
def test_break_continuity(missing):
    d=Detector()
    data=PATTERNS['THREE_BAR_BREAK']
    for i,b in enumerate(data[:3]): d.update(bar(i,*b,complete=(i!=2 or missing)))
    assert d.update(bar(4 if missing else 3,*data[3]))==[]

def test_double_sweep_not_directionally_assigned():
    d=Detector()
    for i,b in enumerate(PATTERNS['RANGE_FAILURE'][:3]): d.update(bar(i,*b))
    assert not any(s['hypothesis']=='RANGE_FAILURE' for s in d.update(bar(3,101,106,94,100)))

def test_equal_range_close_not_break():
    d=Detector()
    for i,b in enumerate(PATTERNS['THREE_BAR_BREAK'][:3]): d.update(bar(i,*b))
    assert not any(s['hypothesis']=='THREE_BAR_BREAK' for s in d.update(bar(3,101,108,99,105)))
