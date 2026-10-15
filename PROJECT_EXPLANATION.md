# AIOps Project — Complete Explanation (Defense Study Guide)

> The full story of the project, told in order. Read top-to-bottom once and every panel
> question becomes a variation of something you already know.
>
> Companion docs: `FINAL_PRESENTATION_SCRIPT.md` (what to say per slide) ·
> `PANEL_QA_BANK.md` (60 drilled Q&As) · `DEMO_GUIDE.md` (live demo steps).

---

## 1. The One-Liner (memorize this cold)

> *"I built a closed-loop AIOps framework: three ML models — failure prediction, log
> anomaly detection, CPU forecasting — served by one FastAPI orchestrator, driving a
> predictive Kubernetes autoscaler. It predicts problems before they happen and acts on
> them automatically."*

If you ever blank, fall back to: **"three models, one orchestrator, one autoscaler, one
closed loop."**

---

## 2. The Problem (why this project exists)

Modern software teams ship code through **CI/CD pipelines** (Jenkins builds, tests, and
deploys automatically) onto **Kubernetes** (which runs the app in containers and scales
it). Both generate huge volumes of operational data: build metadata, console logs, CPU
metrics.

The problem: everything today is **reactive**.

- A build failure is discovered only *after* the build ran — compute already wasted,
  deployment already delayed.
- Log problems are found by a human reading thousands of lines *after* something broke.
- Kubernetes' built-in autoscaler (HPA) adds pods only *after* CPU has already spiked —
  users feel the slowdown first, then the fix arrives.

**AIOps** (Artificial Intelligence for IT Operations — term coined by Gartner) applies
ML to this operational data to flip operations from reactive to **predictive**.

**The research gap:** prior papers each solve exactly one slice — one does autoscaling,
another does log anomalies, another does failure prediction, and the "agentic AIOps"
papers describe closed loops *conceptually* without building anything. **Nobody unifies
all three signals in one system that actually acts on Kubernetes.** That unification is
the contribution.

---

## 3. The Architecture (the four-layer closed loop)

This is the most important mental model (slide 10):

1. **Data collection layer** (`collectors/`) — `jenkins_collector.py` pulls build
   metadata and console logs from the Jenkins REST API; `prometheus_collector.py` pulls
   CPU/memory metrics from the Prometheus HTTP API; `realtime_collector.py` streams
   continuously.
2. **ML layer** (`training/` produces artifacts in `orchestrator/models/`) — three
   models, one per signal type:
   - **XGBoost** → build failure probability (supervised classification)
   - **TF-IDF + Autoencoder** → log anomaly score (unsupervised)
   - **LSTM** → CPU forecast 10 minutes ahead (supervised regression)
3. **Orchestrator layer** (`orchestrator/`) — one FastAPI service loads all models at
   startup and exposes four REST endpoints: `/predict_failure`, `/detect_anomaly`,
   `/forecast_cpu`, `/autoscale`.
4. **Action layer** (`autoscaler/`) — the `DecisionEngine` fuses all three model
   outputs into one scaling decision; `PredictiveScaler` executes it via the Kubernetes
   Python client (changes the replica count of a deployment).

**Why "closed-loop" is the key phrase:** the scaling action changes the cluster → the
cluster produces new metrics → the collectors pick them up → the next prediction cycle
uses them. Prediction → decision → action → feedback → prediction. Most research stops
at "here's a prediction" (open loop). This system completes the circle.

---

## 4. The Data (expect the heaviest questioning here)

Training used a **synthetic but realistic** dataset — own this confidently:

- **600 Jenkins builds** — realistic distribution: 410 SUCCESS / 137 FAILURE /
  53 UNSTABLE (68/23/9%). Each build has 8 metadata features.
