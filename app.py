import streamlit as st
import requests
import json
import pandas as pd
from database import create_table, save_snapshot, should_save_snapshot, get_history

# Make sure the database and table exist before we do anything else
create_table()

st.title("2026 FIFA World Cup Odds")
st.caption("Live win probabilities from Polymarket")

if st.button("Refresh odds"):
    st.rerun()

# --- Fetch the World Cup event from Polymarket ---
with st.spinner("Fetching latest odds..."):
    response = requests.get(
        "https://gamma-api.polymarket.com/events",
        params={"slug": "world-cup-winner"},
    )
    response.raise_for_status()
    event = response.json()[0]  # the API returns a list; we want the first (only) result
    markets = event["markets"]

# --- Extract only active (not yet eliminated) teams ---
teams = {}
for market in markets:
    if not market.get("active") or market.get("closed"):
        continue  # skip eliminated teams
    team = market["groupItemTitle"]
    yes_price = float(json.loads(market["outcomePrices"])[0])  # "Yes" = team wins
    teams[team] = round(yes_price * 100, 1)  # convert 0.194 → 19.4

# --- Save a snapshot only if 30+ minutes have passed since the last one ---
if should_save_snapshot(min_minutes=30):
    save_snapshot(teams)

# --- Show the leaderboard ---
st.subheader("Current win probabilities")

# Sort teams from highest to lowest probability
sorted_teams = sorted(teams.items(), key=lambda x: -x[1])

# Build a simple table using a pandas DataFrame
df = pd.DataFrame(sorted_teams, columns=["Team", "Win probability (%)"])
df.index += 1  # start ranking at 1 instead of 0
st.dataframe(df, use_container_width=True)

# --- Show historical chart for a selected team ---
st.subheader("Track a team over time")

team_names = [team for team, _ in sorted_teams]
selected_team = st.selectbox("Choose a team", team_names)

# Show the current probability clearly so you can confirm it updates when you switch teams
st.metric(label=f"{selected_team} current win probability", value=f"{teams[selected_team]}%")

history = get_history(selected_team)

if len(history) < 2:
    st.info("Not enough data yet — come back after a few page loads to see the chart.")
else:
    # Build a DataFrame from the history rows: (timestamp, prob)
    history_df = pd.DataFrame(history, columns=["Time", "Win probability (%)"])
    history_df["Time"] = pd.to_datetime(history_df["Time"])
    history_df = history_df.set_index("Time")
    st.line_chart(history_df)
