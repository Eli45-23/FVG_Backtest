"""Twelve frozen hypotheses; no capital, dollar-risk, or daily-entry cap."""
from collections import deque
from decimal import Decimal as D
import hashlib
import pandas as pd
from scripts.simple_discovery.core import Detector as First, NY, bracket
from scripts.simple_discovery_v2.core import Detector as Second

HYPOTHESES=('TWO_PUSH','OUTSIDE_REVERSAL','INSIDE_BREAK','PULLBACK_RESUME','RANGE_FAILURE','THREE_BAR_BREAK',
 'OPEN_MOMENTUM_15','OPEN_FADE_15','EMA20_CROSS','EMA20_PULLBACK','CHANNEL12_BREAK','CHANNEL12_RECLAIM')

class Detector:
    def __init__(self):
        self.first=First();self.second=Second()
        self.bars=deque(maxlen=21)
        self.ema=None;self.n=0;self.opening=[]
    def update(self,c):
        out=self.first.update(c)+self.second.update(c)
        for s in out:
            s['signal_id']=hashlib.sha256(f"unrestricted-v1|{s['hypothesis']}|{s['entry_time_utc']}|{s['direction']}".encode()).hexdigest()
        if not c.is_complete_5m:
            self.bars.clear();self.ema=None;self.n=0;self.opening=[]
            return out
        if self.bars and c.timestamp_utc-self.bars[-1].timestamp_utc != pd.Timedelta(minutes=5):
            self.bars.clear();self.ema=None;self.n=0;self.opening=[]
        prev=self.bars[-1] if self.bars else None
        oldema=self.ema
        close=D(str(c.close))
        self.ema=close if self.ema is None else self.ema+(close-self.ema)*D(2)/D(21)
        self.n+=1
        at=c.timestamp_utc+pd.Timedelta(minutes=5)
        local=c.timestamp_utc.tz_convert(NY)
        if local.hour==9 and local.minute in (30,35,40): self.opening.append(c)
        def add(name,side,lo,hi):
            date=str(at.tz_convert(NY).date())
            out.append(dict(hypothesis=name,direction=side,date=date,year=int(date[:4]),entry_time_utc=at,
                entry_time_ny=at.tz_convert(NY),close=c.close,stop_anchor=lo if side=='LONG' else hi,
                trigger_start=c.timestamp_utc,signal_id=hashlib.sha256(f'unrestricted-v1|{name}|{at}|{side}'.encode()).hexdigest()))
        if local.hour==9 and local.minute==40 and len(self.opening)==3:
            o=self.opening[0].open; lo=min(b.low for b in self.opening);hi=max(b.high for b in self.opening)
            if c.close!=o:
                side='LONG' if c.close>o else 'SHORT'
                add('OPEN_MOMENTUM_15',side,lo,hi)
                add('OPEN_FADE_15','SHORT' if side=='LONG' else 'LONG',lo,hi)
        if self.n>=21 and prev is not None:
            pc=D(str(prev.close)); co=D(str(c.open))
            if pc<=oldema and close>self.ema: add('EMA20_CROSS','LONG',c.low,c.high)
            elif pc>=oldema and close<self.ema: add('EMA20_CROSS','SHORT',c.low,c.high)
            if pc>oldema and D(str(c.low))<=oldema and close>self.ema and close>co and self.ema>oldema:
                add('EMA20_PULLBACK','LONG',c.low,c.high)
            elif pc<oldema and D(str(c.high))>=oldema and close<self.ema and close<co and self.ema<oldema:
                add('EMA20_PULLBACK','SHORT',c.low,c.high)
        if len(self.bars)>=12:
            window=list(self.bars)[-12:];lo=min(b.low for b in window);hi=max(b.high for b in window)
            if c.close>hi: add('CHANNEL12_BREAK','LONG',lo,hi)
            elif c.close<lo: add('CHANNEL12_BREAK','SHORT',lo,hi)
            if c.low<lo and lo<c.close<hi and c.high<=hi: add('CHANNEL12_RECLAIM','LONG',c.low,c.high)
            elif c.high>hi and lo<c.close<hi and c.low>=lo: add('CHANNEL12_RECLAIM','SHORT',c.low,c.high)
        self.bars.append(c)
        return out
