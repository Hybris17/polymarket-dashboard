import sqlite3  # built into Python — no install needed
from datetime import datetime

DB_FILE = "data.db"  # the database lives in a single file in your project folder


def get_connection():
    # Opens (or creates) the database file and returns a connection object
    return sqlite3.connect(DB_FILE)


def create_table():
    # Creates the snapshots table if it doesn't already exist.
    # Each row stores one team's probability at one point in time.
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            team      TEXT NOT NULL,
            prob      REAL NOT NULL,   -- probability as a percentage, e.g. 19.4
            timestamp TEXT NOT NULL    -- when this snapshot was taken
        )
    """)
    conn.commit()
    conn.close()


def should_save_snapshot(min_minutes=30):
    # Returns True only if no snapshot exists yet, or the last one is older than min_minutes.
    conn = get_connection()
    row = conn.execute(
        "SELECT timestamp FROM snapshots ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row is None:
        return True  # database is empty — always save the first snapshot
    last_saved = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    minutes_elapsed = (datetime.utcnow() - last_saved).total_seconds() / 60
    return minutes_elapsed >= min_minutes


def save_snapshot(teams_probs: dict):
    # Saves one snapshot for every team in the dict.
    # teams_probs looks like: {"France": 19.4, "Argentina": 15.8, ...}
    conn = get_connection()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    for team, prob in teams_probs.items():
        conn.execute(
            "INSERT INTO snapshots (team, prob, timestamp) VALUES (?, ?, ?)",
            (team, prob, now),
        )
    conn.commit()
    conn.close()


def get_history(team: str):
    # Returns a list of (timestamp, prob) tuples for a given team, oldest first.
    conn = get_connection()
    rows = conn.execute(
        "SELECT timestamp, prob FROM snapshots WHERE team = ? ORDER BY timestamp ASC",
        (team,),
    ).fetchall()
    conn.close()
    return rows
