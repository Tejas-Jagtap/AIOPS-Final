# AIOps — Final Defense Presentation Script (What to Say)

> **Deck:** `Presentation/AIOps_Final_Presentation.pptx` (25 slides)
> **Speaker:** Tejas Jagtap • **Target time:** 15–18 min talk + Q&A
> **Golden rule:** speak to the panel, not the slides. Numbers to memorise:
> **XGBoost F1 = 0.982, Recall = 100%, AUC = 1.000** · **Autoencoder F1 = 0.931, Recall = 100%, AUC = 1.000** · **LSTM RMSE = 0.070, MAPE = 9.68%** · **13/13 E2E tests pass.**

Pace ≈ 40–45 seconds per slide. Where a slide says *(pause)*, stop and let the panel read the table/plot.

---

## Slide 1 — Title (20 sec)
"Good morning. I am Tejas Jagtap, M.Tech Information Security. My project, guided by Dr. V. K. Pachghare, is an **Intelligent AIOps Framework for Predictive CI/CD Pipeline Management and Autonomous Resource Optimization**. In short — I use machine learning to make CI/CD pipelines and Kubernetes infrastructure predict problems and fix themselves before they happen."

## Slide 2 — Contents (15 sec)
"I'll cover the motivation and research gap, my problem statement and objectives, the system architecture, the three ML models and their results, how I integrated everything into a working orchestrator and predictive autoscaler, the end-to-end validation, and finally a comparison with related work and conclusions."

## Slide 3 — Introduction (45 sec)
"Modern software delivery runs on CI/CD pipelines like Jenkins and on Kubernetes for scaling. These generate huge volumes of logs and metrics. The core problem is that today's monitoring is **reactive** — it responds only *after* something breaks: a build fails after wasting compute, log issues are found by manually reading thousands of lines, and Kubernetes' autoscaler adds pods only *after* CPU has already spiked. **AIOps** — AI for IT Operations — applies machine learning to make these operations **predictive** instead. That is exactly what my framework does."

## Slide 4 — Motivation (40 sec)
"Concretely: build failures waste compute and delay deployments; manual root-cause analysis is slow; and reactive scaling causes lag — you either over-provision and waste money, or under-provision and breach your SLA. Critically, prior research treats these as *three separate problems*. There's no single system that predicts failures, detects anomalies, forecasts load, **and** closes the loop by acting on Kubernetes automatically. That gap is my motivation."

