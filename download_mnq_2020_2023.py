import os
from pathlib import Path

from dotenv import load_dotenv
import databento as db


# ============================================================
# LOAD API KEY
# ============================================================

load_dotenv("/Users/DayTrade/.env")

api_key = os.getenv("DATABENTO_API_KEY")

if not api_key:
    raise RuntimeError(
        "DATABENTO_API_KEY was not found in /Users/DayTrade/.env"
    )


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

output_dir = Path(
    "/Users/DayTrade/Documents/Codex/2026-10-06/"
    "1-connect-to-databento-2-request/outputs/data"
)

output_dir.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABENTO CLIENT
# ============================================================

client = db.Historical(api_key)


# ============================================================
# DOWNLOAD ONE YEAR AT A TIME
# ============================================================

periods = [
    ("2020", "2020-01-01", "2021-01-01"),
    ("2021", "2021-01-01", "2022-01-01"),
    ("2022", "2022-01-01", "2023-01-01"),
    ("2023", "2023-01-01", "2024-01-01"),
]


for label, start, end in periods:

    output_path = output_dir / (
        f"GLBX.MDP3_MNQ.v.0_ohlcv-1m_{label}.dbn.zst"
    )

    # Do not accidentally re-download a completed year.
    if output_path.exists():
        print(f"{label}: already exists, skipping")
        print(f"  {output_path}")
        continue

    print()
    print("=" * 60)
    print(f"Downloading {label}")
    print(f"{start} -> {end}")
    print("=" * 60)

    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        schema="ohlcv-1m",
        symbols="MNQ.v.0",
        stype_in="continuous",
        start=start,
        end=end,
    )

    data.to_file(
        path=output_path,
        mode="x",
        compression="zstd",
    )

    size_mb = output_path.stat().st_size / (1024 * 1024)

    print(f"{label}: COMPLETE")
    print(f"Saved to: {output_path}")
    print(f"File size: {size_mb:.2f} MB")


print()
print("ALL REQUESTED YEARS COMPLETE")