- **600 console logs** — one per build, with class-distinctive vocabulary (failure logs
  contain ERROR/FATAL/exception terms; success logs don't).
- **10,080 CPU data points** — exactly **7 days × 24 hours × 60 minutes** of per-minute
  data, built as: daily (diurnal) base pattern + weekly modulation + Gaussian noise +
  randomly injected spikes. Range 0.125–0.934, mean 0.363.

**Why synthetic? Three defensible reasons:**

1. **Reproducibility** — anyone can regenerate the exact experiment.
2. **Known ground-truth labels** — you can't rigorously compute recall without knowing
   the truth.
3. **Controlled evaluation** — isolate whether the *architecture* works before adding
   real-world noise.

**The crucial counter-punch:** the collectors are real code that works against live
Jenkins and Prometheus — synthetic data plugs into the exact same pipeline. Real-data
validation (TravisTorrent, BuildFast) is explicitly stated future work.

**Preprocessing:** 8 engineered numeric features for builds; TF-IDF vectorization
(500 dimensions, n-grams 1–2) for logs; MinMax scaling to [0,1] + sliding 60-minute
windows for CPU.

---

## 5. Model 1 — XGBoost Failure Prediction

**What it does:** takes 8 numbers describing a build → outputs the probability the
build fails.

**The 8 features:** duration, warnings, errors, failures, log_length, tests_failed,
tests_passed, tests_total.

**Why XGBoost:** the gold standard for **small, structured, tabular data** — exactly
this input (600 rows × 8 features).

- A neural net would overfit at this scale.
- Logistic regression can't capture non-linear patterns (both very short *and* very
  long builds fail).
- Versus random forest: boosting builds trees *sequentially*, each correcting the
  previous one's mistakes — usually better accuracy, plus built-in feature importance
  for interpretability.

**How it's trained** (`training/train_failure_xgboost.py`): ~100 trees, 80/20
stratified split, class imbalance (~3:1) handled with `scale_pos_weight ≈ 3` (up-weights
failure examples in the loss), 5-fold cross-validation to prove stability.

**Results:** Accuracy **99.2%**, Precision 96.4%, **Recall 100%**, **F1 = 0.982**,
ROC-AUC 1.000. On the 120-build test set: 92 successes correct, 27 failures correct,
1 false positive, **0 false negatives**.

**The recall-100% defense:** it's a design *goal*, not luck. In CI, a missed failure
that reaches production costs vastly more than one false alarm — the model is weighted
to prioritize recall. Say openly: "on noisier real data I'd expect a small drop — that's
why real-data validation is my next step."

**Feature importance** shows tests_passed, tests_total, and errors dominate — matching
published empirical CI-failure studies, i.e. the model learned *real* signal.

---

## 6. Model 2 — TF-IDF + Autoencoder Log Anomaly Detection

**What it does:** takes raw console log text → outputs an anomaly score and a yes/no
flag.

**The two stages:**

1. **TF-IDF** converts text into a 500-dimensional vector, weighting words by how
   rare-but-informative they are — "OutOfMemoryError" scores high, "the" scores near
   zero. Cheap, fast, interpretable, CPU-only.
2. **Autoencoder** (PyTorch): a neural network shaped
   **500 → 128 → 64 → 32 → 64 → 128 → 500** with BatchNorm and Dropout(0.3). It
   compresses the input through the 32-neuron bottleneck and tries to reconstruct it.

**The core intuition (know this analogy):** the autoencoder is trained **only on normal
logs**, so it becomes an expert at reconstructing "normal." Feed it an anomalous log and
it reconstructs *badly* — high reconstruction error (MSE). Like someone who has only
ever heard English trying to repeat back French. **Anomaly = reconstruction error above
a threshold**, set at the 95th percentile of the normal training errors (≈ mean + 2σ;
actual value 0.00118).

**Why unsupervised is the selling point:** real DevOps teams *don't have labelled
anomalies* — you can't supervise on labels that don't exist. And an autoencoder catches
**novel** anomalies it has never seen; a supervised classifier only recognizes anomaly
types it was trained on.

**Results:** Accuracy 96.7%, Precision 87.1%, **Recall 100%**, **F1 = 0.931**,
AUC 1.000. Precision 87% means ~13% false alarms — an intentional trade-off from the
conservative threshold: a missed anomaly can cascade into an outage, a false alert costs
a glance.

**Live proof (from the E2E test):** a real SUCCESS log scores 0.0008 (below threshold →
normal); a FAILURE log scores 0.0020 (above → anomaly). The error-distribution plot
shows two cleanly separated clusters.

---

## 7. Model 3 — LSTM CPU Forecasting

**What it does:** takes the last **60 minutes** of CPU usage → predicts CPU
**10 minutes ahead**.

