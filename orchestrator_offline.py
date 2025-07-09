# ✅ week8_orchestrator_offline.py
# Complete Orchestrator with Offline Support & Voice Kiosk Mode

import threading
import time
import os
import logging
import socket
import json
from agents.crowd_predictor import run_crowd_forecast
from agents.feedback_analyzer import run_feedback_analysis
from agents.followup_scheduler import run_followup_check
from agents.future_scheduler import run_future_appointments
from agents.token_scheduler import run_token_assignment
from utils.sms_utils import send_sms

logging.basicConfig(level=logging.INFO, filename="logs/agent_log.txt", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

OFFLINE_LOG = "data/offline_events.json"

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except:
        return False

def log_offline_event(agent_name, data):
    event = {"agent": agent_name, "data": data, "timestamp": time.time()}
    if not os.path.exists(OFFLINE_LOG):
        with open(OFFLINE_LOG, "w") as f:
            json.dump([event], f)
    else:
        with open(OFFLINE_LOG, "r+") as f:
            events = json.load(f)
            events.append(event)
            f.seek(0)
            json.dump(events, f)

def sync_offline_data():
    if os.path.exists(OFFLINE_LOG) and is_connected():
        with open(OFFLINE_LOG, "r") as f:
            events = json.load(f)
        for e in events:
            logging.info(f"🔁 Syncing offline agent: {e['agent']} with data: {e['data']}")
            # Simulate syncing with backend or DB
        os.remove(OFFLINE_LOG)

def orchestrator_loop():
    while True:
        online = is_connected()
        try:
            logging.info("📡 Orchestrator cycle started")

            # Agent 1: Crowd Prediction (optional)
            try:
                run_crowd_forecast()
                logging.info("✅ Crowd forecast complete")
            except Exception as e:
                logging.error(f"❌ Crowd forecast error: {e}")

            # Agent 2: Token Assignment
            try:
                data = run_token_assignment()
                if not online:
                    log_offline_event("token_assignment", data)
                logging.info("✅ Token scheduler done")
            except Exception as e:
                logging.error(f"❌ Token scheduler error: {e}")

            # Agent 3: Follow-up Check
            try:
                data = run_followup_check()
                if not online:
                    log_offline_event("followup_check", data)
                logging.info("✅ Follow-up check done")
            except Exception as e:
                logging.error(f"❌ Follow-up error: {e}")

            # Agent 4: Future Appointments
            try:
                run_future_appointments()
                logging.info("✅ Future appointments processed")
            except Exception as e:
                logging.error(f"❌ Future scheduler error: {e}")

            # Agent 5: Feedback Analysis
            try:
                run_feedback_analysis()
                logging.info("✅ Feedback analyzed")
            except Exception as e:
                logging.error(f"❌ Feedback analysis error: {e}")

            # Final: Sync if online
            if online:
                sync_offline_data()

        except Exception as e:
            logging.error(f"❌ Uncaught orchestrator error: {e}")

        time.sleep(300)  # Wait 5 minutes


# 📢 Kiosk Mode (Voice input for Raspberry Pi)
def run_voice_kiosk():
    import speech_recognition as sr
    import pyttsx3
    engine = pyttsx3.init()
    recog = sr.Recognizer()

    def speak(text):
        engine.say(text)
        engine.runAndWait()

    while True:
        with sr.Microphone() as source:
            speak("Welcome to SmartOPD. Please say your name.")
            audio = recog.listen(source)
            try:
                name = recog.recognize_google(audio)
                speak(f"Hi {name}, please describe your symptoms briefly.")
                audio = recog.listen(source)
                symptoms = recog.recognize_google(audio)

                # Write to offline intake file
                patient_data = {"name": name, "symptoms": symptoms, "timestamp": time.time()}
                with open("data/kiosk_intake.json", "a") as f:
                    f.write(json.dumps(patient_data) + "\n")
                speak("Thanks, your data has been collected.")

            except sr.UnknownValueError:
                speak("Sorry, I didn’t catch that. Please try again.")
            except Exception as e:
                speak("Something went wrong.")
                logging.error(f"Voice error: {e}")

# ✳️ Launch orchestrator thread from app.py
if __name__ == "__main__":
    t = threading.Thread(target=orchestrator_loop, daemon=True)
    t.start()
    run_voice_kiosk()  # optional for kiosk boot mode
