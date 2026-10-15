# PROJECT CONTEXT – AIOps Framework for Predictive CI/CD and Kubernetes Autoscaling

This repository will contain a complete implementation of an AIOps system that:

1. Predicts Jenkins CI/CD build failures using machine learning (XGBoost).
2. Detects anomalies in Jenkins console logs using TF-IDF + Autoencoder.
3. Forecasts Kubernetes CPU workload using an LSTM model trained on Prometheus metrics.
4. Exposes all models via a FastAPI-based “AIOps Orchestrator.”
5. Performs predictive autoscaling through a custom Kubernetes autoscaler using the Kubernetes Python client.

The system must be fully modular, production-ready, and runnable on **Windows + VS Code**.

---

# 1. High-Level Architecture

The full system contains:

### 1.1 Data Ingestion Layer

- **Jenkins Collector**
  - Uses Jenkins REST API.
  - Collects:
    - build metadata (result, duration, timestamp)
    - console logs
  - Stores data under `training/data/jenkins/`.

- **Prometheus Collector**
  - Uses Prometheus HTTP API.
  - Collects:
    - CPU usage
    - Memory
    - Pod count
  - Stores CSV under `training/data/prometheus/`.

### 1.2 Machine Learning Models

- **Failure Prediction (XGBoost)**
  - Input: build metadata
  - Output: failure probability (0.0–1.0)
  - Saves: `models/xgboost_failure.bin`

- **Log Anomaly Detection (Autoencoder + TF-IDF)**
  - Input: Jenkins log text
  - Output: anomaly_score + is_anomaly
  - Saves:
    - `models/tfidf.pkl`
    - `models/autoencoder.keras`

- **CPU Forecasting (LSTM)**
  - Input: Prometheus CPU metrics
  - Output: predicted CPU for next N minutes
  - Saves:
    - `models/lstm_cpu.keras`
    - `models/cpu_scaler.pkl`

### 1.3 AIOps Orchestrator (FastAPI)

Exposes:

POST /predict_failure
POST /detect_anomaly
POST /forecast_cpu
POST /autoscale

markdown
Copy code

Loads all ML models at startup.

### 1.4 Predictive Autoscaler

Uses:

- CPU forecast
- Anomaly score
- Failure probability
- Replica limits
- Cooldown periods

Actions:

- Scale up/down using Kubernetes Python client.

---

# 2. Required Repository Structure

The entire project must follow EXACTLY this structure:

aiops-system/
│
├── orchestrator/
│ ├── main.py
│ ├── routers/
│ │ ├── failure_router.py
│ │ ├── anomaly_router.py
│ │ ├── forecast_router.py
│ │ └── autoscale_router.py
│ ├── utils/
│ │ ├── log_preprocess.py
│ │ ├── cpu_preprocess.py
│ │ ├── k8s_client.py
│ │ └── prometheus_client.py
│ └── models/
│ ├── xgboost_failure.bin
│ ├── tfidf.pkl
│ ├── autoencoder.keras
│ ├── lstm_cpu.keras
│ └── cpu_scaler.pkl
│
├── training/
│ ├── train_failure_xgboost.py
│ ├── train_log_anomaly.py
│ ├── train_cpu_lstm.py
│ └── data/
│ ├── jenkins/
│ └── prometheus/
│
├── collectors/
│ ├── jenkins_collector.py
│ └── prometheus_collector.py
│
├── autoscaler/
│ ├── decision_engine.py
│ └── scaler.py
│
├── kubernetes_manifests/
│ ├── orchestrator-deployment.yaml
│ ├── autoscaler-deployment.yaml
│ └── service.yaml
│
├── Dockerfile
├── requirements.txt
├── README.md
└── PROJECT_CONTEXT.md

pgsql
Copy code

Copilot MUST create all missing files in this structure.

---

# 3. Input/Output Requirements (STRICT)

## 3.1 Failure Prediction API

### Input JSON

{
"duration": 300,
"warnings": 12,
"errors": 1,
"tests_failed": 2,
"tests_passed": 210
}

shell
Copy code

### Output JSON

{
"failure_probability": 0.82
}

makefile
Copy code

## 3.2 Anomaly Detection API

