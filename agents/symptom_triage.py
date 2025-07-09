# agents/symptom_triage.py
import pickle
import pandas as pd
import json

# Load ML model and label encoder
with open("models/triage_model.pkl", "rb") as f:
    model, label_encoder = pickle.load(f)

# Path to crowd prediction file
CROWD_FILE = "data/crowd_density.json"  # This should be updated by your crowd_predictor agent

# Load crowd density (assume it's saved by your crowd predictor)
def is_crowd_high(threshold=50):
    try:
        with open("data/crowd_density.json", "r") as f:
            forecast = json.load(f)
            latest_count = forecast[-1]["predicted_patients"]  # Use last hour’s prediction
            return latest_count >= threshold
    except Exception as e:
        print("⚠️ Could not read crowd file:", e)
        return False

# Classify using trained ML model
def classify_symptoms(features: dict):
    input_df = pd.DataFrame([features])
    prediction = model.predict(input_df)[0]
    triage = label_encoder.inverse_transform([prediction])[0]
    return triage


# Add this function to symptom_triage.py
def extract_features_from_text(symptom_text: str):
    symptom_text = symptom_text.lower()

    def keyword_found(keyword):
        return int(keyword in symptom_text)

    features = {
        "Fever": keyword_found("fever"),
        "Cough": keyword_found("cough"),
        "Fatigue": keyword_found("fatigue"),
        "Difficulty Breathing": int("shortness of breath" in symptom_text or "difficulty breathing" in symptom_text),
        "Age": 30,  # Default if unknown
        "Gender": 1,  # Assume Male (1); Female=0
        "Blood Pressure": 1,  # Normal
        "Cholesterol Level": 1  # Normal
    }

    return features



# Main triage logic
def triage_decision(features: dict, disease_name: str = None):
    triage = classify_symptoms(features)
    high_crowd = is_crowd_high()

    if triage == "Normal" and high_crowd:
        return {
            "triage": triage,
            "assign_token": False,
            "message": f"Due to high crowd, '{disease_name or 'your condition'}' can be managed at home. Please consult later or via telemedicine."
        }
    else:
        return {
            "triage": triage,
            "assign_token": True,
            "message": "Token assigned. Please wait for your turn at the OPD."
        }


# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv()
# api_key = os.getenv("OPENROUTER_API_KEY")

# def classify_symptoms(symptom_text):
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json",
#         "HTTP-Referer": "https://smartopd.local",  # optional: set your site or localhost
#         "X-Title": "SmartOPD-Triage"
#     }

#     system_prompt = "You are a medical triage assistant in a government hospital in India."

#     messages = [
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": f"""
# Given the patient's symptoms, classify their case as one of the following:
# - Emergency (life-threatening, immediate care)
# - Priority (serious, needs to be seen soon)
# - Normal (routine issues)

# Patient says: "{symptom_text}"

# Respond in this format:
# 1. Classification
# 2. Reason
# 3. Suggested action
# """}
#     ]

#     payload = {
#         "model": "mistralai/mistral-7b-instruct",  # or try openchat, llama3
#         "messages": messages,
#     }

#     response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

#     if response.status_code == 200:
#         return response.json()['choices'][0]['message']['content']
#     else:
#         return f"Error: {response.status_code} - {response.text}"

# if __name__ == "__main__":
#     symptom_input = input("Describe your symptoms: ")
#     result = classify_symptoms(symptom_input)
#     print("\nTriage Result:\n", result)