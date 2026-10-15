---
name: project-run-and-metrics
description: How to actually run/verify the AIOPS-main orchestrator on this machine (the .venv is broken) and which metric numbers are authoritative vs stale
metadata:
  type: project
---

**Running the system (Windows, this machine):**
- The bundled `.venv` is BROKEN — its base interpreter `c:\python314\python.exe` no longer exists. Do not use `.venv\Scripts\python.exe`.
- Use **`C:\Python313\python.exe`** instead (Python 3.13.5). All deps are installed there globally: fastapi, uvicorn, torch 2.12 (CPU), xgboost, scikit-learn, joblib, python-pptx 1.0.2.
- Start orchestrator: `C:\Python313\python.exe -m uvicorn orchestrator.main:app --port 8001` (E2E suite hard-codes port **8001**).
- Set `PYTHONIOENCODING=utf-8` before running Python that prints ✓/✗ (Windows cp1252 console crashes on the Unicode checkmarks in `tests/test_e2e.py` and demo output).
- Verified 2026-07-01: orchestrator loads all 6 models and **`tests/test_e2e.py` passes 13/13** (SUCCESS build→0.001 failure prob, FAILURE build→0.97, failure log flagged anomaly, CPU forecast in range). `/autoscale` returns 500/503 without a live K8s cluster — expected.

**Authoritative metrics** = `evaluation/metrics/all_metrics.json` (matches the Springer journal paper tables). Use these:
- XGBoost: Acc 0.992, Prec 0.964, Recall 1.000, F1 0.982, ROC-AUC 1.000; CV F1 0.975±0.009.
- Autoencoder: Acc 0.967, Prec 0.871, Recall 1.000, F1 0.931, ROC-AUC 1.000.
- LSTM: MSE 0.0049, RMSE 0.0698, MAE 0.0433, MAPE 9.68%, R² 0.455.
- The plots in `evaluation/plots/` bake in these same numbers (anomaly ROC AUC = 1.000).

**Stale numbers — do NOT quote:** `README.md`, `PRESENTATION_GUIDE.md`, and the old `Presentation/create_ppt.py`/Phase-2 PPTX carry an earlier run (e.g. XGBoost acc 98.3% / F1 96.4%, anomaly F1 91.8% / AUC 0.989). These are outdated; prefer [[project-aiops-overview]] and the JSON above.

See [[project-layout]] for where things live.