**Why 10 minutes matters:** that's the lead time Kubernetes needs to schedule and warm
up new pods *before* the load arrives. The forecast horizon is literally what makes the
autoscaler "predictive" instead of reactive.

**Why LSTM:** CPU is sequential data where order matters and there are long-range
patterns (daily cycles). LSTM's gating mechanism (forget/input/output gates) remembers
long-term patterns while reacting to recent changes. ARIMA/Prophet are statistical
baselines that struggle with non-linear patterns; transformers need far more data and
compute. LSTM is the proven middle ground (the Guruge 2025 paper cited uses it too).

**Architecture** (PyTorch, `training/train_cpu_lstm.py`):
**LSTM(128) → Dropout → LSTM(64) → Dropout → Dense(32, ReLU) → Dense(1)**.
~10,000 training sequences from sliding windows, **chronological** 80/20 split (never
random for time series — that would leak the future into training), early stopping +
learning-rate reduction on plateau.

**Results:** RMSE **0.070**, MAPE **9.68%** (under the 10% rule-of-thumb for a good
forecast), MAE 0.043, R² 0.455.

**The R² = 0.455 defense (they WILL ask):** CPU contains random spikes that are
*fundamentally unpredictable* — no model can foresee a random spike, and R² punishes you
for not predicting them. But for autoscaling you *want* the model to track the **trend**
and smooth the noise: if it chased every blip, the autoscaler would flap (scale up/down
constantly). **Low R² + low RMSE is exactly the right behavior for this use case.** Say
it with confidence — it's a design insight, not a weakness.

---

## 8. The Orchestrator (Phase-III integration work)

`orchestrator/main.py` is a FastAPI app. At startup (lifespan event) it loads all
**6 model artifacts** into memory:

| Artifact | Purpose |
|---|---|
| `xgboost_failure.bin` | failure-prediction model |
| `tfidf.pkl` | log vectorizer |
| `autoencoder.pth` | anomaly model (PyTorch) |
| `anomaly_threshold.pkl` | anomaly decision threshold |
| `lstm_cpu.pth` | CPU forecaster (PyTorch) |
| `cpu_scaler.pkl` | MinMax scaler for CPU |

Each capability is its own router: `routers/failure_router.py`, `anomaly_router.py`,
`forecast_router.py`, `autoscale_router.py`.

**Talking points:** async endpoints; Pydantic schemas validate every request/response;
models cached in memory so inference is milliseconds (no reload per request); Swagger UI
at `/docs` for live demo; all external endpoints configured via environment variables.

**One trap to know (QA bank Q34):** some older docs say TensorFlow/Keras, but **the
implementation is PyTorch** — artifacts are `.pth`, loaded with `torch.load`. If asked,
own it: "early design docs said Keras; the running system is PyTorch."

---

## 9. The Predictive Autoscaler (the decision brain)

`autoscaler/decision_engine.py` runs a **priority policy** each cycle:

1. Log anomaly detected → **raise ALERT** (non-blocking — informational).
2. Failure probability > 0.6 → **HOLD** — don't scale infrastructure for a build that's
   about to fail; extra pods won't save it, they just burn money.
3. Predicted CPU ≥ 0.7 → **SCALE UP +2 replicas**.
4. Predicted CPU ≤ 0.3 → **SCALE DOWN −1 replica**.
5. Otherwise → **MAINTAIN**.

**Guardrails:** 1–10 replicas, 300-second cooldown between actions.

**Anti-flapping — three mechanisms:** the cooldown; asymmetric steps (up fast +2, down
slow −1); and the LSTM smoothing noise so it never reacts to random blips.

**The HPA contrast (slide-18 material):** HPA reacts to *current* CPU after the
threshold is crossed → lag. This system acts on the *forecast* → pods exist before the
spike. HPA sees only CPU; this fuses **three signals** — the HOLD rule is a decision HPA
is structurally incapable of making. The HOLD rule is the best example of *why* unifying
the three models matters (QA bank Q4/Q40).

`autoscaler/scaler.py` (`PredictiveScaler`) executes decisions through the official
Kubernetes Python client. Without a live cluster, `/autoscale` degrades gracefully
(returns 5xx while everything else works) — expected behavior, not a bug.

---

## 10. Validation (proof it all works)

