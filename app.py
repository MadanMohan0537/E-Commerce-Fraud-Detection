from flask import Flask, request, jsonify, render_template
import numpy as np
import pickle
import os

app = Flask(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "fraud_model.pkl")

model = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)


FEATURE_NAMES = [
    "transaction_amount",
    "account_age_days",
    "num_transactions_today",
    "distance_from_home_km",
    "hour_of_day",
    "is_weekend",
    "is_international",
    "payment_method",   # 0=card, 1=wallet, 2=bank
    "device_type",      # 0=mobile, 1=desktop, 2=tablet
    "failed_attempts",
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze")
def analyze():
    return render_template("analyze.html")


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    features = np.array([[
        float(data.get("transaction_amount", 0)),
        float(data.get("account_age_days", 365)),
        float(data.get("num_transactions_today", 1)),
        float(data.get("distance_from_home_km", 0)),
        float(data.get("hour_of_day", 12)),
        int(data.get("is_weekend", 0)),
        int(data.get("is_international", 0)),
        int(data.get("payment_method", 0)),
        int(data.get("device_type", 0)),
        int(data.get("failed_attempts", 0)),
    ]])

    if model is None:
        # Demo mode: rule-based heuristic when model not trained yet
        score = _heuristic_score(features[0])
        is_fraud = score > 0.5
        return jsonify({
            "fraud": bool(is_fraud),
            "probability": round(float(score), 3),
            "confidence": _confidence_label(score),
            "risk_factors": _risk_factors(features[0]),
            "mode": "demo"
        })

    prob = model.predict_proba(features)[0][1]
    return jsonify({
        "fraud": bool(prob > 0.5),
        "probability": round(float(prob), 3),
        "confidence": _confidence_label(prob),
        "risk_factors": _risk_factors(features[0]),
        "mode": "model"
    })


def _heuristic_score(f):
    score = 0.0
    amount, age, txn_today, dist, hour, weekend, intl, pay, device, failed = f
    if amount > 5000: score += 0.35
    elif amount > 1000: score += 0.15
    if age < 30: score += 0.2
    if txn_today > 5: score += 0.15
    if dist > 500: score += 0.2
    if hour < 5 or hour > 22: score += 0.15
    if intl: score += 0.1
    if failed > 1: score += 0.2
    return min(score, 0.99)


def _confidence_label(prob):
    if prob > 0.85: return "Very High Risk"
    if prob > 0.65: return "High Risk"
    if prob > 0.45: return "Medium Risk"
    if prob > 0.25: return "Low Risk"
    return "Very Low Risk"


def _risk_factors(f):
    amount, age, txn_today, dist, hour, weekend, intl, pay, device, failed = f
    factors = []
    if amount > 5000: factors.append({"factor": "High transaction amount", "severity": "high"})
    elif amount > 1000: factors.append({"factor": "Elevated transaction amount", "severity": "medium"})
    if age < 30: factors.append({"factor": "New account (< 30 days)", "severity": "high"})
    if txn_today > 5: factors.append({"factor": "Multiple transactions today", "severity": "medium"})
    if dist > 500: factors.append({"factor": "Transaction far from home", "severity": "high"})
    if hour < 5 or hour > 22: factors.append({"factor": "Unusual transaction time", "severity": "medium"})
    if intl: factors.append({"factor": "International transaction", "severity": "low"})
    if failed > 1: factors.append({"factor": "Previous failed attempts", "severity": "high"})
    if not factors: factors.append({"factor": "No significant risk factors detected", "severity": "none"})
    return factors


if __name__ == "__main__":
    app.run(debug=True)
