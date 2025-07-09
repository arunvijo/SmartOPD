from flask import Flask, render_template, request, session
import pandas as pd
import os
import requests

app = Flask(__name__)
app.secret_key = "smartopd-secret-key"

QUEUE_FILE = "data/token_queue.csv"
FOLLOWUP_FILE = "data/followups.csv"
FUTURE_FILE = "data/future_tokens.csv"


@app.route("/")
def index():
    # Load token queue
    queue = pd.read_csv(QUEUE_FILE) if os.path.exists(QUEUE_FILE) else pd.DataFrame(columns=["token", "name", "symptoms", "triage_level", "timestamp", "reason"])

    # Load follow-up patients
    followups = pd.read_csv(FOLLOWUP_FILE) if os.path.exists(FOLLOWUP_FILE) else pd.DataFrame(columns=["name", "last_triage", "last_visit", "days_since", "status"])
    future_tokens = pd.read_csv(FUTURE_FILE) if os.path.exists(FUTURE_FILE) else pd.DataFrame()

    return render_template("index.html",
                        queue=queue.to_dict(orient="records"),
                        followups=followups.to_dict(orient="records"),
                        future_bookings=future_tokens.to_dict(orient="records"))


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    msg = None
    if request.method == "POST":
        name = request.form["name"]
        token = int(request.form["token"])
        triage = request.form["triage"]
        feedback_text = request.form["feedback"]

        # Send to FastAPI endpoint
        try:
            res = requests.post("http://localhost:8000/feedback", json={
                "name": name,
                "token": token,
                "triage": triage,
                "feedback": feedback_text
            })
            if res.status_code == 200:
                msg = f"Thank you! Sentiment: {res.json()['sentiment']}"
            else:
                msg = f"Server Error: {res.status_code}"
        except Exception as e:
            msg = f"Error: {e}"

    return render_template("feedback.html", message=msg)


@app.route("/admin")
def admin():
    feedback_file = "data/feedback.csv"
    if os.path.exists(feedback_file):
        df = pd.read_csv(feedback_file)
        summary = df.groupby("sentiment").size().reset_index(name="count").to_dict(orient="records")
    else:
        summary = []

    return render_template("admin.html", summary=summary)



@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if "conversation" not in session:
        session["conversation"] = []
        session["data"] = {}
        session["symptom_stage"] = "init"
        session["conversation"].append({"sender": "bot", "text": "🤖 Hi! I’m SmartOPD Assistant. What is your name?"})

    bot_reply = None

    if request.method == "POST":
        user_input = request.form["message"].strip()

        if user_input == "__clear__":
            session.clear()
            return render_template("chatbot.html", conversation=[{"sender": "bot", "text": "🤖 Hi! I’m SmartOPD Assistant. What is your name?"}])

        session["conversation"].append({"sender": "user", "text": user_input})
        data = session.get("data", {})
        stage = session.get("symptom_stage", "init")

        if "name" not in data:
            data["name"] = user_input
            bot_reply = f"Hi {data['name']}, what is your age?"

        elif "age" not in data:
            if user_input.isdigit():
                data["age"] = int(user_input)
                bot_reply = "What is your gender? (male/female)"
            else:
                bot_reply = "Please enter a valid age."

        elif "gender" not in data:
            gender = user_input.lower()
            if gender in ["male", "female"]:
                data["gender"] = 1 if gender == "male" else 0
                bot_reply = "What is your blood pressure? (low/normal/high)"
            else:
                bot_reply = "Please say gender as 'male' or 'female'."

        elif "blood_pressure" not in data:
            bp_map = {"low": 0, "normal": 1, "high": 2}
            if user_input.lower() in bp_map:
                data["blood_pressure"] = bp_map[user_input.lower()]
                bot_reply = "What is your cholesterol level? (low/normal/high)"
            else:
                bot_reply = "Say blood pressure as low, normal, or high."

        elif "cholesterol_level" not in data:
            chol_map = {"low": 0, "normal": 1, "high": 2}
            if user_input.lower() in chol_map:
                data["cholesterol_level"] = chol_map[user_input.lower()]
                data["symptom_flags"] = {}
                session["symptom_stage"] = "fever"
                bot_reply = "Do you have fever? (yes/no)"
            else:
                bot_reply = "Say cholesterol level as low, normal, or high."

        elif stage in ["fever", "cough", "fatigue", "breathing"]:
            yes = user_input.lower().startswith("y")
            symptom_map = {
                "fever": "Fever",
                "cough": "Cough",
                "fatigue": "Fatigue",
                "breathing": "Difficulty Breathing"
            }
            data["symptom_flags"][symptom_map[stage]] = int(yes)
            next_stage = {"fever": "cough", "cough": "fatigue", "fatigue": "breathing", "breathing": "disease"}
            session["symptom_stage"] = next_stage[stage]
            bot_reply = "Do you have any known diseases? If none, say 'none'." if session["symptom_stage"] == "disease" else f"Do you have {session['symptom_stage']}? (yes/no)"

        elif stage == "disease":
            data["disease"] = user_input
            session["symptom_stage"] = "symptoms"
            bot_reply = "Finally, describe your symptoms briefly (e.g., chest pain, headache)."

        elif stage == "symptoms":
            data["symptoms"] = user_input
            features = data.get("symptom_flags", {})
            payload = {
                "name": data["name"],
                "age": data["age"],
                "gender": data["gender"],
                "blood_pressure": data["blood_pressure"],
                "cholesterol_level": data["cholesterol_level"],
                "symptoms": data["symptoms"],
                "disease": data["disease"]
            }
            try:
                response = requests.post("http://localhost:8000/triage", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    token = result.get("token")
                    triage = result.get("triage")
                    msg = result.get("suggested_action")
                    bot_reply = f"✅ Token {token} assigned. Triage: {triage}. {msg}" if token else f"⚠️ {msg}"
                else:
                    bot_reply = f"❌ Server error: {response.status_code}"
            except Exception as e:
                bot_reply = f"Error contacting backend: {str(e)}"
        else:
            bot_reply = "You're already registered. Click 'Clear' to restart."

        session["data"] = data
        session["conversation"].append({"sender": "bot", "text": bot_reply})

    return render_template("chatbot.html", conversation=session["conversation"])
