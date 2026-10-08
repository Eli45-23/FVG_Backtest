"""Frozen Development candidate. No filesystem access or forward outcomes in this source."""
from decimal import Decimal as D
from types import SimpleNamespace
from engine.strategy import Entry
from engine.research.events import EventDetector
from engine.research.sequences import Sequences
from engine.research.levels import SessionConfig, schedule


class Strategy:
    name = "PDH Failed Break Short v1"
    status = "DEVELOPMENT_ONLY_NOT_VALIDATED"
    feature = "bars"
    inputs = []  # Frozen specification: no filter or target optimization inputs.

    def __init__(self):
        self.sessions = schedule()
        self.detector = EventDetector(SessionConfig())
        self.sequences = Sequences()
        self.roots = {}
        self.day = None

    def on_bar(self, ctx, params):
        day = str(ctx.timestamp.tz_convert("America/New_York").date())
        # This immutable source is deliberately Development-only.
        if not "2020-01-01" <= day < "2024-01-01":
            return None
        if day != self.day:
            self.roots = {}
            self.day = day
        b = ctx.bar
        row = SimpleNamespace(
            timestamp_utc=b.timestamp, open=b.open, high=b.high,
            low=b.low, close=b.close, is_complete_5m=True,
        )
        # Detector itself checks availability <= bar START. Newly confirmed levels
        # cannot be used retroactively inside this candle.
        levels = tuple(l for l in ctx.levels if l.level_type == "PDH")
        raw = self.detector.update(row, levels, self.sessions.get(day))
        for event in raw:
            if event["interaction_type"] == "BREAK_ACCEPTANCE":
                self.roots[event["event_id"]] = event
        compounds = self.sequences.update(row, raw)
        for event in compounds:
            if (
                event["interaction_type"] == "BREAK_FAILED_NEXT_CANDLE_HOLD"
                and event["direction"] == "UP"
                and event["approach_side"] == "BELOW"
                and event["touch_number"] == 1
            ):
                root = self.roots[event["root_event_id"]]
                metadata = dict(
                    candidate_event_id=event["event_id"],
                    root_event_id=root["event_id"],
                    root_observation_id=root["observation_id"],
                    sequence_id=event["sequence_id"],
                    level_id=event["level_id"],
                    pdh=event["level_price"],
                    level_available_at=event["level_available_at"],
                    level_source_date=event["level_source_date"],
                    touch_number=event["touch_number"],
                    break_bar_start=root["bar_start_utc"],
                    failure_bar_start=event["bar_start_utc"],
                    confirmation_timestamp=event["timestamp_utc"],
                    break_high=root["high"],
                    failure_high=event["high"],
                    atr14=ctx.features.get("5m", {}).get("atr14"),
                )
                return Entry(
                    "SHORT", max(D(root["high"]), b.high) + ctx.tick_size,
                    D("1"), metadata=metadata,
                )
        return None
