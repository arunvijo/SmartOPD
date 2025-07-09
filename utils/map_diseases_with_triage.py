import pandas as pd
import requests
import os
import time
import re
from dotenv import load_dotenv

print("🔧 Loading environment variables...")
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("❌ OPENROUTER_API_KEY not found in .env file.")
    exit()
print("✅ API key loaded.\n")

# Setup API headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://smartopd.local",
    "X-Title": "SmartOPD-Triage"
}
print("✅ API headers set.\n")

# Function to get triage info
def get_triage_info(disease):
    print(f"🧠 Sending request to classify: {disease}")
    prompt = f"""
You are a medical triage assistant in a government hospital in India.

Given the disease name, classify it into:
- Emergency
- Priority
- Normal

Respond in this format:
1. Classification
2. Reason
3. Suggested action

Disease: {disease}
"""

    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a medical triage assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            classification = re.search(r"1\.\s*(.*)", content)
            reason = re.search(r"2\.\s*(.*)", content)
            action = re.search(r"3\.\s*(.*)", content)

            print(f"✅ Got classification: {classification.group(1).strip() if classification else 'Normal'}\n")
            return {
                "TriageLevel": classification.group(1).strip() if classification else "Normal",
                "Reason": reason.group(1).strip() if reason else "Not specified",
                "SuggestedAction": action.group(1).strip() if action else "Not specified"
            }
        else:
            print(f"❌ API error {response.status_code}: {response.text}")
            return {
                "TriageLevel": "Normal",
                "Reason": "API Error",
                "SuggestedAction": "Check manually"
            }
    except Exception as e:
        print(f"❌ Exception during request: {e}")
        return {
            "TriageLevel": "Normal",
            "Reason": "Request Exception",
            "SuggestedAction": "Check manually"
        }

# Load your original dataset
try:
    df = pd.read_csv("data/known_diseases.csv")
    print(f"📄 Loaded dataset with {len(df)} rows.")
except FileNotFoundError:
    print("❌ File not found: data/known_diseases.csv")
    exit()

# Dictionary to cache disease → triage info
disease_triage_map = {}

unique_diseases = df["Disease"].dropna().unique()
print(f"🔍 Found {len(unique_diseases)} unique diseases.\n")

# Loop through diseases and get triage info
for idx, disease in enumerate(unique_diseases, 1):
    print(f"({idx}/{len(unique_diseases)}) Processing: {disease}")
    info = get_triage_info(disease)
    disease_triage_map[disease] = info
    time.sleep(1)  # ⏱ Avoid hitting rate limits

# Append triage info to each row
print("\n📦 Appending triage info to dataset rows...")
df["TriageLevel"] = df["Disease"].map(lambda d: disease_triage_map[d]["TriageLevel"])
df["Reason"] = df["Disease"].map(lambda d: disease_triage_map[d]["Reason"])
df["SuggestedAction"] = df["Disease"].map(lambda d: disease_triage_map[d]["SuggestedAction"])
print("✅ Appended triage data to each row.\n")

# Save updated dataset
output_path = "data/known_diseases_with_triage.csv"
df.to_csv(output_path, index=False)
print(f"✅ Saved enriched dataset to: {output_path}")
