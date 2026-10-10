from types import SimpleNamespace
from decimal import Decimal as D
import numpy as np
import pandas as pd
import pytest
from scripts.structure_continuation.core import Detector, bracket, milestones
from engine.partial_execution import execute
from engine.legacy import reference as ref
from engine.strategy import Entry

T=pd.Timestamp('2020-03-09 09:30',tz='America/New_York').tz_convert('UTC')
OHLC=[(93,97,92,96),(96,96.5,91,92),(92,94,90,93),(93,97,92,96),(96,99,95,98),(98,100,97,99),(99,99,96,97),(97,98,95,96),(96,99,96,98),(98,99.75,97,99),(99,103,98,102)]
def rows(mirror=False):
    data=[(200-o,200-l,200-h,200-c) for o,h,l,c in OHLC] if mirror else OHLC
    return [SimpleNamespace(timestamp_utc=T+pd.Timedelta(minutes=5*i),open=D(str(o)),high=D(str(h)),low=D(str(l)),close=D(str(c)),is_complete_5m=True) for i,(o,h,l,c) in enumerate(data)]

@pytest.mark.parametrize('mirror',[False,True])
def test_exact_video_signal_causal(mirror):
    d=Detector(); bs=rows(mirror)
    for b in bs[:-1]: assert d.update(b) is None
    s=d.update(bs[-1]);assert s['direction']==('SHORT' if mirror else 'LONG')
    assert s['pullback_available']==T+pd.Timedelta(minutes=50)
    assert s['entry_time_utc']==T+pd.Timedelta(minutes=55)
    assert s['pullback_class']==('LH' if mirror else 'HL')
    assert s['swing_price']==100
    assert s['pullback_price']==(105 if mirror else 95)
    repeat=Detector(); actual=[repeat.update(b) for b in bs][-1];assert actual==s

@pytest.mark.parametrize('mode',['missing','incomplete','wick','equal','unconfirmed'])
def test_no_invalid_signal(mode):
    bs=rows();d=Detector()
    if mode=='missing':bs.pop(8)
    if mode=='incomplete':bs[8].is_complete_5m=False
    if mode=='wick':bs[-1].close=D(99)
    if mode=='equal':bs[-1].close=D(100)
    if mode=='unconfirmed':bs[9].close=D(101);bs[9].high=D(102)
    assert not any(d.update(b) for b in bs)

def test_no_duplicate_or_deferred_break():
    d=Detector();bs=rows(); assert len([s for b in bs if (s:=d.update(b))])==1
    b=bs[-1]; b.timestamp_utc+=pd.Timedelta(minutes=5)
    assert d.update(b) is None

@pytest.mark.parametrize('mirror',[False,True])
@pytest.mark.parametrize('ticks',[0,1,2])
def test_native_bracket_target_costs_and_preentry_exclusion(mirror,ticks):
    d=Detector();s=[d.update(b) for b in rows(mirror)][-1];v=bracket(s,ticks)
    sign=-1 if mirror else 1
    assert v['stop_price']==D('105.25' if mirror else '94.75')
    assert (v['target_price']-v['entry_price'])*sign==2*v['risk_points']
    at=s['entry_time_utc']; e=v['entry_price'];tg=v['target_price']
    mins=pd.DataFrame([dict(open=e,high=D(1000),low=D(0),close=e,volume=1),dict(open=e,high=max(e,tg),low=min(e,tg),close=tg,volume=1)],index=[at-pd.Timedelta(minutes=1),at])
    trade,_=execute(dict(**s,**v),mins,ref.Config(D('.73'),ticks),1,Entry(s['direction'],v['stop_price'],D(2)),None,{},{},at+pd.Timedelta(minutes=1))
    assert trade['exit_reason']=='TARGET'
    assert trade['net_pnl_usd']==4*v['risk_points']-D('.5')*ticks-D('1.46')
    assert trade['management_event_count']==0

@pytest.mark.parametrize('mirror',[False,True])
def test_milestones_stop_first_and_cap(mirror):
    a=np.array([[100,102,99,101],[101,121,89,110]],dtype=float)
    if mirror:a=200-a[:,[0,2,1,3]]
    m=milestones(a,100,110 if mirror else 90,10,'SHORT' if mirror else 'LONG')
    assert not m['reached_1r'] and m['ambiguous_1r']
    a=np.array([[100,130,99,120]],dtype=float)
    if mirror:a=200-a[:,[0,2,1,3]]
    assert milestones(a,100,110 if mirror else 90,10,'SHORT' if mirror else 'LONG')['conservative_max_r']==2
