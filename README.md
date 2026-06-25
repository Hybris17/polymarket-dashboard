# Polymarket Dashboard

A live dashboard tracking prediction market odds for the 2026 FIFA World Cup, built with Python and Streamlit.

**Live app:** https://polymarket-dashboard-hybris17.streamlit.app/

## What it does
- Pulls live win probabilities for all active teams from [Polymarket](https://polymarket.com)
- Ranks teams by their current odds
- Tracks how odds change over time and charts the movement
- (Coming soon) AI-written summary of what's driving each team's odds

## Built in public
Following the build from zero — no prior Python experience. Progress posted on LinkedIn.

## Stack
- Python + Streamlit
- Polymarket Gamma API (no key needed)
- SQLite for historical snapshots
- Anthropic API (Claude) for AI summaries — coming soon
