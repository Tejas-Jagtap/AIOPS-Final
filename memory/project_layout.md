---
name: project-layout
description: Where the main pieces live in AIOPS-main — orchestrator, training, collectors, autoscaler, demo app, paper sources
metadata:
  type: project
---

Top-level layout of `g:\Mtech-Project\AIOPS-main`:

- `orchestrator/` — FastAPI ML serving layer. Entry: `main.py` (lifespan loads all models on startup; chdir's to project root). Routers in `routers/{failure,anomaly,forecast,autoscale}_router.py`. Utilities: `utils/{log_preprocess,cpu_preprocess,k8s_client,prometheus_client}.py`. Model artifacts: `models/`.
- `training/` — `train_failure_xgboost.py`, `train_log_anomaly.py`, `train_cpu_lstm.py`, `generate_synthetic_data.py`. Data lives in `training/data/jenkins/` (build CSV + per-build logs) and `training/data/prometheus/` (CPU timeseries CSV).
- `collectors/` — `jenkins_collector.py`, `prometheus_collector.py`, `realtime_collector.py` (live streaming).
- `autoscaler/` — `scaler.py` (`PredictiveScaler`) and `decision_engine.py` (`DecisionEngine`). Priority policy: anomaly → alert only; high failure prob → HOLD (don't scale a failing build); else CPU thresholds drive scale up/down with cooldown.
- `evaluation/` — `evaluate_all.py` produces 12 plots in `plots/` and `metrics/all_metrics.json`.
- `demo-todo-app/` — Next.js 14 TypeScript todo app used as the CI/CD target. Has its own Jenkinsfile, Jest tests, Prometheus `/api/metrics` endpoint. NOT part of the AIOps system itself — it exists to produce real build logs and metrics.
- `kubernetes_manifests/` — orchestrator, autoscaler, demo-app deployments + service YAMLs.
- `prometheus/` — Prom configs (`prometheus.yml`, `prometheus-windows.yml`) and docker-compose.
- `scripts/` — `load_generator.py`, PowerShell helpers (`collect_jenkins_logs.ps1`, `deploy-minikube.ps1`).
- `tests/test_e2e.py` — 13-test end-to-end suite against running orchestrator.
- `Journal Paper/sn-article.tex` (Springer Nature template) + `Conference Paper/` — paper sources.
- `Report/`, `Presentation/`, `DEMO_GUIDE.md`, `PRESENTATION_GUIDE.md` — thesis deliverables.
