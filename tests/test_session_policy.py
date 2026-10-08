"""Synthetic-only tests: no historical Validation/OOS file access."""
from decimal import Decimal as D
import pandas as pd
import pytest
from engine.runner import RunConfig, run
from engine.timeframes import aggregate

SOURCE = '''from decimal import Decimal as D
from engine.strategy import Entry
class Strategy:
    def on_bar(self,ctx,p):
        if ctx.bar.time=='09:30': return Entry('SHORT',ctx.bar.close+D('50'),D('1'))
'''


def fixture():
    # Synthetic 2020-11-27 early-close session, plus later data that must not be owned.
    ts = pd.date_range('2020-11-27 14:30', periods=390, freq='min', tz='UTC')
    raw = pd.DataFrame(dict(ts_event=ts,open=100*10**9,high=101*10**9,
                            low=99*10**9,close=100*10**9,volume=1))
    raw.loc[ts >= pd.Timestamp('2020-11-27 18:00',tz='UTC'),'high'] = 200*10**9
    return dict(minutes=raw,bars=aggregate(raw,'5m'))


def cfg(policy='XNYS_FULL'):
    return RunConfig(start='2020-11-27',end='2020-11-28',
                     dataset_profile='research_2020_2026',execution_mode='extended_v1',
                     session_policy=policy)


def test_default_full_session_policy_unchanged():
    assert RunConfig().session_policy == 'XNYS_FULL'
    assert run(SOURCE,{},cfg(),fixture())['trades']==[]


def test_opt_in_actual_early_close_and_no_later_fills():
    trades=run(SOURCE,{},cfg('XNYS_ALL'),fixture())['trades']
    assert len(trades)==1
    t=trades[0]
    assert t['exit_reason']=='SESSION_CLOSE'
    assert t['exit_time_ny'].strftime('%H:%M')=='13:00'
    assert t['mae_points']==D('1')


@pytest.mark.parametrize('kwargs',[
    {'session_policy':'UNKNOWN'}, {'session_policy':'XNYS_ALL'},
])
def test_invalid_or_legacy_all_session_config_rejected(kwargs):
    with pytest.raises(ValueError): RunConfig(**kwargs).validate()


def test_explicit_level_session_config_reaches_feature_hub(monkeypatch):
    import engine.extended_runner as runner
    from dataclasses import replace
    original=runner.FeatureHub
    received=[]
    def capture(*args, **kwargs):
        received.append(kwargs['session'])
        return original(*args, **kwargs)
    monkeypatch.setattr(runner,'FeatureHub',capture)
    run(SOURCE,{},replace(cfg('XNYS_ALL'),feature_config={'session':{'rejection_penetration':0}}),fixture())
    assert type(received[0].rejection_penetration) is int
