"""Train a fraud detection model on synthetic transaction data.

Generates a synthetic dataset with realistic fraud signal, trains a
RandomForest classifier, reports AUC / precision / recall, and serializes the
fitted model to ``fraud_model.joblib`` for the inference service to load.
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42
MODEL_PATH = "fraud_model.joblib"

FEATURES = [
    "amount",
    "merchant_category",
    "hour_of_day",
    "days_since_last_txn",
    "num_txns_24h",
    "is_foreign",
    "account_age_days",
]


def generate_synthetic_data(n: int = 10_000) -> pd.DataFrame:
    """Create synthetic transactions with an embedded fraud pattern."""
    rng = np.random.default_rng(RANDOM_SEED)

    data = pd.DataFrame(
        {
            "amount": rng.exponential(scale=120, size=n),
            "merchant_category": rng.integers(0, 10, size=n),
            "hour_of_day": rng.integers(0, 24, size=n),
            "days_since_last_txn": rng.integers(0, 30, size=n),
            "num_txns_24h": rng.poisson(lam=3, size=n),
            "is_foreign": rng.binomial(1, 0.15, size=n),
            "account_age_days": rng.integers(1, 2000, size=n),
        }
    )

    # Fraud is more likely for large amounts, odd hours, foreign transactions,
    # brand-new accounts, and high transaction velocity.
    fraud_signal = (
        (data["amount"] > 300).astype(int) * 0.9
        + ((data["hour_of_day"] < 5) | (data["hour_of_day"] > 23)).astype(int) * 0.7
        + data["is_foreign"] * 0.8
        + (data["account_age_days"] < 30).astype(int) * 0.9
        + (data["num_txns_24h"] > 6).astype(int) * 0.8
    )
    prob = 1 / (1 + np.exp(-(fraud_signal - 1.6) * 3))
    data["is_fraud"] = rng.binomial(1, prob)
    return data


def main() -> None:
    df = generate_synthetic_data()
    X = df[FEATURES]
    y = df["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=100, max_depth=8, random_state=RANDOM_SEED, n_jobs=-1
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    print(f"Test AUC: {roc_auc_score(y_test, proba):.4f}")
    print(classification_report(y_test, model.predict(X_test)))

    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
