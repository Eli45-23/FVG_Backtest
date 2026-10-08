import os
from dotenv import load_dotenv
import databento as db

load_dotenv("/Users/DayTrade/.env")

api_key = os.getenv("DATABENTO_API_KEY")

if not api_key:
    raise RuntimeError(
        "DATABENTO_API_KEY was not found in /Users/DayTrade/.env"
    )

client = db.Historical(api_key)

periods = [
    ("2020", "2020-01-01", "2021-01-01"),
    ("2021", "2021-01-01", "2022-01-01"),
    ("2022", "2022-01-01", "2023-01-01"),
    ("2023", "2023-01-01", "2024-01-01"),
]

total = 0.0

for label, start, end in periods:
    print(f"Checking {label}...", flush=True)

    cost = client.metadata.get_cost(
        dataset="GLBX.MDP3",
        symbols="MNQ.v.0",
        schema="ohlcv-1m",
        stype_in="continuous",
        start=start,
        end=end,
    )

    total += cost
    print(f"{label}: ${cost:.2f}", flush=True)

print()
print(f"TOTAL 2020-2023: ${total:.2f}")
