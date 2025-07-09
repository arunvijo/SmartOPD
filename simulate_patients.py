# Let's modify simulate_patients.py to include auto-generated feedback entries.
# We will also remove the call to Prophet-based forecasting from simulation since it's causing import issues.

# First, let's prepare a version of simulate_patients.py that:
# - Generates 100 random patients
# - Adds them to patients.csv
# - Assigns them random tokens and triage levels
# - Generates some follow-ups and future tokens
# - Creates a feedback.csv with auto-generated feedback and sentiments (random)

import pandas as pd
import random
import os
from datetime import datetime, timedelta
import json

# Seed for reproducibility
random.seed(42)

# Simulate 100 patients
names = [f"Patient{i}" for i in range(1, 101)]
triage_levels = ["Emergency", "Priority", "Normal"]
symptoms = ["headache", "chest pain", "fever", "cough", "fatigue", "breathing difficulty", "dizziness", "nausea"]
reasons = ["checkup", "follow-up", "new issue", "consultation", "pain"]

now = datetime.now()
patients = []
token_queue = []
followups = []
future_tokens = []
feedbacks = []

for i, name in enumerate(names, 1):
    age = random.randint(10, 75)
    gender = random.choice(["male", "female"])
    bp = random.choice(["low", "normal", "high"])
    chol = random.choice(["low", "normal", "high"])
    triage = random.choices(triage_levels, weights=[0.2, 0.5, 0.3])[0]
    symptom = random.choice(symptoms)
    timestamp = now - timedelta(minutes=random.randint(0, 1440))
    reason = random.choice(reasons)

    patients.append({
        "name": name,
        "age": age,
        "gender": gender,
        "blood_pressure": bp,
        "cholesterol_level": chol,
        "triage": triage,
        "symptoms": symptom,
        "disease": "none",
        "timestamp": timestamp
    })

    token_queue.append({
        "token": i,
        "name": name,
        "symptoms": symptom,
        "triage_level": triage,
        "timestamp": timestamp,
        "reason": reason
    })

    # Randomly assign 20 follow-ups
    if random.random() < 0.2:
        date = now + timedelta(days=random.randint(-2, 3))
        followups.append({"name": name, "date": date.strftime("%Y-%m-%d")})

    # Randomly assign 15 future tokens
    if random.random() < 0.15:
        future_tokens.append({
            "name": name,
            "date": (now + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d"),
            "time": f"{random.randint(9, 16)}:00"
        })

    # Randomly generate feedback
    feedback_text = random.choice([
        "Great service", "Too much waiting", "Doctor was kind", "Unclear instructions", "Very satisfied", "Had to wait long"
    ])
    sentiment = "positive" if "great" in feedback_text.lower() or "kind" in feedback_text.lower() or "satisfied" in feedback_text.lower() else "negative"
    feedbacks.append({
        "name": name,
        "token": i,
        "triage": triage,
        "feedback": feedback_text,
        "sentiment": sentiment
    })

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Save all files
pd.DataFrame(patients).to_csv("data/patients.csv", index=False)
pd.DataFrame(token_queue).to_csv("data/token_queue.csv", index=False)
pd.DataFrame(followups).to_csv("data/followups.csv", index=False)
pd.DataFrame(future_tokens).to_csv("data/future_tokens.csv", index=False)
pd.DataFrame(feedbacks).to_csv("data/feedback.csv", index=False)

"✅ Simulation complete with 100 patients and feedback data generated."

