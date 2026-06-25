import streamlit as st  # the library that turns Python into a web app
import requests
import json

# This is the page title that appears in the browser tab and at the top of the app
st.title("Polymarket Dashboard")
st.caption("Live prediction market odds from Polymarket")

# A button the user can click to reload data — when clicked, Streamlit reruns the script
if st.button("Refresh odds"):
    st.rerun()

# --- Fetch data from the Polymarket API ---
# We wrap this in st.spinner() so the user sees a loading message while waiting
with st.spinner("Fetching markets..."):
    response = requests.get(
        "https://gamma-api.polymarket.com/markets",
        params={"limit": 10, "active": "true"},
    )
    response.raise_for_status()
    markets = response.json()

# --- Display each market ---
for market in markets:
    question = market["question"]
    outcomes = json.loads(market["outcomes"])      # convert string → Python list
    prices = json.loads(market["outcomePrices"])   # same here

    # st.subheader renders a bold section title for each market question
    st.subheader(question)

    # st.columns splits the row into N equal columns — one per outcome
    cols = st.columns(len(outcomes))
    for col, outcome, price in zip(cols, outcomes, prices):
        probability = float(price) * 100  # convert 0.515 → 51.5
        # st.metric shows a label + a big number — clean and readable
        col.metric(label=outcome, value=f"{probability:.1f}%")

    st.divider()  # draws a horizontal line between markets
