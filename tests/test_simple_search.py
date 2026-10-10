from tests.test_simple_discovery import bar
from scripts.simple_search.core import Detector,bracket
import pytest
from decimal import Decimal as D

@pytest.mark.parametrize('mirror',[False,True])
def test_opening_only_confirmed_range(mirror):
    d=Detector();data=[(100,104,99,103),(103,108,102,107),(107,110,106,109)]
    if mirror:data=[(200-o,200-l,200-h,200-c) for o,h,l,c in data]
    for i,b in enumerate(data[:2]):assert not any(s['hypothesis'].startswith('OPEN_') for s in d.update(bar(i,*b)))
    found={s['hypothesis']:s for s in d.update(bar(2,*data[2])) if s['hypothesis'].startswith('OPEN_')}
    assert len(found)==2
    assert found['OPEN_MOMENTUM_15']['direction']==('SHORT' if mirror else 'LONG')
    assert found['OPEN_FADE_15']['direction']==('LONG' if mirror else 'SHORT')
    assert str(found['OPEN_FADE_15']['entry_time_ny'].time())=='09:45:00'
    assert found['OPEN_MOMENTUM_15']['stop_anchor']==(101 if mirror else 99)

@pytest.mark.parametrize('missing',[True,False])
def test_opening_no_partial_fallback(missing):
    d=Detector();d.update(bar(0,100,102,99,101))
    d.update(bar(1,101,103,100,102,complete=missing))
    assert not any(s['hypothesis'].startswith('OPEN_') for s in d.update(bar(3 if missing else 2,102,104,101,103)))

def test_channel_requires_twelve_prior_bars():
    d=Detector()
    for i in range(12):assert not any(s['hypothesis'].startswith('CHANNEL') for s in d.update(bar(i,100,105,95,100)))
    found=[s for s in d.update(bar(12,100,110,99,109)) if s['hypothesis']=='CHANNEL12_BREAK']
    assert len(found)==1 and found[0]['stop_anchor']==95
    b=bracket(found[0],1)
    assert b['stop_price']==D('94.75') and b['target_price']-b['entry_price']==2*b['risk_points']

def test_channel_sweep_both_edges_has_no_reclaim():
    d=Detector()
    for i in range(12):d.update(bar(i,100,105,95,100))
    assert not any(s['hypothesis']=='CHANNEL12_RECLAIM' for s in d.update(bar(12,100,106,94,100)))

def test_ema_warmup_and_cross():
    d=Detector()
    for i in range(20):assert not any(s['hypothesis'].startswith('EMA') for s in d.update(bar(i,100,101,99,100)))
    found=[s for s in d.update(bar(20,100,103,99,102)) if s['hypothesis']=='EMA20_CROSS']
    assert len(found)==1 and found[0]['direction']=='LONG'

def test_future_appends_do_not_change_past_signals():
    data=[bar(i,100+i,102+i,99+i,101+i) for i in range(30)]
    a=Detector();b=Detector();first=[];whole=[]
    for x in data[:22]:first.extend(a.update(x))
    for x in data:whole.extend(b.update(x))
    assert first==[s for s in whole if s['entry_time_utc']<=data[21].timestamp_utc+__import__('pandas').Timedelta(minutes=5)]

def test_risk_above_previous_budget_is_not_filtered_by_detector():
    d=Detector()
    for i in range(12):d.update(bar(i,100,150,50,100))
    found=[s for s in d.update(bar(12,100,160,99,155)) if s['hypothesis']=='CHANNEL12_BREAK']
    assert len(found)==1 and bracket(found[0],1)['planned_loss_per_micro']>75
