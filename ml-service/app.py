"""FastAPI service exposing fraud probability inference.

Loads the serialized RandomForest model at startup and scores transaction
feature payloads sent by the Spring Boot service.
"""

import os
from contextlib import asynccontextmanager

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

MODEL_PATH = os.getenv("MODEL_PATH", "fraud_model.joblib")

FEATURES = [
    "amount",
    "merchant_category",
    "hour_of_day",
    "days_since_last_txn",
    "num_txns_24h",
    "is_foreign",
    "account_age_days",
]

# Holds the loaded model; populated on startup.
_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _state["model"] = joblib.load(MODEL_PATH)
    yield
    _state.clear()


app = FastAPI(title="FraudShield ML Inference Service", lifespan=lifespan)


class TransactionFeatures(BaseModel):
    amount: float
    merchant_category: int
    hour_of_day: int
    days_since_last_txn: int
    num_txns_24h: int
    is_foreign: int
    account_age_days: int


class PredictionResponse(BaseModel):
    fraud_probability: float


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": "model" in _state}


@app.post("/predict", response_model=PredictionResponse)
def predict(features: TransactionFeatures):
    row = pd.DataFrame([{name: getattr(features, name) for name in FEATURES}])
    probability = float(_state["model"].predict_proba(row)[0, 1])
    return PredictionResponse(fraud_probability=probability)
