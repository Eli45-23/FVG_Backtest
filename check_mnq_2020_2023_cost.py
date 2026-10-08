import os
from dotenv import load_dotenv
import databento as db

load_dotenv("/Users/DayTrade/.env")

api_key = os.getenv("DATABENTO_API_KEY")

if not api_key:
    raise RuntimeError("DATABENTO_API_KEY was not found in /Users/DayTrade/.env")

client = db.Historical(api_key)

cost = client.metadata.get_cost(
    dataset="GLBX.MDP3",
    symbols="MNQ.v.0",
    schema="ohlcv-1m",
    stype_in="continuous",
    start="2020-01-01",
    end="2024-01-01",
)

print(f"Estimated cost: ${cost:.2f}")
