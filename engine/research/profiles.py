"""Explicit read-only research datasets. Does not alter engine.data legacy identity."""

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
import hashlib
import pyarrow.parquet as pq
from engine.legacy import ROOT


@dataclass(frozen=True)
class DatasetProfile:
    id: str
    start: str
    end: str
    minutes: Path
    bars: Path

    def validate(self, start, end):
        a, b = date.fromisoformat(start), date.fromisoformat(end)
        if not date.fromisoformat(self.start) <= a < b <= date.fromisoformat(self.end):
            raise ValueError(f"Dates must lie in [{self.start}, {self.end})")

    def identity(self):
        return {
            "profile": self.id,
            "start": self.start,
            "end": self.end,
            "files": {
                k: {
                    "name": p.name,
                    "sha256": file_hash(p),
                    "rows": pq.ParquetFile(p).metadata.num_rows,
                }
                for k, p in [("minutes", self.minutes), ("bars", self.bars)]
            },
        }


@lru_cache(maxsize=16)
def _hash(path, size, mtime):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def file_hash(path):
    s = path.stat()
    return _hash(str(path), s.st_size, s.st_mtime_ns)


def profile(id):
    starts = {"legacy_2024_2026": "2024-01-01", "research_2020_2026": "2020-01-01"}
    if id not in starts:
        raise ValueError("Unknown dataset profile")
    start, end = starts[id], "2026-10-06"
    root = ROOT / "outputs/data"
    return DatasetProfile(
        id,
        start,
        end,
        root / f"GLBX.MDP3_MNQ.v.0_ohlcv-1m_{start}_{end}.parquet",
        root / f"MNQ_5m_{start}_{end}.parquet",
    )


SEGMENTS = {
    "development": ("2020-01-01", "2024-01-01"),
    "validation": ("2024-01-01", "2025-01-01"),
    "out-of-sample": ("2025-01-01", "2026-10-06"),
}


def validate_segment(id, segment, start, end):
    profile(id).validate(start, end)
    if segment not in SEGMENTS:
        raise ValueError("Unknown research segment")
    a, b = SEGMENTS[segment]
    if not a <= start < end <= b:
        raise ValueError(f"{segment} requires dates within [{a}, {b})")