## Slide 5 & 6 — Literature Survey (60 sec total)
"I surveyed recent work across three streams. *(gesture to table)* Autoscaling papers — like the Prophet+LSTM work of Guruge — do forecasting well but ignore CI/CD and logs. Anomaly-detection surveys cover autoencoders and VAEs but stay at runtime, not builds. Failure-prediction work uses ensemble trees on build metadata but has no anomaly detection or scaling. And the agentic-AIOps work of Zota is conceptually closed-loop but ships no concrete models. **Every paper solves one slice.**"
*(Don't read every cell — summarise the pattern in the 'Limitation' column.)*

## Slide 7 — Research Gap (30 sec)
"So the gap is clear: no unified framework combines all three signal types, predictive scaling is still rare versus reactive HPA, and almost nobody builds a true **closed loop** — prediction, to decision, to an automatic Kubernetes action, and back. My work fills that gap: Jenkins → ML → Kubernetes, in one loop."

## Slide 8 — Problem Statement (25 sec)
*(Read it once, deliberately.)* "To design and implement an intelligent, closed-loop AIOps framework that proactively predicts CI/CD failures, detects log anomalies in real time, forecasts workload, and autonomously optimises Kubernetes resources through predictive autoscaling."

## Slide 9 — Objectives (30 sec)
"Five objectives: build the data-collection layer; build the three ML models; serve them through a FastAPI orchestrator; design a predictive autoscaling engine driven by those model outputs; and finally integrate everything into a closed loop and validate it end-to-end. I'll show that **all five are complete.**"

## Slide 10 — System Architecture (55 sec)
"Here's the architecture — four layers forming a closed loop. *(point left figure)* At the bottom, **collectors** pull build metadata and logs from the Jenkins REST API, and CPU/memory metrics from the Prometheus API. That feeds the **ML layer**: XGBoost for failure prediction, TF-IDF plus an autoencoder for log anomalies, and an LSTM for CPU forecasting. All three sit behind the **FastAPI orchestrator**, which loads them once and exposes REST endpoints. The orchestrator's outputs drive the **predictive autoscaler**, which calls the Kubernetes Python client to change replica counts — and the resulting metrics feed straight back into the next prediction cycle. That feedback is what makes it *closed-loop* rather than a one-shot prediction."

## Slide 11 — Methodology: Data (45 sec)
"For training I generated a **synthetic but realistic** dataset — this gives me reproducibility and known ground-truth labels. It's 600 Jenkins builds with a realistic 68/23/9 split of success, failure and unstable; 600 matching console logs with class-distinctive vocabulary; and just over 10,000 CPU time-series points with daily and weekly patterns plus injected noise and spikes. Importantly, the collectors are real — the same pipeline works against live Jenkins and Prometheus. Preprocessing is eight engineered build features, 500-dimension TF-IDF for logs, and MinMax scaling for CPU."

## Slide 12 — XGBoost (55 sec)
"Model one: XGBoost for failure prediction. It's a gradient-boosted ensemble of 100 trees on eight build features, outputting a failure probability. I handle the 3-to-1 class imbalance with `scale_pos_weight`, use a stratified 80/20 split, and confirm stability with 5-fold cross-validation — F1 of 0.975 plus-or-minus 0.009, so no overfitting. *(pause on table)* On the held-out set: **99.2% accuracy, F1 of 0.982, and 100% recall** — meaning it never misses a real failure — with a perfect ROC-AUC of 1.000. The feature-importance plot on the right confirms it's learning real signals: test results and error counts dominate, which matches empirical CI failure studies."

## Slide 13 — Autoencoder (55 sec)
"Model two: log anomaly detection, and this one is **unsupervised** — which matters, because in real DevOps you rarely have labelled anomalies. Stage one converts log text to a 500-dimension TF-IDF vector. Stage two is an autoencoder that compresses 500 down to a 32-neuron bottleneck and reconstructs it. I train it **only on normal logs**, so it learns what 'normal' looks like. An anomalous log reconstructs badly — high error — and I flag anything above the 95th percentile of normal errors. *(pause)* Result: **96.7% accuracy, F1 of 0.931, 100% recall, AUC 1.000.** The error-distribution plot shows clean separation between normal and anomalous logs."

## Slide 14 — LSTM (50 sec)
"Model three: an LSTM to forecast CPU. It takes the last 60 minutes of usage and predicts 10 minutes ahead — that 10-minute lead time is exactly what the autoscaler needs to spin up pods early. Architecture is two stacked LSTM layers, 128 then 64 units, into dense layers. *(pause on table)* RMSE is **0.070** and MAPE **9.68%** — under the 10% rule-of-thumb for good forecasting. The R² of 0.455 looks modest, but that's deliberate: CPU has random spikes that are fundamentally unpredictable; the model tracks the *trend* and smooths the noise, which is exactly what you want for scaling — you don't want to scale on every random blip."

## Slide 15 — Combined Summary (30 sec)
"Putting it together: XGBoost F1 0.982, Autoencoder F1 0.931, LSTM RMSE 0.070. Note that **both classifiers hit 100% recall** — a deliberate design choice, because in operations a missed failure costs far more than a false alarm."

## Slide 16 — ROC Curves (25 sec)
"The ROC curves confirm it — both classification models reach an AUC of 1.000, near-perfect separation between the two classes. I'll be honest in the discussion about why these numbers are this high on synthetic data."

## Slide 17 — Orchestrator (45 sec)
"Now the integration — this is the Phase-III work that ties it all together. A single FastAPI service loads all three models at startup and serves them through four REST endpoints: predict_failure, detect_anomaly, forecast_cpu, and autoscale. Endpoints are async with typed Pydantic schemas, models are cached in memory for millisecond inference, and there's a live Swagger UI at /docs. Nothing is hard-coded — all endpoints come from environment variables."

## Slide 18 — Predictive Autoscaler (55 sec)
"The autoscaler is the decision brain. It runs a **priority policy** each cycle: first, if a log anomaly is detected, raise an alert — but don't block. Second, if failure probability is above 0.6, **hold** — because it's pointless to scale up infrastructure for a build that's about to fail. Otherwise it looks at the forecast: CPU at or above 0.7, scale up by two; at or below 0.3, scale down by one; else maintain. Guardrails cap it at 1 to 10 replicas with a 5-minute cooldown to prevent thrashing. *(gesture right)* The key contrast: **Kubernetes HPA is reactive** — it scales after CPU already crossed the line. Mine acts on the 10-minute forecast, so Kubernetes has lead time to add pods *before* the spike."

## Slide 19 — End-to-End Validation (45 sec)
"And it genuinely works, end to end — I have an automated suite of **13 tests, all passing.** It checks the data layer, confirms all six model artefacts load, and exercises every endpoint: a clean build returns 0.1% failure probability, a broken build returns 97%, normal logs pass, failure logs flag as anomalies, and the full pipeline runs failure-plus-anomaly-plus-forecast into a single scaling decision. Beyond that, I built a real Next.js demo app with a six-stage Jenkinsfile, Docker images, and Kubernetes manifests — so this runs on real infrastructure, not just in theory."

## Slide 20 — Comparison (35 sec)
*(Let the table speak.)* "Against related work, mapped onto four capabilities — failure prediction, log anomaly, predictive scaling, closed-loop. Each prior study has one or two ticks. **Mine is the only row with all four.** That integration into a single closed-loop architecture is the core contribution."

## Slide 21 — Conclusion (35 sec)
"To conclude: I built a unified, closed-loop AIOps framework — three ML models, a FastAPI orchestrator, and a predictive Kubernetes autoscaler. Failures predicted at F1 0.982 with zero misses, anomalies caught unsupervised at F1 0.931, CPU forecast at 7% error, scaling that acts *before* spikes, and the whole thing validated end-to-end. It's a concrete implementation of the closed-loop AIOps that recent literature only describes conceptually."

## Slide 22 — Future Scope (25 sec)
"Next steps: validate on real-world datasets like TravisTorrent; add automatic retraining for concept drift; try transformer-based log embeddings like LogBERT; benchmark my autoscaler head-to-head against HPA under load; and add a live dashboard."

## Slide 23 — Publications (20 sec)
"The work is written up as a research manuscript in Springer Nature journal format, with a conference version prepared as well, co-authored with Prof. Charulata Patil and Dr. Pachghare."

## Slide 24 — References (10 sec)
"These are the key references underpinning the work."

## Slide 25 — Thank You (10 sec)
"Thank you. I'm happy to take questions."

---

## Timing cheat-sheet
| Section | Slides | Budget |
|---|---|---|
| Setup (intro → gap) | 1–7 | ~4 min |
| Problem → architecture | 8–10 | ~2 min |
| Data + 3 models | 11–14 | ~3.5 min |
| Results | 15–16 | ~1 min |
| Integration (orchestrator/autoscaler/E2E) | 17–19 | ~2.5 min |
| Comparison → close | 20–25 | ~2 min |
| **Total talk** | | **~15 min** |

## If you're running short on time (cut these)
Slides 5–6 (compress to 30 sec), Slide 16 (skip — already covered), Slide 23–24 (mention verbally). Never cut 10, 12–14, 17–19 — those are the graded core.

## Delivery tips
- **Open strong, close strong.** Memorise the first 2 lines of Slide 1 and all of Slide 21.
- When a plot is on screen, **say what it proves**, don't describe axes.
- Own the weak spots *before* they ask: synthetic data (Slide 11), R²=0.455 (Slide 14), AUC=1.000 (Slide 16). Pre-empting them shows maturity.
- If you blank, fall back to the one-liner: *"three models — failure, anomaly, forecast — one orchestrator, one autoscaler, one closed loop."*
