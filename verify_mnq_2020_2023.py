from pathlib import Path
import hashlib

import databento as db
import pandas as pd


DATA_DIR = Path(
    "/Users/DayTrade/Documents/Codex/2026-10-06/"
    "1-connect-to-databento-2-request/outputs/data"
)

OLD_FILE = DATA_DIR / (
    "GLBX.MDP3_MNQ.v.0_ohlcv-1m_2024-01-01_2026-10-06.parquet"
)

YEARS = ["2020", "2021", "2022", "2023"]


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


print("=" * 72)
print("NEW DATABENTO FILE VERIFICATION")
print("=" * 72)

for year in YEARS:

    path = DATA_DIR / (
        f"GLBX.MDP3_MNQ.v.0_ohlcv-1m_{year}.dbn.zst"
    )

    print()
    print(f"YEAR: {year}")
    print("-" * 72)

    if not path.exists():
        print("MISSING FILE")
        continue

    store = db.DBNStore.from_file(path)

    # Keep fixed-point integer prices.
    df = store.to_df(
        price_type="fixed",
        pretty_ts=True,
    )

    # ts_event is normally the index for OHLCV data.
    df = df.reset_index()

    print(f"Rows: {len(df):,}")
    print(f"Columns: {list(df.columns)}")

    if "ts_event" in df.columns:
        print(f"First timestamp: {df['ts_event'].min()}")
        print(f"Last timestamp:  {df['ts_event'].max()}")

        duplicates = df["ts_event"].duplicated().sum()

        print(f"Duplicate timestamps: {duplicates:,}")

    ohlc = ["open", "high", "low", "close"]

    missing_ohlc = df[ohlc].isna().any(axis=1).sum()

    invalid_ohlc = (
        (df["high"] < df["low"])
        | (df["open"] > df["high"])
        | (df["open"] < df["low"])
        | (df["close"] > df["high"])
        | (df["close"] < df["low"])
    ).sum()

    print(f"Missing OHLC rows: {missing_ohlc:,}")
    print(f"Invalid OHLC rows: {invalid_ohlc:,}")

    print(f"SHA256: {sha256(path)}")


print()
print("=" * 72)
print("COMPARE AGAINST EXISTING VALIDATED 2024-2026 PARQUET")
print("=" * 72)

if not OLD_FILE.exists():

    print("Existing 2024-2026 parquet was not found:")
    print(OLD_FILE)

else:

    old = pd.read_parquet(OLD_FILE)

    print(f"Existing rows: {len(old):,}")
    print(f"Existing columns: {list(old.columns)}")
    print()
    print("Existing dtypes:")
    print(old.dtypes)

    print()
    print(f"Existing SHA256: {sha256(OLD_FILE)}")


print()
print("VERIFICATION COMPLETE")
