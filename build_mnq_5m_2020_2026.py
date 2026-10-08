from pathlib import Path
import json

import pyarrow.parquet as pq

from outputs.build_5m import (
    build_bars,
    validate_all,
    write_parquet,
    sha256,
)


DATA_DIR = Path(
    "/Users/DayTrade/Documents/Codex/2026-10-06/"
    "1-connect-to-databento-2-request/outputs/data"
)

SOURCE = DATA_DIR / (
    "GLBX.MDP3_MNQ.v.0_ohlcv-1m_2020-01-01_2026-10-06.parquet"
)

OUTPUT = DATA_DIR / (
    "MNQ_5m_2020-01-01_2026-10-06.parquet"
)

REPORT = DATA_DIR / (
    "MNQ_5m_2020-01-01_2026-10-06_validation.json"
)


if not SOURCE.exists():
    raise FileNotFoundError(SOURCE)

if OUTPUT.exists():
    raise FileExistsError(
        f"Output already exists:\n{OUTPUT}\n"
        "Refusing to overwrite it."
    )


print("=" * 72)
print("BUILDING VALIDATED MNQ 5-MINUTE DATA: 2020-2026")
print("=" * 72)

source_hash_before = sha256(SOURCE)

print(f"Source:")
print(SOURCE)
print()
print(f"Source SHA256:")
print(source_hash_before)

print()
print("Reading raw 1-minute parquet...")

raw = pq.read_table(SOURCE).to_pandas()

print(f"1-minute rows: {len(raw):,}")

print()
print("Building 5-minute bars with existing validated bar engine...")

bars = build_bars(raw)

print()
print("Running full independent reconciliation...")

report = validate_all(raw, bars)

source_hash_after = sha256(SOURCE)

if source_hash_before != source_hash_after:
    raise RuntimeError(
        "Master 1-minute source changed during 5-minute build."
    )


print()
print("Writing new 5-minute parquet...")

write_parquet(
    bars,
    OUTPUT,
    source_hash_before,
)


# ============================================================
# READ-BACK CHECK
# ============================================================

saved = pq.read_table(OUTPUT).to_pandas()

if len(saved) != len(bars):
    raise RuntimeError(
        "Saved 5-minute row count differs from in-memory result."
    )


# ============================================================
# ADD EXTRA REPORTING
# ============================================================

report.update(
    {
        "source_path": str(SOURCE),
        "output_path": str(OUTPUT),
        "raw_sha256": source_hash_before,
        "raw_file_unchanged": True,
        "output_sha256": sha256(OUTPUT),
        "timestamp_convention": "Bar start, [t,t+5min)",
    }
)

REPORT.write_text(
    json.dumps(report, indent=2) + "\n"
)


# ============================================================
# YEAR COUNTS
# ============================================================

print()
print("=" * 72)
print("BUILD COMPLETE")
print("=" * 72)

print(f"5-minute bars: {len(bars):,}")
print(f"Complete bars: {int(bars['is_complete_5m'].sum()):,}")
print(
    f"Incomplete bars: "
    f"{int((~bars['is_complete_5m']).sum()):,}"
)

print(
    f"First timestamp UTC: "
    f"{bars['timestamp_utc'].iloc[0]}"
)

print(
    f"Last timestamp UTC:  "
    f"{bars['timestamp_utc'].iloc[-1]}"
)

print()
print("5-minute bars by NY calendar year:")

year_counts = (
    bars.groupby(
        bars["timestamp_ny"].dt.year
    )
    .size()
)

for year, count in year_counts.items():
    print(f"  {year}: {count:,}")

print()
print(f"RTH bars:       {int(bars['is_rth'].sum()):,}")
print(f"Premarket bars: {int(bars['is_premarket'].sum()):,}")
print(f"Postmarket bars:{int(bars['is_postmarket'].sum()):,}")

print()
print(f"Output:")
print(OUTPUT)

print()
print("Output SHA256:")
print(sha256(OUTPUT))

print()
print(f"Validation report:")
print(REPORT)

print()
print("Source master remained unchanged: YES")
print("FULL BAR RECONCILIATION: PASSED")
