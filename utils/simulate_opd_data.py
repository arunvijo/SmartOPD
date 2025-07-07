# utils/simulate_opd_data.py
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_opd_data(start_date, end_date):
    data = []
    current_date = start_date

    while current_date <= end_date:
        is_weekend = current_date.weekday() >= 5
        is_holiday = random.choices([0, 1], weights=[0.9, 0.1])[0]  # 10% chance holiday
        is_rainy = random.choices([0, 1], weights=[0.8, 0.2])[0]     # 20% chance rain
        doctor_count = random.randint(2, 5)

        for hour in range(8, 17):  # OPD hours: 8AM to 5PM
            base = random.randint(10, 30)
            noise = np.random.normal(0, 5)

            # Reduce patients on holidays/weekends/rain
            multiplier = 1
            if is_weekend: multiplier -= 0.4
            if is_holiday: multiplier -= 0.5
            if is_rainy:   multiplier -= 0.2

            total_patients = max(0, int((base + noise) * multiplier))

            data.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "hour": hour,
                "total_patients": total_patients,
                "is_holiday": is_holiday,
                "is_rainy": is_rainy,
                "doctor_count": doctor_count
            })

        current_date += timedelta(days=1)

    df = pd.DataFrame(data)
    df.to_csv("data/opd_footfall.csv", index=False)
    print("Simulated data saved to data/opd_footfall.csv")

if __name__ == "__main__":
    generate_opd_data(start_date=datetime(2024, 5, 1), end_date=datetime(2024, 7, 1))