Input:
{"log": "<raw Jenkins log text>"}

makefile
Copy code

Output:
{
"anomaly_score": 0.41,
"is_anomaly": true
}

makefile
Copy code

## 3.3 CPU Forecast API

Output:
{
"predicted_cpu": 0.77
}

makefile
Copy code

## 3.4 Autoscaling API

Output:
{
"action": "scale_up",
"current_replicas": 3,
"new_replicas": 5
}

markdown
Copy code

---

# 4. Copilot MUST Follow These Rules

## 4.1 Coding Rules

- Always use clean, modular Python code.
- Use dependency injection where appropriate.
- Never hardcode credentials or URLs.
- Always load API endpoints from environment variables.
- Keep training scripts separate from inference code.
- Insert docstrings for every function.
- Include error handling.
- Use Pydantic models for all FastAPI request/response schemas.

## 4.2 Orchestrator Rules

- Must load all ML models at startup.
- Must cache models in memory.
- Must use async FastAPI endpoints.
- Must log all requests and inference results.

## 4.3 Autoscaler Rules

- Must use Kubernetes Python client.
- Must respect:
  - min_replicas
  - max_replicas
  - cooldown seconds
- Must never scale more than +3 replicas per call.
- Must return new replica count as JSON.

## 4.4 LSTM Rules

- Use Keras Sequential API.
- Use MinMaxScaler.
- Save scaler separately.

## 4.5 Autoencoder Rules

- Use Dense layers.
- Reconstruction error threshold must be configurable.

## 4.6 XGBoost Rules

- Use XGBClassifier.
- Export using joblib.

---

# 5. Technologies That MUST Be Used

- Python 3.10+
- FastAPI
- Uvicorn
- TensorFlow / Keras
- Scikit-learn
- XGBoost
- Pandas / NumPy
- Jenkins API
- Prometheus HTTP API
- Kubernetes Python client
- Docker
- Minikube (for local testing)

---

# 6. Full System Workflow

1. Jenkins Collector gathers:
   - logs → anomaly detection
   - metadata → failure prediction

2. Prometheus Collector gathers:
   - CPU metrics → LSTM forecasting

3. Training scripts produce:
   - xgboost_failure.bin
   - tfidf.pkl + autoencoder.keras
   - lstm_cpu.keras + cpu_scaler.pkl

4. FastAPI Orchestrator loads all models:
   - /predict_failure → XGBoost
   - /detect_anomaly → Autoencoder
   - /forecast_cpu → LSTM
   - /autoscale → Predictive decision engine

5. Autoscaler evaluates:
   - predicted CPU
   - anomaly signals
   - failure probability

6. Autoscaler applies scaling changes through Kubernetes.

---

# 7. Copilot Tasks (MANDATORY)

Copilot must now generate:

- All Python files in the structure above.
- Complete FastAPI application.
- All ML training scripts.
- Jenkins & Prometheus collectors.
- Predictive autoscaler.
- Dockerfile.
- Kubernetes deployment YAMLs.
- README with installation + usage instructions (Windows-friendly).
- Example .env template.

---

# 8. Demo Todo App - Real Monitoring Setup

The project includes a demo Next.js application (`demo-todo-app/`) that exposes real Prometheus metrics.

## Metrics Endpoint

`GET /api/metrics` returns Prometheus-format metrics:

- `http_requests_total` - Counter of total HTTP requests
- `http_request_duration_seconds` - Request duration
- `app_todos_total` - Current number of todos
- `app_todos_completed` - Completed todos count
- `app_errors_total` - Error counter
- `app_uptime_seconds` - Application uptime
- `nodejs_memory_heap_used_mb` - Memory usage

## Data Collection Scripts

- `scripts/load_generator.py` - Generates realistic app traffic
- `collectors/realtime_collector.py` - Collects live metrics to CSV

## Prometheus Configuration

`prometheus/prometheus-windows.yml` is configured to scrape:

1. Prometheus itself at `localhost:9090`
2. Demo todo app at `host.docker.internal:3000`

See `docs/REAL_MONITORING.md` for complete setup instructions.

---

# 9. Final Instruction for Copilot

This context defines the complete system.  
All generated code MUST strictly follow this design.
