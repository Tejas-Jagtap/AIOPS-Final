# AIOps Panel Presentation — Demo Guide

## Quick Start (Before Presentation)

```powershell
# Terminal 1: Activate venv + start orchestrator
cd C:\Users\k64169500\Downloads\AIOPS-main\AIOPS-main
.\.venv\Scripts\Activate.ps1
python -m uvicorn orchestrator.main:app --port 8001

# Terminal 2: Run demo (when ready)
python demo_runner.py                 # Full 5-section demo
python demo_runner.py --quick         # Quick 3-min (sections 2+3)
python demo_runner.py --section 3     # Only live API demo
python demo_runner.py --interactive   # Pauses between sections
```

---

## Presentation Flow (15-20 min)

### Part 1: Architecture Overview (3 min)
```
python demo_runner.py --section 1
```
**Key Points:**
- 8-module architecture (orchestrator, training, collectors, autoscaler, etc.)
- 600 synthetic Jenkins builds (68% SUCCESS, 23% FAILURE, 9% UNSTABLE)
- 600 console log files, 10,080 CPU timeseries points
- 6 trained model files (XGBoost, TF-IDF, PyTorch Autoencoder, LSTM, scalers)

### Part 2: ML Model Results (3 min)
```
python demo_runner.py --section 2
```
**Key Metrics to Highlight:**
| Model | Metric | Value |
|-------|--------|-------|
| XGBoost Failure Prediction | F1 Score | 0.982 |
| XGBoost Failure Prediction | ROC AUC | 1.000 |
| Autoencoder Anomaly Detection | F1 Score | 0.931 |
| LSTM CPU Forecasting | RMSE | 0.070 |

**Show Plots:** Open `evaluation/plots/` folder and show:
- `xgboost_confusion_matrix.png` — Near-perfect classification
- `xgboost_roc_curve.png` — AUC = 1.0
- `anomaly_error_distribution.png` — Clear separation
- `lstm_actual_vs_predicted.png` — Trend following
- `model_comparison_summary.png` — All models compared
- `performance_summary_table.png` — Summary table for thesis

### Part 3: Live API Demo (5 min)
```
python demo_runner.py --section 3
```
**Show in browser:** http://localhost:8001/docs (Swagger UI)

**Manual API calls to demonstrate:**
```powershell
# Failure prediction
curl -X POST http://localhost:8001/predict_failure -H "Content-Type: application/json" -d '{"duration":180,"warnings":8,"errors":15,"failures":3,"log_length":25000,"tests_failed":8,"tests_passed":16}'

# Anomaly detection
curl -X POST http://localhost:8001/detect_anomaly -H "Content-Type: application/json" -d '{"log":"FATAL ERROR: Build FAILURE. npm ERR! segmentation fault core dumped."}'

# CPU forecast
curl -X POST http://localhost:8001/forecast_cpu -H "Content-Type: application/json" -d '{"cpu_history":[0.3,0.32,0.35,0.33,0.31,0.34,0.36,0.38,0.35,0.33,0.3,0.32,0.35,0.33,0.31,0.34,0.36,0.38,0.35,0.33,0.3,0.32,0.35,0.33,0.31,0.34,0.36,0.38,0.35,0.33,0.3,0.32,0.35,0.33,0.31,0.34,0.36,0.38,0.35,0.33,0.3,0.32,0.35,0.33,0.31,0.34,0.36,0.38,0.35,0.33,0.3,0.32,0.35,0.33,0.31,0.34,0.36,0.38,0.35,0.33]}'
```

### Part 4: CI/CD Integration (2 min)
```
python demo_runner.py --section 4
```
**Show Files:**
- `demo-todo-app/Jenkinsfile` — 5-stage pipeline
- `kubernetes_manifests/` — K8s deployment configs
- `prometheus/prometheus.yml` — Monitoring config

### Part 5: End-to-End Test (3 min)
```
python demo_runner.py --section 5
```
Or run the formal test suite:
```
python tests/test_e2e.py
```
Expected: **13/13 tests PASS**

---

## Panel Q&A — Anticipated Questions & Answers

### "How does the system integrate with CI/CD?"
→ Jenkins webhook triggers on build completion → sends build metadata + console log to orchestrator API → failure prediction + anomaly detection run in real-time → results feed into autoscaling decisions.

### "Why XGBoost for failure prediction?"
→ Works well with tabular data (8 features), handles class imbalance via scale_pos_weight, fast inference (<1ms), interpretable feature importance. Achieved 98.2% F1 score.

### "How does the autoencoder detect anomalies?"
→ Trained only on normal (SUCCESS) logs → learns to reconstruct normal patterns → failure logs have higher reconstruction error → threshold (95th percentile of normal errors) separates normal from anomalous.

### "How does predictive autoscaling work?"
→ Three signals combined: (1) LSTM-predicted CPU > 0.7 → scale up, (2) anomaly detected → scale up, (3) failure probability > 0.6 → scale up. Decision engine enforces min/max replicas and 5-min cooldown to prevent thrashing.

### "Why PyTorch instead of TensorFlow?"
→ Better Python 3.14 compatibility, cleaner model serialization, production-ready inference, and growing industry adoption.

### "What about real data vs synthetic?"
→ The system is designed to work with both. Collectors module (jenkins_collector.py, prometheus_collector.py) can collect real data from live Jenkins/Prometheus instances. Synthetic data validates the ML pipeline architecture.

### "How would you deploy this in production?"
→ Docker containers → K8s deployment (manifests provided) → ServiceAccount with RBAC for scaling permissions → Prometheus scraping metrics → Orchestrator running as ClusterIP service → LoadBalancer for external access.

---

## File Paths for Quick Reference

| What | Path |
|------|------|
| Orchestrator API | `orchestrator/main.py` |
| Failure Router | `orchestrator/routers/failure_router.py` |
| Anomaly Router | `orchestrator/routers/anomaly_router.py` |
| Forecast Router | `orchestrator/routers/forecast_router.py` |
| Autoscale Router | `orchestrator/routers/autoscale_router.py` |
| Decision Engine | `autoscaler/decision_engine.py` |
| XGBoost Training | `training/train_failure_xgboost.py` |
| Autoencoder Training | `training/train_log_anomaly.py` |
| LSTM Training | `training/train_cpu_lstm.py` |
| Data Generator | `training/generate_synthetic_data.py` |
| Evaluation | `evaluation/evaluate_all.py` |
| E2E Tests | `tests/test_e2e.py` |
| Demo Runner | `demo_runner.py` |
| Evaluation Plots | `evaluation/plots/` |
| All Metrics | `evaluation/metrics/all_metrics.json` |
| Jenkinsfile | `demo-todo-app/Jenkinsfile` |
| K8s Manifests | `kubernetes_manifests/` |
| Dockerfile | `Dockerfile` |
