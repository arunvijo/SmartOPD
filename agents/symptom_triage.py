# agents/symptom_triage.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

def classify_symptoms(symptom_text):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://smartopd.local",  # optional: set your site or localhost
        "X-Title": "SmartOPD-Triage"
    }

    system_prompt = "You are a medical triage assistant in a government hospital in India."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""
Given the patient's symptoms, classify their case as one of the following:
- Emergency (life-threatening, immediate care)
- Priority (serious, needs to be seen soon)
- Normal (routine issues)

Patient says: "{symptom_text}"

Respond in this format:
1. Classification
2. Reason
3. Suggested action
"""}
    ]

    payload = {
        "model": "mistralai/mistral-7b-instruct",  # or try openchat, llama3
        "messages": messages,
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"

if __name__ == "__main__":
    symptom_input = input("Describe your symptoms: ")
    result = classify_symptoms(symptom_input)
    print("\nTriage Result:\n", result)
