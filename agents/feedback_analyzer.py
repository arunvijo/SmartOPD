# agents/feedback_analyzer.py

import pandas as pd
from datetime import datetime

FEEDBACK_FILE = "data/feedback.csv"

positive_keywords = ["good", "great", "excellent", "quick", "helpful", "satisfied"]
negative_keywords = ["bad", "worst", "delay", "slow", "rude", "unhelpful", "angry"]

def classify_sentiment(feedback):
    feedback = feedback.lower()
    if any(word in feedback for word in positive_keywords):
        return "Positive"
    elif any(word in feedback for word in negative_keywords):
        return "Negative"
    return "Neutral"

def save_feedback(name, token, triage, feedback_text):
    sentiment = classify_sentiment(feedback_text)
    record = {
        "name": name,
        "token": token,
        "triage_level": triage,
        "feedback": feedback_text,
        "sentiment": sentiment,
        "timestamp": datetime.now()
    }

    df = pd.DataFrame([record])
    if not pd.read_csv(FEEDBACK_FILE).empty:
        df.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(FEEDBACK_FILE, mode='w', header=True, index=False)

    return sentiment

# ✅ Wrapper for orchestrator
def run_feedback_analysis():
    save_feedback()