**13/13 automated E2E tests pass** (`tests/test_e2e.py`) — re-verified 2026-07-03:

| Layer | Tests | What's checked |
|---|---|---|
| Data | 3 | files exist, 600 builds with correct distribution, CPU in valid range |
| Model | 2 | all 6 artifacts load; evaluation outputs exist |
| API | 7 | SUCCESS build → 0.0009 failure prob; FAILURE build → 0.9743; normal log passes; failure log flagged; forecast in range; autoscale degrades gracefully |
| Full pipeline | 1 | failure + anomaly + forecast fused into one scaling decision |

**Real infrastructure exists:** `demo-todo-app/` is a Next.js 14 TypeScript app with
Jest tests, a 6-stage `Jenkinsfile`, a Prometheus `/api/metrics` endpoint, Docker
images, and Kubernetes manifests.

**Important nuance (Q60):** the todo app is **not part of the AIOps system** — it's the
*target* application that generates real builds, logs and metrics to exercise the
pipeline.

**Live demo:**

```bash
C:\Python313\python.exe -m uvicorn orchestrator.main:app --port 8001
# then open http://localhost:8001/docs
```

(Do **not** use the bundled `.venv` — it's broken; use the system Python 3.13.)

---

## 11. Results Summary + Honest Limitations

| Model | Task | Headline numbers |
|---|---|---|
| XGBoost | Failure prediction | F1 **0.982**, Recall **100%**, Acc 99.2%, AUC 1.000 |
| TF-IDF + Autoencoder | Log anomaly (unsupervised) | F1 **0.931**, Recall **100%**, Acc 96.7%, AUC 1.000 |
| LSTM | CPU forecast (t+10 min) | RMSE **0.070**, MAPE **9.68%**, R² 0.455 |

**Own the three limitations *before* they're asked — it reads as maturity:**

1. **Synthetic data** — AUC 1.000 partly reflects clean separability; real data will be
   noisier (mitigation: real-data validation is next).
2. **No concept-drift handling yet** — models are static; retraining pipeline is future
   work.
3. **TF-IDF ignores word order** — LogBERT-style transformer embeddings are future work.

Plus: the HPA-vs-predictive load benchmark has not been run yet.

> ⚠️ **Number discrepancy to be aware of:** the deck and QA bank say CV F1 =
> **0.975 ± 0.009**, but the authoritative `evaluation/metrics/all_metrics.json` says
> **0.978 ± 0.014**. Both round to ≈0.98 with tiny variance — if asked, say
> *"cross-validation F1 was about 0.98 with very small variance"*; that is safely true
> either way.

---

## 12. Where Everything Lives (if asked "show me")

| Path | Contents |
|---|---|
| `training/` | 3 training scripts + `generate_synthetic_data.py` |
| `orchestrator/` | FastAPI service, routers, `models/` artifacts |
| `collectors/` | Jenkins / Prometheus / realtime collectors |
| `autoscaler/` | `decision_engine.py` + `scaler.py` |
| `evaluation/` | `evaluate_all.py` → 12 plots + `metrics/all_metrics.json` |
| `tests/test_e2e.py` | the 13-test E2E suite |
| `kubernetes_manifests/`, `prometheus/` | deployment YAMLs, Prom configs |
| `demo-todo-app/` | CI/CD target app (Next.js + Jenkinsfile + Docker) |
| `Journal Paper*/`, `Conference Paper/` | Springer manuscript + conference version |
| `Presentation/AIOps_Final_Presentation.pptx` | the final deck (25 slides) |

---

## 13. Prep Sequence for the Defense

1. Read this document once for the story.
2. Skim `FINAL_PRESENTATION_SCRIPT.md` for what to say per slide (~15 min talk).
3. Drill `PANEL_QA_BANK.md` sections **E** (synthetic data), **J** (limitations), and
   **K** (rapid-fire) — those are where panels attack.

**Numbers to memorize:** XGBoost F1 0.982 / Recall 100% · Autoencoder F1 0.931 /
Recall 100% · LSTM RMSE 0.070 / MAPE 9.68% · 13/13 E2E tests.

**The single most important thing to internalize:** *the novelty is the integration,
not the algorithms* (Q43). Every hard question bends back to that answer.
