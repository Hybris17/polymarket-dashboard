"""
Run this script ONCE to populate the database with historical price data from Polymarket.
Usage: python3 backfill.py
"""
import requests
import json
from datetime import datetime
from database import create_table, insert_historical_snapshot
import sqlite3

DB_FILE = "data.db"

# Step 1: clear existing snapshots so we start fresh from historical data
def clear_snapshots():
    conn = sqlite3.connect(DB_FILE)
    count = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
    conn.execute("DELETE FROM snapshots")
    conn.commit()
    conn.close()
    print(f"Cleared {count} existing snapshots.")

# Step 2: fetch ALL World Cup markets, including eliminated teams
def fetch_all_markets():
    print("Fetching all World Cup markets from Polymarket...")
    response = requests.get(
        "https://gamma-api.polymarket.com/events",
        params={"slug": "world-cup-winner"},
    )
    response.raise_for_status()
    markets = response.json()[0]["markets"]
    print(f"Found {len(markets)} markets (active + eliminated).\n")
    return markets

# Step 3: for each team, fetch daily price history and store it
def backfill_team(team, yes_token_id):
    response = requests.get(
        "https://clob.polymarket.com/prices-history",
        params={
            "market": yes_token_id,
            "interval": "max",   # go as far back as possible
            "fidelity": 1440,    # one data point per day (1440 minutes)
        },
    )
    if response.status_code != 200:
        print(f"  {team}: skipped (API error {response.status_code})")
        return 0

    history = response.json().get("history", [])
    if not history:
        print(f"  {team}: skipped (no data)")
        return 0

    for point in history:
        # convert Unix timestamp → readable date string
        timestamp = datetime.utcfromtimestamp(point["t"]).strftime("%Y-%m-%d %H:%M:%S")
        prob = round(point["p"] * 100, 1)  # 0.174 → 17.4
        insert_historical_snapshot(team, prob, timestamp)

    return len(history)


if __name__ == "__main__":
    create_table()
    clear_snapshots()

    markets = fetch_all_markets()

    for market in markets:
        team = market.get("groupItemTitle", "Unknown")

        # clobTokenIds is a JSON string — parse it to get the list
        raw_ids = market.get("clobTokenIds")
        if not raw_ids:
            print(f"  {team}: skipped (no token ID)")
            continue

        token_ids = json.loads(raw_ids)
        yes_token_id = token_ids[0]  # index 0 = "Yes" token

        count = backfill_team(team, yes_token_id)
        if count:
            print(f"  {team}: {count} days of data saved")

    print("\nBackfill complete. Restart the Streamlit app to see the charts.")
