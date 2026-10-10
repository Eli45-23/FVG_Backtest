"""Frozen standalone continuation experiment; causal detector, no outcome access."""
from decimal import Decimal as D
from types import SimpleNamespace
import hashlib
import pandas as pd
from engine.research.structure import Structure
from engine.legacy import reference as ref

NY = 'America/New_York'
BINS = ['09:30–09:59','10:00–10:29','10:30–10:59','11:00–11:59','12:00–13:59','14:00–15:59']

def bucket(at):
    t=at.tz_convert(NY); m=t.hour*60+t.minute
    return next((v for end,v in zip([600,630,660,720,840,960],BINS) if m<end),'SESSION_CLOSE')

class Detector:
    def __init__(self):
        self.structure=Structure(); self.previous=None

    def update(self,b):
        at=b.timestamp_utc
        if not b.is_complete_5m:
            self.structure=Structure(); self.previous=None
            return None
        if self.previous is not None and at-self.previous.timestamp_utc != pd.Timedelta(minutes=5):
            self.structure=Structure(); self.previous=None
        high,low=self.structure.high,self.structure.low
        confirmed=at+pd.Timedelta(minutes=5)
        bar=SimpleNamespace(timestamp=at,open=b.open,high=b.high,low=b.low,close=b.close)
        events=self.structure.update(bar,confirmed)
        s=None
        if high and low and self.previous is not None:
            for direction,level,pullback,prog in [('LONG',high,low,'HL'),('SHORT',low,high,'LH')]:
                sign=1 if direction=='LONG' else -1
                broken=any(e.get('swing_id')==level['id'] for e in events)
                if (broken and pullback['progression']==prog
                    and level['formation_timestamp'] < pullback['formation_timestamp']
                    and max(level['availability_timestamp'],pullback['availability_timestamp']) <= at
                    and (float(self.previous.close)-level['price'])*sign<=0):
                    sid=hashlib.sha256(f"structure-continuation-2r-v1|{level['id']}|{pullback['id']}|{confirmed}".encode()).hexdigest()
                    date=str(confirmed.tz_convert(NY).date())
                    s=dict(signal_id=sid,event_id=sid,date=date,year=int(date[:4]),direction=direction,
                        entry_time_utc=confirmed,entry_time_ny=confirmed.tz_convert(NY),trigger_bar_start=at,
                        close=b.close,signal_high=b.high,signal_low=b.low,
                        swing_id=level['id'],swing_price=level['price'],swing_formed=level['formation_timestamp'],
                        swing_available=level['availability_timestamp'],pullback_id=pullback['id'],
                        pullback_price=pullback['price'],pullback_formed=pullback['formation_timestamp'],
                        pullback_available=pullback['availability_timestamp'],pullback_class=prog,time_bucket=bucket(confirmed))
        self.previous=b
        return s

def bracket(s,ticks):
    sign=D(1) if s['direction']=='LONG' else D(-1)
    entry=ref.tick(D(str(s['close'])))+sign*D('.25')*ticks
    stop=D(str(s['pullback_price']))-sign*D('.25')
    risk=(entry-stop)*sign
    return dict(entry_price=entry,stop_price=stop,risk_points=risk,risk_usd=risk*2,
                target_price=ref.tick(entry+sign*risk*2),target_r=D(2))

def milestones(owned,entry,stop,risk,direction):
    """Only owned minutes. Stop-first; cap guaranteed movement at the 2R exit."""
    sign=1 if direction=='LONG' else -1
    out={}; stopped=False
    favorable=[]
    for row in owned:
        if (row[2]<=stop if sign==1 else row[1]>=stop):
            stopped=True; break
        favorable.append(max(0,(row[1]-entry) if sign==1 else (entry-row[2])))
    safe=min(max(favorable,default=0),2*risk)
    for r in [.5,1,1.5,2]:
        name=str(r).replace('.','p')
        out['reached_'+name+'r']=safe>=r*risk
        out['ambiguous_'+name+'r']=bool(stopped and safe<r*risk and
            ((owned[-1,1]-entry if sign==1 else entry-owned[-1,2])>=r*risk))
    out['conservative_max_r']=safe/risk
    return out
