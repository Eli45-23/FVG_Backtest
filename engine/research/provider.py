"""Read-only level provider for ordinary strategies with restricted callback schedules."""

import pandas as pd
import pyarrow.parquet as pq
from engine.research.levels import LevelEngine, SessionConfig, FIVE, NY
from engine.research.profiles import profile


class CausalLevelSource:
    """Public API returns known level snapshots; source rows remain private to the provider.

    Trusted Python is not a sandbox. Private attributes are not a security boundary.
    Feed a chronological source or use from_profile(). Queries must move forward in time.
    """

    def __init__(self, rows, config=SessionConfig(), sessions=None, identity=None):
        self._rows = iter(rows)
        self._next = next(self._rows, None)
        self._engine = LevelEngine(config, sessions)
        self._last_query = None
        self.identity = identity

    @classmethod
    def from_profile(cls, profile_id="legacy_2024_2026", config=SessionConfig()):
        source = profile(profile_id)
        bars = pq.read_table(source.bars).to_pandas().sort_values("timestamp_utc")
        if bars.timestamp_utc.duplicated().any():
            raise ValueError("Duplicate level source bars")
        return cls(bars.itertuples(index=False), config, identity=source.identity())

    def at(self, confirmed_timestamp):
        at = pd.Timestamp(confirmed_timestamp)
        if at.tzinfo is None or (
            self._last_query is not None and at < self._last_query
        ):
            raise ValueError(
                "Level queries require aware, nondecreasing confirmation times"
            )
        self._last_query = at
        while self._next is not None and self._next.timestamp_utc + FIVE <= at:
            self._engine.update(self._next)
            self._next = next(self._rows, None)
        day = str(at.tz_convert(NY).date())
        return tuple(
            level for level in self._engine.active(at) if level.trading_date == day
        )
