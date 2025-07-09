import json
import os
import pandas as pd

PROFILE_FILE = "data/patient_profiles.json"

def load_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profiles(profiles):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

def update_profile(name, age, gender, disease, triage):
    profiles = load_profiles()

    if name not in profiles:
        profiles[name] = {
            "name": name,
            "age": age,
            "gender": gender,
            "diseases": [],
            "tags": []
        }

    if disease and disease.lower() != "none":
        if disease not in profiles[name]["diseases"]:
            profiles[name]["diseases"].append(disease)

    tags = []

    if len(profiles[name]["diseases"]) >= 2:
        tags.append("chronic")

    if triage == "Emergency":
        tags.append("high-risk")

    visits_df = pd.read_csv("data/patients.csv") if os.path.exists("data/patients.csv") else pd.DataFrame()
    user_visits = visits_df[visits_df["name"] == name]

    if len(user_visits) >= 3:
        tags.append("frequent")

    profiles[name]["tags"] = list(set(tags))
    save_profiles(profiles)

def get_profile(name):
    profiles = load_profiles()
    return profiles.get(name, {})
