from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
import threading
import time
from datetime import datetime, timedelta
import requests
from agents import crowd_predictor, symptom_triage, token_scheduler, followup_scheduler, future_scheduler, feedback_analyzer, personalization
from utils.speech_utils import speak_token

app = FastAPI()

# Mount static files and templates
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Enable CORS (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure data directory and files exist
os.makedirs("data", exist_ok=True)
QUEUE_FILE = "data/token_queue.csv"
FOLLOWUP_FILE = "data/followups.csv"
FUTURE_FILE = "data/future_tokens.csv"
PATIENTS_CSV = "data/patients.csv"
FEEDBACK_FILE = "data/feedback.csv"


from fastapi.responses import RedirectResponse

@app.get("/chatbot")
async def redirect_chatbot():
    return RedirectResponse(url="/chatbot-ui")


if not os.path.exists(PATIENTS_CSV):
    pd.DataFrame(columns=[
        "token", "name", "age", "gender", "blood_pressure",
        "cholesterol_level", "symptoms", "disease", "triage", "timestamp"
    ]).to_csv(PATIENTS_CSV, index=False)

# ---------------------- AGENT BACKGROUND JOBS ------------------------

@app.on_event("startup")
def launch_background_agents():
    def update_crowd_predictions():
        while True:
            print("[Crowd Predictor] Updating predictions...")
            crowd_predictor.save_predictions_to_file()
            time.sleep(300)

    def run_followup_scheduler():
        while True:
            try:
                followup_scheduler.save_followups()
            except Exception as e:
                print("[Follow-up Error]", e)
            time.sleep(3600)

    threading.Thread(target=update_crowd_predictions, daemon=True).start()
    threading.Thread(target=run_followup_scheduler, daemon=True).start()


# ---------------------- HOMEPAGE ------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    queue = pd.read_csv(QUEUE_FILE) if os.path.exists(QUEUE_FILE) else pd.DataFrame()
    followups = pd.read_csv(FOLLOWUP_FILE) if os.path.exists(FOLLOWUP_FILE) else pd.DataFrame()
    future_tokens = pd.read_csv(FUTURE_FILE) if os.path.exists(FUTURE_FILE) else pd.DataFrame()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "queue": queue.to_dict(orient="records"),
        "followups": followups.to_dict(orient="records"),
        "future_bookings": future_tokens.to_dict(orient="records")
    })



@app.get("/chatbot-ui", response_class=HTMLResponse)
async def get_chatbot(request: Request):
    request.session.clear()
    request.session["conversation"] = [
        {"sender": "bot", "text": "🤖 Hi! I’m SmartOPD Assistant. What is your name?"}
    ]
    request.session["data"] = {}
    request.session["symptom_stage"] = "init"
    return templates.TemplateResponse("chatbot.html", {"request": request, "conversation": request.session["conversation"]})


@app.post("/chatbot-ui", response_class=HTMLResponse)
async def post_chatbot(request: Request, message: str = Form(...)):
    session = request.session

    if "conversation" not in session:
        session["conversation"] = []
        session["data"] = {}
        session["symptom_stage"] = "init"

    if message.strip() == "__clear__":
        return RedirectResponse("/chatbot-ui", status_code=302)

    session["conversation"].append({"sender": "user", "text": message})
    data = session.get("data", {})
    stage = session.get("symptom_stage", "init")
    bot_reply = ""

    if "name" not in data:
        data["name"] = message
        bot_reply = f"Hi {data['name']}, what is your age?"

    elif "age" not in data:
        if message.isdigit():
            data["age"] = int(message)
            bot_reply = "What is your gender? (male/female)"
        else:
            bot_reply = "Please enter a valid age."

    elif "gender" not in data:
        gender = message.lower()
        if gender in ["male", "female"]:
            data["gender"] = 1 if gender == "male" else 0
            bot_reply = "What is your blood pressure? (low/normal/high)"
        else:
            bot_reply = "Please say gender as 'male' or 'female'."

    elif "blood_pressure" not in data:
        bp_map = {"low": 0, "normal": 1, "high": 2}
        if message.lower() in bp_map:
            data["blood_pressure"] = bp_map[message.lower()]
            bot_reply = "What is your cholesterol level? (low/normal/high)"
        else:
            bot_reply = "Say blood pressure as low, normal, or high."

    elif "cholesterol_level" not in data:
        chol_map = {"low": 0, "normal": 1, "high": 2}
        if message.lower() in chol_map:
            data["cholesterol_level"] = chol_map[message.lower()]
            data["symptom_flags"] = {}
            session["symptom_stage"] = "fever"
            bot_reply = "Do you have fever? (yes/no)"
        else:
            bot_reply = "Say cholesterol level as low, normal, or high."

    elif stage in ["fever", "cough", "fatigue", "breathing"]:
        yes = message.lower().startswith("y")
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
        data["disease"] = message
        session["symptom_stage"] = "symptoms"
        bot_reply = "Finally, describe your symptoms briefly (e.g., chest pain, headache)."

    elif stage == "symptoms":
        data["symptoms"] = message
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
                tag_str = ", ".join(result.get("tags", [])) if result.get("tags") else "No tags"
                bot_reply = f"✅ Token {token} assigned. Triage: {triage}. {msg}<br>🧠 Profile Tags: {tag_str}" if token else f"⚠️ {msg}"
            else:
                bot_reply = f"❌ Server error: {response.status_code}"
        except Exception as e:
            bot_reply = f"Error contacting backend: {str(e)}"

    session["data"] = data
    session["conversation"].append({"sender": "bot", "text": bot_reply})
    return templates.TemplateResponse("chatbot.html", {"request": request, "conversation": session["conversation"]})

