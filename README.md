# AIOps: AI-Driven DevOps Intelligence Platform

> **MTech Final Year Project** — Predictive CI/CD Analytics with Machine Learning  
> Tejas Jagtap | M.Tech Computer Engineering

An intelligent operations platform that applies machine learning to CI/CD pipelines for **predictive failure analysis**, **log anomaly detection**, **resource forecasting**, and **automated Kubernetes scaling**.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────────┐ │
│  │   Jenkins     │  │   Prometheus     │  │   Application Logs    │ │
│  │  (CI/CD)      │  │  (Metrics)       │  │   (Console Output)    │ │
│  └──────┬───────┘  └────────┬─────────┘  └───────────┬───────────┘ │
└─────────┼──────────────────┼─────────────────────────┼─────────────┘
          │                  │                         │
          ▼                  ▼                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA COLLECTION LAYER                           │
│  ┌──────────────────┐  ┌─────────────────────┐                     │
│  │ jenkins_collector │  │ prometheus_collector │                     │
│  └──────────────────┘  └─────────────────────┘                     │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ML TRAINING LAYER                            │
│  ┌────────────────────┐ ┌───────────────────┐ ┌──────────────────┐ │
│  │ XGBoost Classifier  │ │ TF-IDF+Autoencoder│ │ LSTM Forecaster  │ │
│  │ (Failure Prediction)│ │ (Anomaly Detect.) │ │ (CPU Prediction) │ │
│  │ Accuracy: 98.3%     │ │ F1-Score: 91.8%   │ │ RMSE: 0.071      │ │
│  └────────────────────┘ └───────────────────┘ └──────────────────┘ │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (FastAPI)                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐  │
│  │/predict_   │ │/detect_    │ │/forecast_  │ │/autoscale      │  │
│  │ failure    │ │ anomaly    │ │ cpu        │ │                │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    KUBERNETES AUTOSCALER                             │
│  Predictive scaling based on ML model outputs                       │
│  Scale up/down before issues occur                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Results

| Model                    | Task                     | Metric              | Value |
| ------------------------ | ------------------------ | ------------------- | ----- |
| **XGBoost**              | Build Failure Prediction | Accuracy            | 98.3% |
|                          |                          | F1-Score            | 96.4% |
|                          |                          | ROC AUC (5-fold CV) | 99.0% |
| **TF-IDF + Autoencoder** | Log Anomaly Detection    | Accuracy            | 95.9% |
|                          |                          | F1-Score            | 91.8% |
|                          |                          | ROC AUC             | 98.9% |
| **LSTM**                 | CPU Usage Forecasting    | RMSE                | 0.071 |
|                          |                          | MAE                 | 0.044 |
|                          |                          | MAPE                | 9.56% |

---

## Project Structure

```
AIOPS/
├── demo-todo-app/            # Next.js application (CI/CD target)
│   ├── app/                  # App Router pages & API routes
│   │   ├── api/metrics/      # Prometheus metrics endpoint
│   │   ├── api/todos/        # CRUD API for todos
│   │   └── page.tsx          # Main UI
│   ├── __tests__/            # Jest test suite (24 tests)
│   ├── Jenkinsfile           # CI/CD pipeline definition
│   └── jenkins-setup/        # Jenkins Docker setup
│
├── collectors/               # Data collection modules
│   ├── jenkins_collector.py  # Jenkins REST API build collector
│   ├── prometheus_collector.py # Prometheus metrics collector
│   └── realtime_collector.py # Real-time streaming collector
│
├── training/                 # ML model training
│   ├── generate_synthetic_data.py  # Synthetic data generator
│   ├── train_failure_xgboost.py    # XGBoost failure classifier
│   ├── train_log_anomaly.py        # Autoencoder anomaly detector
│   ├── train_cpu_lstm.py           # LSTM CPU forecaster
│   └── data/                       # Training datasets
│       ├── jenkins/          # Build CSV + log files
│       └── prometheus/       # CPU timeseries CSV
│
├── orchestrator/             # FastAPI ML serving layer
│   ├── main.py               # Application entry point
│   ├── routers/              # API endpoint routers
│   │   ├── failure_router.py
│   │   ├── anomaly_router.py
│   │   ├── forecast_router.py
│   │   └── autoscale_router.py
│   ├── models/               # Trained model artifacts
│   │   ├── xgboost_failure.bin
│   │   ├── tfidf.pkl
│   │   ├── autoencoder.keras
│   │   ├── anomaly_threshold.pkl
│   │   ├── lstm_cpu.keras
│   │   └── cpu_scaler.pkl
│   └── utils/                # K8s & Prometheus clients
│
├── autoscaler/               # Kubernetes predictive scaler
│   ├── scaler.py             # PredictiveScaler class
│   └── decision_engine.py    # Scaling decision logic
│
├── evaluation/               # Model evaluation & visualization
│   ├── evaluate_all.py       # Publication-quality evaluation
│   ├── plots/                # 12 generated plots (PNG)
│   └── metrics/              # all_metrics.json
│
├── kubernetes_manifests/     # K8s deployment configs
├── prometheus/               # Prometheus monitoring setup
├── tests/                    # Integration & E2E tests
│   └── test_e2e.py           # 13-test end-to-end suite
│
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container build
└── README.md                 # This file
```

