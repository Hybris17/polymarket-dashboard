import streamlit as st
import requests
import json
import pandas as pd
import anthropic
from dotenv import load_dotenv
from database import create_table, save_snapshot, should_save_snapshot, get_history

# Load the ANTHROPIC_API_KEY from the .env file into the environment
load_dotenv()

# Make sure the database and table exist before we do anything else
create_table()

# Flag emoji for each team
FLAGS = {
    "France": "🇫🇷", "Argentina": "🇦🇷", "Spain": "🇪🇸", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Portugal": "🇵🇹", "Netherlands": "🇳🇱", "Brazil": "🇧🇷", "Germany": "🇩🇪",
    "USA": "🇺🇸", "Norway": "🇳🇴", "Colombia": "🇨🇴", "Japan": "🇯🇵",
    "Morocco": "🇲🇦", "Mexico": "🇲🇽", "Belgium": "🇧🇪", "Switzerland": "🇨🇭",
    "Ivory Coast": "🇨🇮", "Croatia": "🇭🇷", "Canada": "🇨🇦", "Senegal": "🇸🇳",
    "Austria": "🇦🇹", "Egypt": "🇪🇬", "Sweden": "🇸🇪", "South Korea": "🇰🇷",
    "Ghana": "🇬🇭", "Bosnia-Herzegovina": "🇧🇦", "Uruguay": "🇺🇾", "Ecuador": "🇪🇨",
    "Cape Verde": "🇨🇻", "Australia": "🇦🇺", "New Zealand": "🇳🇿", "Curaçao": "🇨🇼",
    "Iran": "🇮🇷", "Algeria": "🇩🇿", "Paraguay": "🇵🇾", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Uzbekistan": "🇺🇿", "Iraq": "🇮🇶", "South Africa": "🇿🇦", "Congo DR": "🇨🇩",
    "Saudi Arabia": "🇸🇦",
}

st.title("2026 FIFA World Cup Odds")
st.caption("Live win probabilities from Polymarket")

from datetime import datetime, timezone
st.caption(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

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

# --- Fetch Kalshi odds ---
KALSHI_NAME_MAP = {
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
}

kalshi_teams = {}
try:
    kalshi_markets = requests.get(
        "https://external-api.kalshi.com/trade-api/v2/markets",
        params={"limit": 100, "series_ticker": "KXMENWORLDCUP", "status": "open"},
    ).json().get("markets", [])

    for m in kalshi_markets:
        name = m.get("yes_sub_title")
        bid = m.get("yes_bid_dollars")
        ask = m.get("yes_ask_dollars")
        if name and bid and ask:
            prob = round((float(bid) + float(ask)) / 2 * 100, 1)
            name = KALSHI_NAME_MAP.get(name, name)
            kalshi_teams[name] = prob
except Exception:
    pass  # if Kalshi is down, skip silently

# --- Show the leaderboard ---
st.subheader("Current win probabilities")

# Sort teams from highest to lowest probability
sorted_teams = sorted(teams.items(), key=lambda x: -x[1])

# Build a simple table using a pandas DataFrame — show top 10 by default
show_all = st.toggle("Show all teams")
display_teams = sorted_teams if show_all else sorted_teams[:10]

df = pd.DataFrame(display_teams, columns=["Team", "Polymarket (%)"])
df["Kalshi (%)"] = df["Team"].apply(lambda t: kalshi_teams.get(t))
df["Team"] = df["Team"].apply(lambda t: f"{FLAGS.get(t, '')} {t}")
df.index += 1
st.dataframe(
    df,
    use_container_width=True,
    column_config={
        "Polymarket (%)": st.column_config.ProgressColumn(
            "Polymarket (%)", min_value=0, max_value=100, format="%.1f%%",
        ),
        "Kalshi (%)": st.column_config.ProgressColumn(
            "Kalshi (%)", min_value=0, max_value=100, format="%.1f%%",
        ),
    },
)

# --- Today's matches ---
st.subheader("Today's matches")

try:
    fixtures = requests.get(
        "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
    ).json().get("events", [])

    if not fixtures:
        st.info("No matches scheduled today.")
    else:
        for match in fixtures:
            competitors = match["competitions"][0]["competitors"]
            home = competitors[0]["team"]["displayName"]
            away = competitors[1]["team"]["displayName"]
            status = match["status"]["type"]["description"]

            # parse the UTC kickoff time into a readable string
            kickoff_utc = datetime.strptime(match["date"], "%Y-%m-%dT%H:%MZ")
            kickoff_str = kickoff_utc.strftime("%d %b %Y, %H:%M UTC")

            home_prob = teams.get(home, None)
            away_prob = teams.get(away, None)

            col1, col2, col3 = st.columns([2, 1, 2])
            col1.metric(
                label=f"{FLAGS.get(home, '')} {home}",
                value=f"{home_prob}%" if home_prob else "—",
            )
            col2.markdown("<div style='text-align:center; padding-top:24px'>vs</div>", unsafe_allow_html=True)
            col3.metric(
                label=f"{FLAGS.get(away, '')} {away}",
                value=f"{away_prob}%" if away_prob else "—",
            )
            st.caption(f"{status} · {kickoff_str}")
            st.divider()

except Exception:
    st.info("Could not load today's fixtures.")

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

# --- AI summary ---
st.subheader("What's driving these odds?")

if st.button(f"Explain {selected_team}'s chances"):
    with st.spinner("Asking Claude..."):
        client = anthropic.Anthropic()  # automatically reads ANTHROPIC_API_KEY from environment
        prob = teams[selected_team]

        prompt = (
            f"The prediction market Polymarket currently gives {selected_team} "
            f"a {prob}% probability of winning the 2026 FIFA World Cup. "
            f"In 3 sentences, explain what is likely driving this probability — "
            f"consider their recent tournament performance, squad strength, and bracket position. "
            f"Be specific and concise."
        )

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",  # fast and cheap — good for short summaries
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        summary = message.content[0].text
        st.write(summary)
