import requests  # third-party library for making HTTP requests (install with pip)

# The Gamma API is Polymarket's public market metadata API — no key needed
API_URL = "https://gamma-api.polymarket.com/markets"

# Ask for 5 active (not yet resolved) markets
params = {
    "limit": 5,
    "active": "true",
}

print("Fetching markets from Polymarket...\n")

# Make the HTTP GET request; raise an error if something goes wrong
response = requests.get(API_URL, params=params)
response.raise_for_status()  # crashes loudly if the server returned an error code

markets = response.json()  # parse the JSON response into a Python list

for market in markets:
    question = market["question"]
    outcomes = market["outcomes"]        # e.g. '["Yes", "No"]' — stored as a string
    prices = market["outcomePrices"]     # e.g. '["0.515", "0.485"]' — also a string

    # The API returns these as JSON strings inside the object, so we parse them
    import json
    outcomes = json.loads(outcomes)
    prices = json.loads(prices)

    print(f"Market: {question}")
    for outcome, price in zip(outcomes, prices):
        # Price is a probability: 0.515 means 51.5% chance
        print(f"  {outcome}: {float(price) * 100:.1f}%")
    print()  # blank line between markets
