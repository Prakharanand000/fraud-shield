"""No-Docker quickstart for FraudShield.

Runs the entire demo in a single Python process so you can use the web UI
without Docker, Java, or Kubernetes. It serves the same browser frontend that
the Spring Boot service ships, and replicates the Java decision layer
(BLOCK / REVIEW / APPROVE) on top of the scikit-learn model.

Usage:
    pip install -r ml-service/requirements.txt
    python quickstart.py
    # then open http://localhost:8080

The full polyglot architecture (Java API tier -> Python ML service, on Docker /
Kubernetes) still lives in java-service/, ml-service/, and k8s/. This script is
only a convenience runner for local demos.
"""

import os
import subprocess
import sys
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

ROOT = Path(__file__).parent
ML_DIR = ROOT / "ml-service"
MODEL_PATH = ML_DIR / "fraud_model.joblib"
STATIC_DIR = ROOT / "java-service" / "src" / "main" / "resources" / "static"

FEATURES = [
    "amount",
    "merchant_category",
    "hour_of_day",
    "days_since_last_txn",
    "num_txns_24h",
    "is_foreign",
    "account_age_days",
]

# Decision thresholds — identical to the Java service's application.yml.
BLOCK_THRESHOLD = float(os.getenv("RISK_THRESHOLD_BLOCK", "0.80"))
REVIEW_THRESHOLD = float(os.getenv("RISK_THRESHOLD_REVIEW", "0.50"))


def ensure_model():
    """Train the model on first run if the serialized artifact is missing."""
    if MODEL_PATH.exists():
        return
    print("No trained model found — training one now (a few seconds)...")
    subprocess.run([sys.executable, "train_model.py"], cwd=ML_DIR, check=True)


ensure_model()
_model = joblib.load(MODEL_PATH)

app = FastAPI(title="FraudShield (quickstart)")


class Transaction(BaseModel):
    transactionId: str
    amount: float
    merchantCategory: int
    hourOfDay: int
    daysSinceLastTxn: int
    numTxns24h: int
    isForeign: bool
    accountAgeDays: int


class RiskAssessment(BaseModel):
    transactionId: str
    fraudProbability: float
    decision: str
    reason: str


def decide(probability: float) -> tuple[str, str]:
    if probability >= BLOCK_THRESHOLD:
        return "BLOCK", "Fraud probability exceeds block threshold"
    if probability >= REVIEW_THRESHOLD:
        return "REVIEW", "Fraud probability flagged for manual review"
    return "APPROVE", "Fraud probability within acceptable range"


@app.post("/api/v1/assess", response_model=RiskAssessment)
def assess(txn: Transaction):
    row = pd.DataFrame([{
        "amount": txn.amount,
        "merchant_category": txn.merchantCategory,
        "hour_of_day": txn.hourOfDay,
        "days_since_last_txn": txn.daysSinceLastTxn,
        "num_txns_24h": txn.numTxns24h,
        "is_foreign": 1 if txn.isForeign else 0,
        "account_age_days": txn.accountAgeDays,
    }])[FEATURES]
    probability = float(_model.predict_proba(row)[0, 1])
    decision, reason = decide(probability)
    return RiskAssessment(
        transactionId=txn.transactionId,
        fraudProbability=probability,
        decision=decision,
        reason=reason,
    )


@app.get("/api/v1/health")
def health():
    return {"status": "FraudShield quickstart is running"}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


# Serve the rest of the static assets (kept after the routes above so "/" maps
# to index.html explicitly).
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    print("\n  FraudShield quickstart -> http://localhost:8080\n")
    uvicorn.run(app, host="0.0.0.0", port=8080)
