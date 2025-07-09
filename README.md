# 🏥 SmartOPD – AI-Driven Patient Queue & Triage System

![SmartOPD](https://img.shields.io/badge/AI--powered-Triage-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![Build](https://img.shields.io/badge/render-live-brightgreen)

SmartOPD is an intelligent, open-source OPD management system built to improve patient flow, reduce crowding, and enhance healthcare access in Primary Health Centers and Government Hospitals.

✨ **Built with FastAPI · Bootstrap · ML Agents · SQLite**

---

## 🚀 Live Demo

👉 [Try SmartOPD Online](https://smartopd-backend.onrender.com) (Auto-deployed on Render)  
📱 Optimized for mobile use  
🔐 No login required for patients  

---

## 🧠 Features

✅ **AI-Based Symptom Triage** (Normal, Priority, Emergency)  
✅ **Live Token Queue Dashboard**  
✅ **Crowd Prediction using Time-Series ML (Prophet)**  
✅ **Feedback Sentiment Analysis**  
✅ **Follow-up Scheduling & Rebooking Agents**  
✅ **Voice Feedback + Offline Support Ready**  
✅ **Responsive Web UI for Patients & Staff**

---

## 🖼 Screenshots

| Dashboard | Chatbot Assistant |
|----------|------------------|
| ![dashboard](public/screenshots/dashboard.png) | ![chatbot](public/screenshots/chatbot.png) |

---

## 🔧 Tech Stack

- 🐍 **Backend**: FastAPI, Pandas, Prophet, Scikit-learn  
- 🧠 **AI Agents**: Custom ML + NLP agents for triage, feedback, and scheduling  
- 🎨 **Frontend**: HTML, Bootstrap 5 (mobile-first UI)  
- 🗃 **Database**: CSV (for demo), can scale to SQLite/PostgreSQL  
- 🛠 **Deployment**: Render (free tier), supports auto-deploy from GitHub

---

## 📁 Project Structure

SmartOPD/
│
├── main.py # Unified FastAPI backend
├── agents/ # AI agents for triage, follow-up, etc.
├── templates/ # HTML templates (Jinja2)
├── static/ # Bootstrap/CSS/JS assets
├── data/ # Patient records, feedbacks, etc.
├── requirements.txt # Python dependencies
├── README.md
└── CONTRIBUTING.md

yaml
Copy
Edit

---

## 🛠 Local Development

```bash
# Clone the repo
git clone https://github.com/arunvijo/SmartOPD.git
cd SmartOPD

# Create virtual environment and activate
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn main:app --reload
Visit: http://localhost:8000

🤝 Contribute
We welcome contributions of all kinds!
Want to add new languages, a QR-based check-in system, or a React UI?

👉 Check CONTRIBUTING.md for details.
🪪 Star ⭐ this repo if you support the mission of smarter healthcare access for all.

📃 License
This project is licensed under the MIT License.

Built with ❤️ for real-world impact in rural and government hospitals.