from scripts.simple_search.timing import signal
from tests.test_simple_discovery import bar
import pandas as pd

def frame():
    return pd.DataFrame([vars(bar(i,100,110,90,101)) for i in range(78)])

def test_timing_confirmation_and_directions():
    g=frame();s=signal(g,102)
    assert len(s)==2
    assert [x['direction'] for x in s]==['LONG','SHORT']
    assert all(str(x['entry_time_ny'].time())=='15:30:00' for x in s)
    assert s[0]['stop_anchor']==90 and s[1]['stop_anchor']==110

def test_missing_prior_close_only_omits_overnight():
    assert [s['hypothesis'] for s in signal(frame(),None)]==['LAST30_RTH']

def test_incomplete_opening_or_recent_window_blocks():
    for i in [0,5,66,71]:
        g=frame();g.loc[i,'is_complete_5m']=False
        assert signal(g,102)==[]

def test_no_future_candles_required():
    g=frame()
    assert signal(g.iloc[:72],102)==signal(g,102)
    assert signal(g.iloc[:71],102)==[]
