"""Three frozen candle patterns and transparent account sizing; no future data."""

from collections import deque
from decimal import Decimal as D
import hashlib
import pandas as pd
from engine.legacy import reference as ref

NY = "America/New_York"
HYPOTHESES = ("TWO_PUSH", "OUTSIDE_REVERSAL", "INSIDE_BREAK")
MODES = {
    "ONE_MICRO_DIAGNOSTIC": None,
    "ONE_MICRO_200": D(200),
    "RISK_SIZED_200": D(200),
    "RISK_SIZED_400": D(400),
    "RISK_SIZED_4763": D(4763),
}


class Detector:
    def __init__(self):
        self.bars = deque(maxlen=3)

    def update(self, c):
        if not c.is_complete_5m:
            self.bars.clear()
            return []
        if self.bars and c.timestamp_utc - self.bars[-1].timestamp_utc != pd.Timedelta(
            minutes=5
        ):
            self.bars.clear()
        self.bars.append(c)
        if len(self.bars) < 3:
            return []
        m, p, c = self.bars
        out = []
        for name in HYPOTHESES:
            side = None
            if name == "TWO_PUSH":
                if (
                    p.close > p.open
                    and c.close > c.open
                    and p.close > m.high
                    and c.close > p.high
                ):
                    side = "LONG"
                if (
                    p.close < p.open
                    and c.close < c.open
                    and p.close < m.low
                    and c.close < p.low
                ):
                    side = "SHORT"
                lo, hi = min(p.low, c.low), max(p.high, c.high)
            elif name == "OUTSIDE_REVERSAL":
                if (
                    p.close < p.open
                    and c.close > c.open
                    and c.low < p.low
                    and c.close > p.high
                ):
                    side = "LONG"
                if (
                    p.close > p.open
                    and c.close < c.open
                    and c.high > p.high
                    and c.close < p.low
                ):
                    side = "SHORT"
                lo, hi = c.low, c.high
            else:
                if p.high < m.high and p.low > m.low:
                    if c.close > m.high:
                        side = "LONG"
                    elif c.close < m.low:
                        side = "SHORT"
                lo, hi = m.low, m.high
            if side:
                at = c.timestamp_utc + pd.Timedelta(minutes=5)
                date = str(at.tz_convert(NY).date())
                out.append(
                    dict(
                        hypothesis=name,
                        direction=side,
                        date=date,
                        year=int(date[:4]),
                        entry_time_utc=at,
                        entry_time_ny=at.tz_convert(NY),
                        close=c.close,
                        stop_anchor=lo if side == "LONG" else hi,
                        trigger_start=c.timestamp_utc,
                        signal_id=hashlib.sha256(
                            f"simple-v1|{name}|{at}|{side}".encode()
                        ).hexdigest(),
                    )
                )
        return out


def bracket(s, ticks):
    sign = D(1) if s["direction"] == "LONG" else D(-1)
    entry = ref.tick(D(str(s["close"]))) + sign * D(".25") * ticks
    stop = D(str(s["stop_anchor"])) - sign * D(".25")
    risk = (entry - stop) * sign
    loss = risk * 2 + D(".50") * ticks + D("1.46")
    win = risk * 4 - D(".50") * ticks - D("1.46")
    return dict(
        entry_price=entry,
        stop_price=stop,
        risk_points=risk,
        target_price=ref.tick(entry + sign * risk * 2),
        risk_usd=risk * 2,
        target_r=D(2),
        planned_loss_per_micro=loss,
        planned_gain_per_micro=win,
    )


def size(b, mode, equity):
    loss = b["planned_loss_per_micro"]
    if b["risk_points"] <= 0:
        return 0, "NON_POSITIVE_RISK"
    if loss > 75:
        return 0, "RISK_BUDGET"
    if b["planned_gain_per_micro"] <= loss:
        return 0, "NET_REWARD_NOT_GREATER_THAN_RISK"
    if mode == "ONE_MICRO_DIAGNOSTIC":
        return 1, None
    margin = MODES[mode]
    q = min(int(D(75) // loss), max(0, int(equity // (margin + loss))))
    if mode == "ONE_MICRO_200":
        q = min(1, q)
    return (q, None) if q else (0, "INSUFFICIENT_CAPITAL")
