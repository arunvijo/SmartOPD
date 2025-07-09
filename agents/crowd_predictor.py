# agents/crowd_predictor.py

import pandas as pd
import pickle
import json
from prophet import Prophet
from datetime import datetime

def load_model():
    with open("agents/prophet_model.pkl", "rb") as f:
        return pickle.load(f)

def predict_next_day():
    model = load_model()
    future = model.make_future_dataframe(periods=24, freq='h')
    forecast = model.predict(future)

    next_day = forecast.tail(24)[['ds', 'yhat']]
    next_day.columns = ['datetime', 'predicted_patients']
    next_day['datetime'] = next_day['datetime'].astype(str)  # For JSON serialization
    next_day['predicted_patients'] = next_day['predicted_patients'].astype(int)

    return next_day

def save_predictions_to_file():
    df = predict_next_day()
    output_path = "data/crowd_density.json"
    df.to_json(output_path, orient="records", indent=2)
    print(f"✅ Crowd forecast saved to {output_path}")

# ✅ Add this so orchestrator can call it
def run_crowd_forecast():
    save_predictions_to_file()

if __name__ == "__main__":
    save_predictions_to_file()
