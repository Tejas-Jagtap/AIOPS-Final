---
name: project-aiops-overview
description: Top-level shape of the AIOPS-main repo — three ML models behind a FastAPI orchestrator that drives a custom predictive Kubernetes autoscaler, with a Next.js demo app feeding Jenkins CI
metadata:
  type: project
---

`g:\Mtech-Project\AIOPS-main` is an end-to-end AIOps system for CI/CD pipelines. It is the implementation behind a Springer Nature journal paper (`Journal Paper/sn-article.tex`).

**Three ML models** (artifacts in `orchestrator/models/`):
- **XGBoost** failure prediction — `xgboost_failure.bin` (joblib). 8 build features (duration, warnings, errors, failures, log_length, tests_failed/passed/total). Test accuracy 0.992, ROC-AUC 1.0 in `evaluation/metrics/all_metrics.json`.
- **TF-IDF + Autoencoder** log anomaly detection — `tfidf.pkl` + `autoencoder.pth` + `anomaly_threshold.pkl`. PyTorch, Dense 500→128→64→32→64→128→500 with BN+Dropout(0.3). Threshold = mean + 2σ of train recon errors.
- **LSTM** CPU forecast — `lstm_cpu.pth` + `cpu_scaler.pkl`. PyTorch: LSTM(128)→Dropout→LSTM(64)→Dropout→Dense(32, ReLU)→Dense(1). Lookback 60, horizon t+10. RMSE 0.070.

**Note on framework:** README still says "TensorFlow/Keras" and uses `.keras` paths in places, but the actual saved artifacts are `.pth` and the router code at `orchestrator/routers/anomaly_router.py` and `orchestrator/routers/forecast_router.py` loads PyTorch checkpoints via `torch.load`. The code is PyTorch; the README/PROJECT_CONTEXT.md are out of date on this point.

**Why:** Unify supervised, unsupervised, and time-series ML into one closed-loop AIOps stack for CI/CD — the paper's claimed research gap is that prior work treats these as isolated problems.

**How to apply:** When editing orchestrator code, treat `.pth` + `Autoencoder`/`LSTMModel` `nn.Module` classes in the routers as ground truth, not the Keras references in docs. The model class definitions in the routers MUST match the training scripts byte-for-byte or `load_state_dict` will fail.
