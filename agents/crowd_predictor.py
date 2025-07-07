# agents/crowd_predictor.py

import pandas as pd
import pickle
from prophet import Prophet
from datetime import datetime, timedelta

def load_model():
    with open("agents/prophet_model.pkl", "rb") as f:
        return pickle.load(f)

def predict_next_day():
    model = load_model()
    last_date = model.history['ds'].max()
    future = model.make_future_dataframe(periods=24, freq='h')
    forecast = model.predict(future)

    next_day = forecast.tail(24)[['ds', 'yhat']]
    next_day.columns = ['datetime', 'predicted_patients']
    return next_day

if __name__ == "__main__":
    df = predict_next_day()
    print(df)
