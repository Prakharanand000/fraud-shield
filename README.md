# FraudShield

Live Demo: https://fraud-shield-22cy.onrender.com/
A polyglot, real-time fraud risk scoring system. A **Spring Boot (Java)** REST
API owns the request handling and decision policy; a **Python (FastAPI)** service
owns the ML inference. Both run as independent containers and are orchestrated
together on **Kubernetes**.

This mirrors a common production pattern: the business/API tier is written in a
strongly-typed JVM language for reliability and throughput, while the model is
served from Python where the ML ecosystem lives. The two communicate over HTTP.

A small **web UI** (served at `/`) lets you score transactions from the browser
— enter the transaction details, hit *Assess risk*, and see the
BLOCK / REVIEW / APPROVE decision with the model's fraud probability.

## Two ways to run it

| Mode | What it runs | When to use |
|------|--------------|-------------|
| **Quickstart** (no Docker) | One Python process serving the web UI + model + decision layer | Fastest way to click around the demo locally |
| **Full stack** (Docker / k8s) | The real Spring Boot API tier + Python ML service as separate containers | The production-shaped architecture; the resume story |

### Quickstart (no Docker, ~1 minute)

Requires Python 3.11+ only:

```bash
pip install -r quickstart-requirements.txt
python quickstart.py
# open http://localhost:8080
```

This trains the model on first run (a few seconds), then serves the web UI and a
`/api/v1/assess` endpoint that mirrors the Java decision logic. It's a
convenience runner — the real polyglot architecture lives in `java-service/`,
`ml-service/`, and `k8s/`.

## Architecture

```
                  ┌──────────────────────────────┐
   POST           │   java-service (Spring Boot)  │
   /api/v1/assess │                               │
  ───────────────▶│  FraudController              │
                  │      │                        │
                  │      ▼                        │
                  │  RiskScoringService           │
                  │   (BLOCK / REVIEW / APPROVE)  │
                  │      │                        │
                  │      ▼                        │
                  │  MlInferenceClient ───────────┼──── HTTP POST /predict
                  └──────────────────────────────┘            │
                                                               ▼
                  ┌──────────────────────────────┐
                  │   ml-service (FastAPI)        │
                  │   RandomForest fraud model    │
                  │   returns fraud_probability   │
                  └──────────────────────────────┘

        Both services containerized (Docker) and deployed on Kubernetes
        with liveness/readiness probes, resource limits, and 2 replicas each.
```

The Java tier scores each transaction by calling the ML service, then applies
externalized risk thresholds to return a decision. If the ML call fails, the
service **fails closed** (routes to REVIEW) rather than silently approving.

## Tech stack

| Layer            | Technology                                            |
|------------------|-------------------------------------------------------|
| API / business   | Java 17, Spring Boot 3.2, Spring Web, Bean Validation |
| HTTP client      | Spring `RestClient`                                   |
| ML inference     | Python 3.11, FastAPI, scikit-learn (RandomForest)     |
| Packaging        | Docker (multi-stage Java build)                       |
| Orchestration    | Kubernetes (Deployments, Services, probes)            |
| Observability    | Spring Boot Actuator (liveness/readiness/metrics)     |

## Running locally with Docker Compose

```bash
docker compose up --build
```

This builds both images (the ML image trains the model at build time), starts
them, and wires `java-service` to `ml-service`. The Java API waits for the ML
service health check before starting. Once it's up, open **http://localhost:8080**
for the web UI, or call the API directly:

Score a transaction:

```bash
curl -X POST http://localhost:8080/api/v1/assess \
  -H "Content-Type: application/json" \
  -d '{
    "transactionId": "txn-001",
    "amount": 850.0,
    "merchantCategory": 4,
    "hourOfDay": 3,
    "daysSinceLastTxn": 1,
    "numTxns24h": 9,
    "isForeign": true,
    "accountAgeDays": 12
  }'
```

Example response:

```json
{
  "transactionId": "txn-001",
  "fraudProbability": 0.87,
  "decision": "BLOCK",
  "reason": "Fraud probability exceeds block threshold"
}
```

## Deploying to Kubernetes (minikube)

Point Docker at minikube's daemon so the cluster can use locally built images
without a registry:

```bash
minikube start
eval $(minikube docker-env)

docker build -t fraud-shield/ml-service:latest ./ml-service
docker build -t fraud-shield/java-service:latest ./java-service

kubectl apply -f k8s/
kubectl get pods -n fraud-shield -w
```

Reach the Java service:

```bash
minikube service java-service -n fraud-shield --url
```

## API reference

### `POST /api/v1/assess`

Request body (all fields required):

| Field             | Type    | Description                              |
|-------------------|---------|------------------------------------------|
| transactionId     | string  | Unique transaction id                    |
| amount            | number  | Transaction amount                       |
| merchantCategory  | integer | Encoded merchant category code (0-9)     |
| hourOfDay         | integer | Hour of day, 0-23                        |
| daysSinceLastTxn  | integer | Days since the account's last txn        |
| numTxns24h        | integer | Transactions on the account in last 24h  |
| isForeign         | boolean | Whether the transaction is cross-border  |
| accountAgeDays    | integer | Age of the account in days               |

### `GET /actuator/health`

Liveness/readiness probes used by Kubernetes.

## Risk policy

Decision thresholds are configurable in `application.yml` (or via
`RISK_THRESHOLD_BLOCK` / `RISK_THRESHOLD_REVIEW` env vars):

- `fraudProbability >= 0.80` → **BLOCK**
- `fraudProbability >= 0.50` → **REVIEW**
- otherwise → **APPROVE**

## Project layout

```
fraud-shield/
├── java-service/         Spring Boot API + decision layer
│   ├── src/main/java/com/fraudshield/
│   │   ├── controller/   REST endpoints
│   │   ├── service/      Risk scoring + thresholds
│   │   ├── client/       ML inference HTTP client
│   │   └── model/        Request/response records
│   ├── src/main/resources/static/
│   │   └── index.html    Browser UI (served at /)
│   ├── pom.xml
│   └── Dockerfile
├── ml-service/           FastAPI inference service
│   ├── train_model.py    Synthetic data + model training
│   ├── app.py            Inference API
│   └── Dockerfile
├── k8s/                  Kubernetes manifests
├── quickstart.py         No-Docker single-process runner (UI + model)
├── quickstart-requirements.txt
├── docker-compose.yml
└── README.md
```

## Notes

The model is trained on **synthetic** data with an injected fraud signal; it
demonstrates the end-to-end serving architecture rather than production fraud
accuracy. Swapping in a real model only requires replacing `fraud_model.joblib`
and aligning the feature contract.
