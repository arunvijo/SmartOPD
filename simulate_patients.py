import requests
import random
import time

names = ["Arun", "Meera", "Fathima", "Rakesh", "Neha"]
symptoms_list = [
    "Chest pain and shortness of breath",
    "Mild headache",
    "High fever",
    "Sudden dizziness",
    "Slurred speech",
    "Back pain",
    "Severe bleeding"
]

for i in range(100):
    name = random.choice(names) + str(i)
    symptoms = random.choice(symptoms_list)
    payload = {"name": name, "symptoms": symptoms}
    requests.post("http://localhost:8000/triage", json=payload)
    time.sleep(0.2)