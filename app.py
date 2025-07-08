# app/app.py

from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

QUEUE_FILE = "data/token_queue.csv"

@app.route("/")
def index():
    if os.path.exists(QUEUE_FILE):
        df = pd.read_csv(QUEUE_FILE)
    else:
        df = pd.DataFrame(columns=["token", "name", "symptoms", "triage_level", "timestamp", "reason"])

    return render_template("index.html", queue=df.to_dict(orient="records"))

@app.route("/search", methods=["POST"])
def search():
    name = request.form.get("name")
    df = pd.read_csv(QUEUE_FILE)
    result = df[df["name"].str.lower() == name.lower()]
    return render_template("search.html", results=result.to_dict(orient="records"), name=name)

if __name__ == "__main__":
    app.run(debug=True)
