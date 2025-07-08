from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from agents import crowd_predictor, symptom_triage, token_scheduler
from utils.speech_utils import speak_token
import os
import re

app = FastAPI()

class PatientRequest(BaseModel):
    name: str
    symptoms: str

@app.get("/")
def root():
    return {"message": "SmartOPD FastAPI is running!"}


@app.get("/predict")
def predict():
    df = crowd_predictor.predict_next_day()
    # Convert all columns to native Python types
    df['datetime'] = df['datetime'].astype(str)
    df['predicted_patients'] = df['predicted_patients'].astype(int)
    return df.to_dict(orient="records")



@app.post("/triage")
def triage(data: PatientRequest):
    output = symptom_triage.classify_symptoms(data.symptoms)

    # Extract values using regex
    classification_match = re.search(r"1\.\s*(.*)", output)
    reason_match = re.search(r"2\.\s*(.*)", output)

    triage_level = classification_match.group(1).strip() if classification_match else "Normal"
    reason = reason_match.group(1).strip() if reason_match else "Not provided"

    token, queue = token_scheduler.assign_token(
        data.name, data.symptoms, triage_level, reason
    )

    speak_token(token, data.name)  # voice callout

    return {
        "token": token,
        "triage": triage_level,
        "reason": reason
    }


@app.get("/queue")
def get_queue():
    df = pd.read_csv("data/token_queue.csv")
    return df.to_dict(orient="records")
