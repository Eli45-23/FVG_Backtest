"""Frozen strategy tests using synthetic Development candles only."""
from pathlib import Path
from decimal import Decimal as D
import pandas as pd
import pytest
from engine.strategy import Bar, Context
from engine.strategy.loading import load
from engine.research.levels import Level

SOURCE=(Path(__file__).resolve().parents[1]/'strategies/builtins/pdh_failed_break_short_v1.py').read_text()


def ctx(clock, o=99, h=102, l=98, c=101, available='2020-01-03 21:00'):
    start=pd.Timestamp('2020-01-06 '+clock,tz='America/New_York').tz_convert('UTC')
    b=Bar(start,*map(lambda x:D(str(x)),[o,h,l,c]),1)
    level=Level('synthetic-pdh','PDH',D(100),'2020-01-06','2020-01-03',pd.Timestamp(available,tz='UTC'),True,())
    return Context(start+pd.Timedelta(minutes=5),b,None,(b,),bar1=b,bar2=b,
                   levels=(level,),features={'5m':{'atr14':D(10)}})


def test_exact_failed_break_fixed_1r_and_sequence_high():
    s,p,_=load(SOURCE)
    assert s.on_bar(ctx('09:35',h=104),p) is None
    order=s.on_bar(ctx('09:40',o=101,h=103,c=99),p)
    assert order.direction=='SHORT' and order.stop==D('104.25')
    assert order.target_r==1 and order.max_risk is None
    assert order.metadata['touch_number']==1
    assert pd.Timestamp(order.metadata['confirmation_timestamp'])==ctx('09:40').timestamp
    assert not hasattr(s,'manage')


@pytest.mark.parametrize('close',[100,101,102])
def test_failure_must_close_strictly_below(close):
    s,p,_=load(SOURCE);s.on_bar(ctx('09:35'),p)
    assert s.on_bar(ctx('09:40',c=close),p) is None


def test_missing_or_skipped_incomplete_bar_cannot_bridge():
    s,p,_=load(SOURCE);s.on_bar(ctx('09:35'),p)
    assert s.on_bar(ctx('09:45',c=99),p) is None


def test_second_touch_episode_rejected():
    s,p,_=load(SOURCE)
    s.on_bar(ctx('09:30',h=101,c=99),p)
    s.on_bar(ctx('09:35',h=99,l=97,c=98),p)
    s.on_bar(ctx('09:40'),p)
    assert s.on_bar(ctx('09:45',c=99),p) is None


def test_first_episode_can_have_repeated_distinct_breaks():
    s,p,_=load(SOURCE);s.on_bar(ctx('09:30'),p)
    a=s.on_bar(ctx('09:35',c=99),p)
    s.on_bar(ctx('09:40'),p)
    b=s.on_bar(ctx('09:45',c=99),p)
    assert a and b and a.metadata['candidate_event_id']!=b.metadata['candidate_event_id']
    assert a.metadata['touch_number']==b.metadata['touch_number']==1


def test_unavailable_pdh_never_used_retroactively():
    s,p,_=load(SOURCE)
    s.on_bar(ctx('09:35',available='2020-01-06 14:40'),p)
    assert s.on_bar(ctx('09:40',c=99,available='2020-01-06 14:40'),p) is None
