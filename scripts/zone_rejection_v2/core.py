"""Newest-zone policy and conservative milestone measurement; no outcome inputs."""

from decimal import Decimal as D
import pandas as pd


class ActiveZones:
    def __init__(self):
        self.active = {}
        self.ended = {}
        self.audit = []

    def add(self, z):
        side = z["zone_type"]
        at = pd.Timestamp(z["availability_timestamp"])
        old = self.active.get(side)
        if old:
            self.ended[old["zone_id"]] = at
            self.audit.append(
                dict(
                    zone_id=old["zone_id"],
                    timestamp=at,
                    reason="REPLACED_BY_NEW_ZONE",
                    replacement=z["zone_id"],
                )
            )
        self.active[side] = z
        self.audit.append(
            dict(
                zone_id=z["zone_id"], timestamp=at, reason="AVAILABLE", replacement=None
            )
        )

    def observe(self, row):
        from engine.research.levels import valid_bar

        if not valid_bar(row):
            return
        at = row.timestamp_utc + pd.Timedelta(minutes=5)
        for side, z in list(self.active.items()):
            if pd.Timestamp(z["availability_timestamp"]) > row.timestamp_utc:
                continue
            broken = (
                row.low > D(str(z["top"]))
                if side == "SUPPLY"
                else row.high < D(str(z["bottom"]))
            )
            if broken:
                self.ended[z["zone_id"]] = at
                self.audit.append(
                    dict(
                        zone_id=z["zone_id"],
                        timestamp=at,
                        reason="FULL_5M_BREAK",
                        replacement=None,
                    )
                )
                del self.active[side]

    def known(self):
        return {z["zone_id"]: z for z in self.active.values()}


def milestones(trade, day):
    """Count observed gross price milestones before actual exit; stop-first."""
    entry = trade["entry_price"]
    risk = trade["risk_points"]
    stop = trade["stop_price"]
    long = trade["direction"] == "LONG"
    out = {}
    for r in (1, 2):
        level = entry + (1 if long else -1) * risk * r
        hit = False
        ambiguous = False
        when = None
        owned = day.loc[
            (day.index >= trade["entry_time_utc"])
            & (day.index < trade["exit_time_utc"])
        ]
        for at, b in owned.iterrows():
            stopped = b.low <= stop if long else b.high >= stop
            reached = b.high >= level if long else b.low <= level
            if stopped:
                ambiguous = bool(reached)
                break
            if reached:
                hit = True
                when = at + pd.Timedelta(minutes=1)
                break
        out[f"reached_{r}r"] = hit
        out[f"{r}r_stop_same_minute_ambiguity"] = ambiguous
        out[f"first_{r}r_observed_at"] = when
    return out
