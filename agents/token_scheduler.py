# agents/token_scheduler.py

import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Path to where the patient queue will be stored
QUEUE_FILE = "data/token_queue.csv"

# Priority mapping
TRIAGE_PRIORITY = {
    "Emergency": 1,
    "Priority": 2,
    "Normal": 3
}

# Load or initialize token queue
def load_queue():
    if os.path.exists(QUEUE_FILE):
        return pd.read_csv(QUEUE_FILE)
    else:
        return pd.DataFrame(columns=["token", "name", "symptoms", "triage_level", "timestamp", "reason"])

# Save the queue back to CSV
def save_queue(queue):
    queue.to_csv(QUEUE_FILE, index=False)

# Assign next available token based on priority rules
def assign_token(name, symptoms, triage_level, reason):
    queue = load_queue()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate new token number
    new_token = 1 if queue.empty else queue["token"].max() + 1

    # Create new entry
    new_entry = {
        "token": new_token,
        "name": name,
        "symptoms": symptoms,
        "triage_level": triage_level,
        "timestamp": now,
        "reason": reason
    }

    # Append to queue
    queue = pd.concat([queue, pd.DataFrame([new_entry])], ignore_index=True)

    # Reorder queue: Emergency → Priority → Normal
    queue["priority"] = queue["triage_level"].map(TRIAGE_PRIORITY)
    queue.sort_values(by=["priority", "timestamp"], inplace=True)
    queue.drop(columns=["priority"], inplace=True)

    save_queue(queue)

    return new_token, queue


# CLI Test
if __name__ == "__main__":
    name = input("Enter patient name: ")
    symptoms = input("Enter symptoms: ")
    triage_level = input("Enter triage (Emergency / Priority / Normal): ")
    reason = input("Reason for triage: ")

    token, updated_queue = assign_token(name, symptoms, triage_level, reason)

    print(f"\n✅ Token assigned: {token}")
    print("\n🧾 Current Queue:\n")
    print(updated_queue.to_string(index=False))
