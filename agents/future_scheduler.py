import pandas as pd
from datetime import datetime, timedelta
import os

FUTURE_TOKEN_FILE = "data/future_tokens.csv"

def save_future_booking(data: dict):
    df = pd.DataFrame([{
        "name": data["name"],
        "symptoms": data["symptoms"],
        "triage": data["triage"],
        "scheduled_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "status": "pending",
        "reason": data.get("reason", "Low severity + crowd")
    }])

    header = not os.path.exists(FUTURE_TOKEN_FILE)
    df.to_csv(FUTURE_TOKEN_FILE, mode='a', index=False, header=header)
    print(f"🕓 Rebooking added for {data['name']}")

def get_future_bookings():
    if os.path.exists(FUTURE_TOKEN_FILE):
        return pd.read_csv(FUTURE_TOKEN_FILE)
    return pd.DataFrame(columns=["name", "symptoms", "triage", "scheduled_date", "status", "reason"])

def reschedule_booking(name: str, new_date: str):
    df = get_future_bookings()
    df.loc[df["name"] == name, ["scheduled_date", "status"]] = [new_date, "rescheduled"]
    df.to_csv(FUTURE_TOKEN_FILE, index=False)
    return True


def run_future_appointments():
    save_future_booking()