---

## Prerequisites

- **Python 3.10+** (tested with 3.13)
- **Node.js 18+** (for demo-todo-app)
- **Docker Desktop** (for Jenkins, Prometheus)
- **Minikube** (for Kubernetes autoscaling)
- **Git**

---

## Quick Start

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/Tejas-Jagtap/aiops-demo-todo-app.git
cd aiops-demo-todo-app
pip install -r requirements.txt
```

### 2. Generate Training Data

```bash
python training/generate_synthetic_data.py
```

Generates:

- 600 Jenkins build records with realistic feature distributions
- 600 corresponding console log files with class-distinctive vocabulary
- 10,080 CPU timeseries data points with daily/weekly patterns

### 3. Train ML Models

```bash
python training/train_failure_xgboost.py
python training/train_log_anomaly.py
python training/train_cpu_lstm.py
```

Trained models are saved to `orchestrator/models/`.

### 4. Run Evaluation

```bash
python evaluation/evaluate_all.py
```

Generates 12 publication-quality plots in `evaluation/plots/` and metrics in `evaluation/metrics/all_metrics.json`.

### 5. Start the Orchestrator

```bash
python -m uvicorn orchestrator.main:app --host 0.0.0.0 --port 8001
```

### 6. Test the API

```bash
# Run full E2E test suite (13 tests)
python tests/test_e2e.py

# Manual endpoint tests:
curl http://localhost:8001/

# Predict build failure
curl -X POST http://localhost:8001/predict_failure \
  -H "Content-Type: application/json" \
  -d '{"duration":120,"warnings":5,"errors":8,"failures":2,"log_length":25000,"tests_failed":5,"tests_passed":19,"tests_total":24}'

# Detect log anomaly
curl -X POST http://localhost:8001/detect_anomaly \
  -H "Content-Type: application/json" \
  -d '{"log":"<full console log text>"}'

# Forecast CPU usage (requires 60 data points)
curl -X POST http://localhost:8001/forecast_cpu \
  -H "Content-Type: application/json" \
  -d '{"cpu_history":[0.3, 0.35, 0.4, ...]}'
```

---

## Component Details

### 1. Demo Application (Next.js)

A full-stack Todo application serving as the CI/CD target:

- **Framework**: Next.js 14 with TypeScript, App Router
- **API**: RESTful CRUD endpoints (`/api/todos`)
- **Monitoring**: Prometheus metrics endpoint (`/api/metrics`)
- **Testing**: Jest test suite with 24 tests
- **CI/CD**: Jenkinsfile with 6 stages (Checkout → Install → Lint → Test → Build → Archive)

### 2. Data Collection

| Collector                    | Source               | Output                            |
| ---------------------------- | -------------------- | --------------------------------- |
| `jenkins_collector.py`       | Jenkins REST API     | Build metadata CSV + console logs |
| `prometheus_collector.py`    | Prometheus HTTP API  | CPU/memory timeseries CSV         |
| `realtime_collector.py`      | Jenkins + Prometheus | Streaming real-time data          |
| `generate_synthetic_data.py` | Synthetic generation | Training-ready datasets           |

### 3. ML Models

#### XGBoost Failure Prediction

- **Input**: 8 build features (duration, warnings, errors, failures, log_length, tests_failed, tests_passed, tests_total)
- **Output**: Failure probability (0.0–1.0)
- **Architecture**: XGBoost binary classifier with `scale_pos_weight` balancing
- **Training**: 480 train / 120 test, stratified split, 5-fold cross-validation

#### TF-IDF + Autoencoder Anomaly Detection

- **Input**: Raw console log text
- **Pipeline**: Text preprocessing → TF-IDF vectorization (500 features, bigrams, sublinear TF) → Autoencoder reconstruction
- **Autoencoder**: Dense 500→128→64→**32**→64→128→500 with BatchNormalization & Dropout(0.3)
- **Detection**: Anomaly if reconstruction MSE > threshold (mean + 2σ of training errors)
- **Training**: 601 log files, 100 epochs, Adam optimizer (lr=0.0005)

#### LSTM CPU Forecasting

- **Input**: 60 timesteps of normalized CPU usage history
- **Output**: Predicted CPU usage at t+10
- **Architecture**: LSTM(128, return_sequences)→Dropout(0.2)→LSTM(64)→Dropout(0.2)→Dense(32, ReLU)→Dense(1)
- **Training**: 10,080 timeseries points, 80/20 temporal split, MinMaxScaler normalization

### 4. FastAPI Orchestrator

| Endpoint                   | Method | Description                          |
| -------------------------- | ------ | ------------------------------------ |
| `/`                        | GET    | Service info and available endpoints |
| `/predict_failure`         | POST   | Predict build failure probability    |
| `/detect_anomaly`          | POST   | Detect anomalies in console logs     |
| `/forecast_cpu`            | POST   | Forecast CPU usage from history      |
| `/autoscale`               | POST   | Trigger predictive autoscaling       |
| `/detect_anomaly/health`   | GET    | Anomaly model health check           |
| `/autoscale/status/{name}` | GET    | Autoscaler status for deployment     |

Interactive API docs available at `http://localhost:8001/docs` (Swagger UI).

