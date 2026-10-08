"""Causal compound state machines; no outcome module or future dataframe."""

from dataclasses import dataclass
import pandas as pd
from engine.canonical import digest
from engine.research.levels import valid_bar


@dataclass(frozen=True)
class SequenceConfig:
    retest_full_hold: str = "adjacent_after_retest"
    confirmation: str = "next_close_beyond_event_extreme"

    def __post_init__(self):
        if (
            self.retest_full_hold != "adjacent_after_retest"
            or self.confirmation != "next_close_beyond_event_extreme"
        ):
            raise ValueError("Unsupported mechanical sequence definition")


class Sequences:
    def __init__(self, config=SequenceConfig(), minutes=5):
        self.config = config
        self.delta = pd.Timedelta(minutes=minutes)
        self.roots = {}
        self.pending = []
        self.last = None
        self.day = None

    def update(self, row, events, context=None):
        start = pd.Timestamp(row.timestamp_utc)
        at = start + self.delta
        day = str(start.tz_convert("America/New_York").date())
        if (
            day != self.day
            or (self.last is not None and start - self.last != self.delta)
            or not valid_bar(row)
        ):
            self.roots = {}
            self.pending = []
        self.day = day
        self.last = start
        if not valid_bar(row):
            return []
        result = []

        def emit(root, kind, direction, components):
            event = {
                **root,
                **(context or {}),
                "interaction_type": kind,
                "compound_interaction": kind,
                "direction": direction,
                "timestamp_utc": at.isoformat(),
                "timestamp_ny": at.tz_convert("America/New_York").isoformat(),
                "bar_start_utc": start.isoformat(),
                "price_at_event": str(row.close),
                "open": str(row.open),
                "high": str(row.high),
                "low": str(row.low),
                "close": str(row.close),
                "root_event_id": root["event_id"],
                "component_event_ids": components,
                "break_confirmation_timestamp": (
                    root["timestamp_utc"]
                    if root["interaction_type"] == "BREAK_ACCEPTANCE"
                    else None
                ),
                "confirmation_timestamp": at.isoformat(),
                "candles_between_stages": int(
                    (at - pd.Timestamp(root["timestamp_utc"])) / self.delta
                ),
                "break_distance_points": abs(
                    float(root["close"]) - float(root["level_price"])
                ),
                "break_body_ratio": root.get("body_ratio"),
                "hold_body_ratio": (
                    abs(float(row.close - row.open)) / float(row.high - row.low)
                    if row.high != row.low
                    else None
                ),
                "hold_candle_range": float(row.high - row.low),
                "touch_number": root["touch_number"],
            }
            atr = root.get("atr14")
            event["break_distance_atr"] = (
                event["break_distance_points"] / float(atr) if atr else None
            )
            event["sequence_id"] = digest([root["event_id"], kind, str(at), components])
            event["event_id"] = event["sequence_id"]
            result.append(event)

        for pending in self.pending:
            root, stage, sign, components = pending
            if pd.Timestamp(stage["timestamp_utc"]) != start:
                continue
            price = float(root["level_price"])
            close = (float(row.close) - price) * sign
            full = (float(row.low) > price) if sign == 1 else float(row.high) < price
            if stage["interaction_type"] == "RETEST":
                if full:
                    emit(
                        root,
                        "BREAK_RETEST_FULL_HOLD",
                        "UP" if sign == 1 else "DOWN",
                        components,
                    )
                    result[-1].update(
                        touch_number=stage["touch_number"],
                        retest_penetration=stage["distance_through_level"],
                        retest_delay=int(
                            (
                                pd.Timestamp(stage["timestamp_utc"])
                                - pd.Timestamp(root["timestamp_utc"])
                            )
                            / self.delta
                        ),
                    )
            elif stage["interaction_type"] == "BREAK_ACCEPTANCE":
                if close > 0:
                    emit(
                        root,
                        "BREAK_NEXT_CANDLE_CLOSE_HOLD",
                        "UP" if sign == 1 else "DOWN",
                        components,
                    )
                if full:
                    emit(
                        root,
                        "BREAK_NEXT_CANDLE_FULL_HOLD",
                        "UP" if sign == 1 else "DOWN",
                        components,
                    )
                if close < 0:
                    emit(
                        root,
                        "BREAK_FAILED_NEXT_CANDLE_HOLD",
                        "UP" if sign == 1 else "DOWN",
                        components,
                    )
            else:
                extreme = float(stage["high"] if sign == 1 else stage["low"])
                if (float(row.close) - extreme) * sign > 0:
                    emit(
                        root,
                        stage["interaction_type"] + "_CONFIRMATION",
                        "UP" if sign == 1 else "DOWN",
                        components,
                    )
        self.pending = []
        for event in events:
            kind = event["interaction_type"]
            key = event["level_id"]
            if kind == "RETEST" and key in self.roots:
                root = self.roots[key]
                sign = 1 if root["direction"] == "UP" else -1
                components = [root["event_id"], event["event_id"]]
                emit(root, "BREAK_RETEST", root["direction"], components)
                side = (float(row.close) - float(root["level_price"])) * sign
                if side:
                    emit(
                        root,
                        "BREAK_RETEST_HOLD" if side > 0 else "BREAK_RETEST_FAIL",
                        root["direction"],
                        components,
                    )
                for r in result:
                    if r.get("component_event_ids") == components:
                        r.update(
                            retest_penetration=event["distance_through_level"],
                            retest_delay=int(
                                (at - pd.Timestamp(root["timestamp_utc"])) / self.delta
                            ),
                            touch_number=event["touch_number"],
                        )
                self.pending.append((root, event, sign, components))
            if kind == "BREAK_ACCEPTANCE":
                self.roots[key] = event
                self.pending.append(
                    (
                        event,
                        event,
                        1 if event["direction"] == "UP" else -1,
                        [event["event_id"]],
                    )
                )
            elif kind in ("SWEEP_RECLAIM", "REJECTION"):
                sign = 1 if event["approach_side"] == "ABOVE" else -1
                self.pending.append((event, event, sign, [event["event_id"]]))
        return result