# ---------------------- REGISTER ------------------------

@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "message": None})

@app.post("/register", response_class=HTMLResponse)
def register_post(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    gender: int = Form(...),
    bp: int = Form(...),
    chol: int = Form(...),
    symptoms: str = Form(...),
    disease: str = Form("")
):
    try:
        record = {
            "name": name,
            "age": age,
            "gender": gender,
            "blood_pressure": bp,
            "cholesterol_level": chol,
            "symptoms": symptoms,
            "disease": disease,
            "timestamp": pd.Timestamp.now(),
        }
        df = pd.DataFrame([record])
        df.to_csv(PATIENTS_CSV, mode="a", header=not os.path.exists(PATIENTS_CSV), index=False)
        msg = "✅ Registered successfully."
    except Exception as e:
        msg = f"❌ Error: {str(e)}"
    return templates.TemplateResponse("register.html", {"request": request, "message": msg})

# ---------------------- GET TOKEN ------------------------

@app.get("/get-token", response_class=HTMLResponse)
def get_token_view(request: Request):
    df = pd.read_csv(QUEUE_FILE) if os.path.exists(QUEUE_FILE) else pd.DataFrame()
    latest = df.iloc[-1].to_dict() if not df.empty else None
    return templates.TemplateResponse("token.html", {"request": request, "token": latest})

# ---------------------- PREDICT CROWD ------------------------

@app.get("/predict-crowd")
def get_crowd_predictions():
    path = "data/crowd_density.json"
    if not os.path.exists(path):
        crowd_predictor.save_predictions_to_file()
    return requests.get("http://localhost:8000/static/crowd_density.json").json()

# ---------------------- DASHBOARD ------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(request: Request):
    df = pd.read_csv(PATIENTS_CSV) if os.path.exists(PATIENTS_CSV) else pd.DataFrame()
    stats = {
        "total": len(df),
        "emergencies": len(df[df["triage"] == "Emergency"]) if not df.empty else 0
    }
    return templates.TemplateResponse("dashboard.html", {"request": request, "patients": df.to_dict(orient="records"), "stats": stats})

# ---------------------- EMERGENCY ALERT ------------------------

class Alert(BaseModel):
    message: str
    timestamp: str = datetime.now().isoformat()

@app.post("/emergency-alert")
def emergency_alert(data: Alert):
    print(f"[ALERT] 🚨 {data.timestamp}: {data.message}")
    return {"status": "received", "message": data.message}

# ---------------------- FEEDBACK ------------------------

@app.get("/feedback", response_class=HTMLResponse)
def feedback_get(request: Request):
    return templates.TemplateResponse("feedback.html", {"request": request, "message": None})

@app.post("/feedback", response_class=HTMLResponse)
def feedback_post(request: Request, name: str = Form(...), token: int = Form(...), triage: str = Form(...), feedback: str = Form(...)):
    try:
        sentiment = feedback_analyzer.save_feedback(name, token, triage, feedback)
        msg = f"✅ Thank you! Sentiment: {sentiment}"
    except Exception as e:
        msg = f"❌ Error: {str(e)}"
    return templates.TemplateResponse("feedback.html", {"request": request, "message": msg})

