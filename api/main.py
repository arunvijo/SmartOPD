# Updated FastAPI Backend (triage agent)
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import os
from agents import crowd_predictor, symptom_triage, token_scheduler, followup_scheduler, future_scheduler, personalization
from utils.speech_utils import speak_token
import threading
import time
from datetime import datetime, timedelta


app = FastAPI()

# In your main FastAPI file

from pydantic import BaseModel
from agents import feedback_analyzer

class FeedbackRequest(BaseModel):
    name: str
    token: int
    triage: str
    feedback: str

@app.post("/feedback")
def submit_feedback(data: FeedbackRequest):
    sentiment = feedback_analyzer.save_feedback(
        data.name,
        data.token,
        data.triage,
        data.feedback
    )
    return {
        "message": "✅ Feedback submitted.",
        "sentiment": sentiment
    }

class PatientRequest(BaseModel):
    name: str
    age: int
    gender: int
    blood_pressure: int
    cholesterol_level: int
    symptoms: str
    disease: str = None

@app.on_event("startup")
def update_agents_periodically():
    def run_periodically():
        while True:
            print("[Updater] Refreshing crowd predictions...")
            crowd_predictor.save_predictions_to_file()
            time.sleep(300)  # Refresh every 5 minutes

    threading.Thread(target=run_periodically, daemon=True).start()

@app.post("/rebook")
def rebook_case(data: dict):
    future_scheduler.save_future_booking(data)
    return {"status": "scheduled", "scheduled_for": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}

@app.post("/reschedule")
def reschedule(data: dict):
    name = data.get("name")
    new_date = data.get("new_date")
    future_scheduler.reschedule_booking(name, new_date)
    return {"status": "rescheduled", "new_date": new_date}

def periodic_followup_runner(interval_minutes=60):
    while True:
        try:
            followup_scheduler.save_followups()
        except Exception as e:
            print("❌ Follow-up Agent Error:", e)
        time.sleep(interval_minutes * 60)

threading.Thread(target=periodic_followup_runner, daemon=True).start()

@app.post("/triage")
def triage(data: PatientRequest):
    crowd_file_path = "data/crowd_density.json"
    if not os.path.exists(crowd_file_path):
        print("⚠️ Crowd file missing. Recomputing...")
        crowd_predictor.save_predictions_to_file()

    history_path = "data/patients.csv"
    past_visits = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()
    past_user = past_visits[past_visits["name"] == data.name]

    features = symptom_triage.extract_features_from_text(data.symptoms)
    features.update({
        "Age": data.age,
        "Gender": data.gender,
        "Blood Pressure": data.blood_pressure,
        "Cholesterol Level": data.cholesterol_level,
    })

    if not past_user.empty:
        recent = pd.to_datetime(past_user["timestamp"]).max()
        days_since_last = (pd.Timestamp.now() - recent).days
        emergencies = past_user[past_user["triage"] == "Emergency"]
        if days_since_last < 7 or len(emergencies) >= 2:
            features["FrequentVisits"] = 1

    result = symptom_triage.triage_decision(features=features, disease_name=data.disease)

    if not result["assign_token"]:
        # Auto-schedule rebooking for tomorrow
        future_scheduler.save_future_booking({
            "name": data.name,
            "symptoms": data.symptoms,
            "triage": result["triage"],
            "reason": result["message"]
        })

        return {
            "token": None,
            "triage": result["triage"],
            "reason": result["message"],
            "suggested_action": "You’ve been automatically rebooked for tomorrow due to high crowd. Please visit again."
        }

    # Token assigned
    token, queue = token_scheduler.assign_token(
        data.name, data.symptoms, result["triage"], result["message"]
    )

    threading.Thread(target=speak_token, args=(int(token), data.name)).start()

    record = {
        "name": data.name,
        "age": data.age,
        "gender": data.gender,
        "blood_pressure": data.blood_pressure,
        "cholesterol_level": data.cholesterol_level,
        "symptoms": data.symptoms,
        "disease": data.disease or "",
        "triage": result["triage"],
        "token": int(token),
        "timestamp": pd.Timestamp.now(),
        "feedback": ""
    }

    df_record = pd.DataFrame([record])
    df_record.to_csv(history_path, mode='a', header=not os.path.exists(history_path), index=False)

    personalization.update_profile(
        data.name,
        data.age,
        data.gender,
        data.disease,
        result["triage"]
    )

    return {
        "token": int(token),
        "triage": result["triage"],
        "reason": result["message"],
        "suggested_action": "Proceed to OPD. Token generated."
    }


@app.get("/followups")
def get_followups():
    if os.path.exists("data/followups.csv"):
        df = pd.read_csv("data/followups.csv")
        return df.to_dict(orient="records")
    return []


