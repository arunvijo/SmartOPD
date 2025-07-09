# agents/followup_scheduler.py

import pandas as pd
from datetime import datetime, timedelta
import os

HISTORY_PATH = "data/patients.csv"
FOLLOWUP_PATH = "data/followups.csv"

def find_followups():
    if not os.path.exists(HISTORY_PATH):
        return []

    df = pd.read_csv(HISTORY_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    now = pd.Timestamp.now()

    followups = []

    for name, group in df.groupby("name"):
        last_visit = group["timestamp"].max()
        days_since = (now - last_visit).days
        last_triage = group.sort_values("timestamp", ascending=False).iloc[0]["triage"]

        if (
            (last_triage == "Emergency" and days_since >= 3) or
            (last_triage == "Priority" and days_since >= 5)
        ):
            followups.append({
                "name": name,
                "last_triage": last_triage,
                "last_visit": last_visit.strftime("%Y-%m-%d"),
                "days_since": days_since,
                "status": "Follow-up Needed"
            })

    return followups

def save_followups():
    followups = find_followups()
    if followups:
        pd.DataFrame(followups).to_csv(FOLLOWUP_PATH, index=False)
        print(f"✅ {len(followups)} follow-ups saved to {FOLLOWUP_PATH}")
    else:
        print("🔎 No follow-ups needed today.")

if __name__ == "__main__":
    save_followups()