### 5. Kubernetes Autoscaler

Predictive scaling engine that uses ML model outputs:

- **Scale Up**: When predicted CPU > 70% OR failure probability > 60% OR anomaly detected
- **Scale Down**: When predicted CPU < 30% AND no anomalies AND low failure risk
- **Integration**: Kubernetes Python client for deployment replica management

---

## Evaluation Plots

The evaluation suite generates 12 publication-quality visualizations:

| #   | Plot                             | Description                         |
| --- | -------------------------------- | ----------------------------------- |
| 1   | `xgboost_confusion_matrix.png`   | Failure prediction confusion matrix |
| 2   | `xgboost_roc_curve.png`          | ROC curve with AUC score            |
| 3   | `xgboost_pr_curve.png`           | Precision-Recall curve              |
| 4   | `xgboost_feature_importance.png` | Feature importance ranking          |
| 5   | `anomaly_confusion_matrix.png`   | Anomaly detection confusion matrix  |
| 6   | `anomaly_roc_curve.png`          | ROC curve for anomaly detection     |
| 7   | `anomaly_error_distribution.png` | Reconstruction error distribution   |
| 8   | `lstm_actual_vs_predicted.png`   | CPU actual vs predicted overlay     |
| 9   | `lstm_residuals.png`             | Forecast residual distribution      |
| 10  | `lstm_scatter.png`               | Predicted vs actual scatter plot    |
| 11  | `model_comparison_summary.png`   | Cross-model metric comparison       |
| 12  | `performance_summary_table.png`  | Tabular performance summary         |

---

## Infrastructure Setup

### Jenkins (Docker)

```bash
cd demo-todo-app/jenkins-setup
docker-compose up -d
# Access at http://localhost:8080
```

### Prometheus (Docker)

```bash
cd prometheus
docker-compose up -d
# Access at http://localhost:9090
```

### Minikube (Kubernetes)

```bash
minikube start --driver=docker
kubectl apply -f kubernetes_manifests/
kubectl get pods -w
```

---

## Testing

```bash
# End-to-end integration test (13 tests)
python tests/test_e2e.py

# Demo app unit tests (24 tests)
cd demo-todo-app && npm test

# Individual model training verification
python training/train_failure_xgboost.py
python training/train_log_anomaly.py
python training/train_cpu_lstm.py
```

---

## Research & Thesis

This project demonstrates the application of:

1. **Gradient Boosted Trees (XGBoost)** for CI/CD build outcome prediction
2. **Unsupervised Autoencoders** for log anomaly detection without labeled anomaly data
3. **Recurrent Neural Networks (LSTM)** for time-series resource forecasting
4. **Predictive Autoscaling** — proactive infrastructure management driven by ML predictions

### Key Contributions

- End-to-end AIOps pipeline from data collection to automated remediation
- Multi-model orchestration serving predictions via unified REST API
- Predictive (vs. reactive) Kubernetes autoscaling using ML-derived signals
- Publication-quality evaluation with 12 visualizations and comprehensive metrics

---

## Tech Stack

| Layer         | Technology                              |
| ------------- | --------------------------------------- |
| Application   | Next.js 14, TypeScript, React           |
| CI/CD         | Jenkins (Docker), Jenkinsfile pipeline  |
| Monitoring    | Prometheus, custom metrics endpoint     |
| ML Framework  | TensorFlow/Keras, XGBoost, scikit-learn |
| API Server    | FastAPI, Uvicorn                        |
| NLP           | TF-IDF vectorization (scikit-learn)     |
| Container     | Docker, Minikube                        |
| Orchestration | Kubernetes, Python K8s client           |
| Language      | Python 3.13, TypeScript                 |

---

## License

MIT License — Tejas Jagtap, 2025