# ---------------------- ADMIN DASHBOARD ------------------------

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    patients = pd.read_csv(PATIENTS_CSV) if os.path.exists(PATIENTS_CSV) else pd.DataFrame()
    feedbacks = pd.read_csv(FEEDBACK_FILE) if os.path.exists(FEEDBACK_FILE) else pd.DataFrame()
    followups = pd.read_csv(FOLLOWUP_FILE) if os.path.exists(FOLLOWUP_FILE) else pd.DataFrame()

    stats = {"total_patients": len(patients), "emergency_pct": 0, "avg_wait": 0, "missed_followups": 0}

    if not patients.empty:
        emergencies = patients[patients.triage == "Emergency"]
        stats["emergency_pct"] = round(100 * len(emergencies) / len(patients), 1)
        patients["timestamp"] = pd.to_datetime(patients["timestamp"], errors="coerce")
        wait_times = (pd.Timestamp.now() - patients["timestamp"]).dt.total_seconds() / 60
        stats["avg_wait"] = round(wait_times.mean(), 1)

    if not followups.empty:
        followups["date"] = pd.to_datetime(followups["date"], errors="coerce")
        stats["missed_followups"] = len(followups[followups["date"] < pd.Timestamp.now()])

    heatmap = patients["symptoms"].value_counts().head(10).to_dict() if not patients.empty else {}

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "stats": stats,
        "heatmap": heatmap,
        "feedbacks": feedbacks.to_dict(orient="records")
    })

# ---------------------- EXPORT DATA ------------------------

@app.get("/export")
def export_data():
    if os.path.exists(PATIENTS_CSV):
        df = pd.read_csv(PATIENTS_CSV)
        export_path = "data/patient_report.xlsx"
        df.to_excel(export_path, index=False)
        return {"status": "✅ Exported", "path": export_path}
    return {"status": "⚠️ No patient data found."}

# ---------------------- TRIAGE API ------------------------

class PatientRequest(BaseModel):
    name: str
    age: int
    gender: int
    blood_pressure: int
    cholesterol_level: int
    symptoms: str
    disease: str = None

@app.post("/triage")
def triage(data: PatientRequest):
    crowd_file_path = "data/crowd_density.json"
    if not os.path.exists(crowd_file_path):
        crowd_predictor.save_predictions_to_file()

    history_path = PATIENTS_CSV
    past_visits = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()
    past_user = past_visits[past_visits["name"] == data.name]

    features = symptom_triage.extract_features_from_text(data.symptoms)
    features.update({
        "Age": data.age,
        "Gender": data.gender,
        "Blood Pressure": data.blood_pressure,
        "Cholesterol Level": data.cholesterol_level,
    })

    if not past_user.empty:
        recent = pd.to_datetime(past_user["timestamp"]).max()
        days_since_last = (pd.Timestamp.now() - recent).days
        emergencies = past_user[past_user["triage"] == "Emergency"]
        if days_since_last < 7 or len(emergencies) >= 2:
            features["FrequentVisits"] = 1

    result = symptom_triage.triage_decision(features, disease_name=data.disease)

    if not result["assign_token"]:
        future_scheduler.save_future_booking({
            "name": data.name,
            "symptoms": data.symptoms,
            "triage": result["triage"],
            "reason": result["message"]
        })
        return {
            "token": None,
            "triage": result["triage"],
            "reason": result["message"],
            "suggested_action": "You’ve been automatically rebooked for tomorrow due to high crowd. Please visit again."
        }

    token, queue = token_scheduler.assign_token(data.name, data.symptoms, result["triage"], result["message"])
    threading.Thread(target=speak_token, args=(int(token), data.name)).start()

    record = {
        "name": data.name,
        "age": data.age,
        "gender": data.gender,
        "blood_pressure": data.blood_pressure,
        "cholesterol_level": data.cholesterol_level,
        "symptoms": data.symptoms,
        "disease": data.disease or "",
        "triage": result["triage"],
        "token": int(token),
        "timestamp": pd.Timestamp.now(),
        "feedback": ""
    }

    df_record = pd.DataFrame([record])
    df_record.to_csv(history_path, mode='a', header=not os.path.exists(history_path), index=False)

    personalization.update_profile(data.name, data.age, data.gender, data.disease, result["triage"])

    return {
        "token": int(token),
        "triage": result["triage"],
        "reason": result["message"],
        "suggested_action": "Proceed to OPD. Token generated."
    }

# ---------------------- OTHER AGENTS ------------------------

@app.get("/followups")
def get_followups():
    if os.path.exists(FOLLOWUP_FILE):
        df = pd.read_csv(FOLLOWUP_FILE)
        return df.to_dict(orient="records")
    return []

@app.post("/rebook")
def rebook_case(data: dict):
    future_scheduler.save_future_booking(data)
    return {"status": "scheduled", "scheduled_for": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}

@app.post("/reschedule")
def reschedule(data: dict):
    name = data.get("name")
    new_date = data.get("new_date")
    future_scheduler.reschedule_booking(name, new_date)
    return {"status": "rescheduled", "new_date": new_date}

# ---------------------- Run ------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)