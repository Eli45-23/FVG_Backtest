"""Frozen second research batch; confirmed adjacent bars only."""
from collections import deque
import hashlib
import pandas as pd
from scripts.simple_discovery.core import NY

HYPOTHESES = ('PULLBACK_RESUME', 'RANGE_FAILURE', 'THREE_BAR_BREAK')

class Detector:
    def __init__(self):
        self.bars = deque(maxlen=4)

    def update(self, c):
        if not c.is_complete_5m:
            self.bars.clear()
            return []
        if self.bars and c.timestamp_utc - self.bars[-1].timestamp_utc != pd.Timedelta(minutes=5):
            self.bars.clear()
        self.bars.append(c)
        if len(self.bars) != 4:
            return []
        a, b, p, c = self.bars
        signals = []
        for name in HYPOTHESES:
            side = None
            if name == 'PULLBACK_RESUME':
                if b.close > a.high and p.close < p.open and p.low > b.low and c.close > p.high:
                    side = 'LONG'
                elif b.close < a.low and p.close > p.open and p.high < b.high and c.close < p.low:
                    side = 'SHORT'
                lo, hi = min(p.low,c.low), max(p.high,c.high)
            elif name == 'RANGE_FAILURE':
                lo0, hi0 = min(a.low,b.low,p.low), max(a.high,b.high,p.high)
                # Outside bars sweeping BOTH sides are explicitly ambiguous and omitted.
                if c.low < lo0 and lo0 < c.close < hi0 and c.high <= hi0:
                    side = 'LONG'
                elif c.high > hi0 and lo0 < c.close < hi0 and c.low >= lo0:
                    side = 'SHORT'
                lo, hi = c.low, c.high
            else:
                lo, hi = min(a.low,b.low,p.low), max(a.high,b.high,p.high)
                if c.close > hi:
                    side = 'LONG'
                elif c.close < lo:
                    side = 'SHORT'
            if side:
                at = c.timestamp_utc + pd.Timedelta(minutes=5)
                date = str(at.tz_convert(NY).date())
                signals.append(dict(hypothesis=name,direction=side,date=date,year=int(date[:4]),
                    entry_time_utc=at,entry_time_ny=at.tz_convert(NY),close=c.close,
                    stop_anchor=lo if side=='LONG' else hi,trigger_start=c.timestamp_utc,
                    signal_id=hashlib.sha256(f'simple-v2|{name}|{at}|{side}'.encode()).hexdigest()))
        return signals
