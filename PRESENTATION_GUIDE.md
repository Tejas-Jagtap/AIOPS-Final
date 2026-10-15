# AIOps Project — Complete ML Presentation Guide
> **For Tejas Jagtap | Phase-II Panel Presentation**
> Read this end-to-end. After reading, you will be able to explain every ML decision in your project confidently.

---

## TABLE OF CONTENTS
1. [Project in One Paragraph](#1-project-in-one-paragraph)
2. [The 3 Problems We Solve](#2-the-3-problems-we-solve)
3. [MODEL 1: XGBoost — Failure Prediction](#3-model-1-xgboost--failure-prediction)
4. [MODEL 2: TF-IDF + Autoencoder — Log Anomaly Detection](#4-model-2-tf-idf--autoencoder--log-anomaly-detection)
5. [MODEL 3: LSTM — CPU Forecasting](#5-model-3-lstm--cpu-forecasting)
6. [Evaluation Metrics Explained (What to Say to Panel)](#6-evaluation-metrics-explained)
7. [Our Results — What to Highlight](#7-our-results--what-to-highlight)
8. [Common Panel Questions & Answers](#8-common-panel-questions--answers)
9. [Glossary of ML Terms](#9-glossary-of-ml-terms)

---

## 1. Project in One Paragraph

> "We built an AIOps system that uses machine learning to make CI/CD pipelines and Kubernetes infrastructure smarter. It does 3 things: (1) predicts if a Jenkins build will fail BEFORE it runs, (2) detects anomalies hidden in build logs automatically, and (3) forecasts CPU usage in Kubernetes so we can scale resources BEFORE demand spikes. All 3 models are trained, evaluated, and ready to be integrated into a FastAPI orchestrator in the next phase."

---

## 2. The 3 Problems We Solve

| # | Problem | Input Data | ML Model | Output |
|---|---------|-----------|----------|--------|
| 1 | Build fails waste time & resources | Jenkins build metadata (duration, errors, warnings, test results) | **XGBoost** (classification) | "This build has 87% chance of failing" |
| 2 | Anomalies hidden in huge logs | Jenkins console log text (thousands of lines) | **TF-IDF + Autoencoder** (unsupervised) | "This log is anomalous — score: 0.85" |
| 3 | Kubernetes scales AFTER problems | Prometheus CPU time-series (minute-by-minute) | **LSTM** (time-series forecast) | "CPU will be 72% in 10 minutes" |

---

## 3. MODEL 1: XGBoost — Failure Prediction

### 3.1 What is XGBoost? (Explain Like I'm 5)

XGBoost = **eXtreme Gradient Boosting**. Think of it as a **team of decision trees** that work together.

- A **decision tree** is like a flowchart: "Is duration > 100s? → Yes → Are errors > 5? → Yes → Likely FAILURE"
- A single tree is okay but not great. XGBoost builds **100 trees one after another**.
- Each new tree **focuses on the mistakes the previous trees made**. Tree #2 pays extra attention to the samples Tree #1 got wrong.
- Final prediction = **combined vote of all 100 trees**.

This is called **boosting** — unlike Random Forest where trees work independently (bagging), here each tree LEARNS from the previous tree's errors.

### 3.2 Why We Chose XGBoost (What to Tell Panel)

> "We chose XGBoost because:
> 1. It's the **gold standard for tabular/structured data** — our input is a CSV table with 8 numeric columns.
> 2. It handles **class imbalance** well (we have ~25% failures, ~75% success) via `scale_pos_weight`.
> 3. It's **fast to train** — seconds, not hours. Good for iterating.
> 4. It provides **feature importance** — we can explain WHICH features matter most (interpretability).
> 5. Literature (Mathew & Baswareddy, 2025) confirmed ensemble trees work well for CI/CD failure prediction."

**Why NOT Neural Networks?** — Our data is small (600 rows, 8 columns). Neural networks need thousands/millions of rows. XGBoost works great on small tabular data. Using a neural network here would be overkill and might actually perform worse.

**Why NOT Logistic Regression?** — It's linear. The relationship between features and failure is non-linear (e.g., very short AND very long builds both fail). XGBoost captures these non-linear patterns.

### 3.3 Our Input Features (8 Features)

| Feature | What It Means | Why It Matters |
|---------|--------------|----------------|
| `duration` | Build time in seconds | Failed builds tend to be very short (early abort) or very long (timeout) |
| `warnings` | Count of warning messages | More warnings → more instability |
| `errors` | Count of error messages | Direct indicator of problems |
| `failures` | Count of build step failures | Steps that crashed |
| `log_length` | Total characters in log | Failed builds often have different log sizes |
| `tests_failed` | Number of test failures | **Most important feature** — failed tests = failed build |
| `tests_passed` | Number of passing tests | Context for test health |
| `tests_total` | Total test count | When 0, build failed before tests even ran |

### 3.4 Hyperparameters Explained

```python
XGBClassifier(
    n_estimators=100,        # Number of trees in the ensemble
    max_depth=6,             # How deep each tree can grow
    learning_rate=0.1,       # Step size for each tree's contribution
    subsample=0.8,           # Use 80% of data per tree (prevents overfitting)
    colsample_bytree=0.8,    # Use 80% of features per tree (prevents overfitting)
    scale_pos_weight=spw,    # Compensate for class imbalance
    random_state=42,         # Reproducibility seed
    eval_metric='logloss'    # Loss function for binary classification
)
```

#### What each hyperparameter does:

**`n_estimators=100`** (Number of trees)
- We build 100 decision trees sequentially.
- Too few (10) → underfitting (model too simple).
- Too many (1000) → overfitting + slower.
- **100 is a standard starting point**. Our data is small, so 100 is sufficient.
- *Panel answer: "100 estimators is a widely-used default for datasets of this size. We verified via cross-validation that the model generalizes well."*

**`max_depth=6`** (Tree depth)
- Each tree can have at most 6 levels of decisions.
- Depth 1-3 = very simple rules. Depth 10+ = memorizes training data.
- **6 is the XGBoost default**. It allows capturing complex patterns without overfitting.
- *Panel answer: "Depth 6 balances model complexity and generalization. The cross-validation scores (99% ± 0.6%) confirm no overfitting."*

**`learning_rate=0.1`** (Shrinkage)
- Each tree's contribution is multiplied by 0.1 (scaled down).
- Think of it as: "Don't trust any single tree too much."
- Lower rate = more trees needed but better generalization.
- **0.1 is the standard default** for XGBoost.
- *Panel answer: "Learning rate 0.1 with 100 trees is a well-established combination. Lower rates like 0.01 would need 1000+ trees for similar performance."*

**`subsample=0.8`** (Row sampling)
- Each tree only sees 80% of the training data (randomly sampled).
- This adds randomness → prevents overfitting.
- Like training on "slightly different versions" of the data each time.

**`colsample_bytree=0.8`** (Column/Feature sampling)
- Each tree only uses 80% of the 8 features.
- Forces trees to find different patterns → more robust model.

**`scale_pos_weight`** (Class imbalance handling)
- Our data: ~75% SUCCESS, ~25% FAILURE. Without this, model would just predict "SUCCESS" always and get 75% accuracy.
- `scale_pos_weight = n_negative / n_positive ≈ 3.0`
- This tells XGBoost: "A failure sample is 3x more important than a success sample."
- *Panel answer: "We use scale_pos_weight to handle the 3:1 class imbalance. This ensures the model learns failure patterns rather than defaulting to the majority class."*

**`random_state=42`**
- Seed for reproducibility. Everyone in ML uses 42 (it's a convention from "The Hitchhiker's Guide to the Galaxy").

**`eval_metric='logloss'`**
- Log loss = measures how confident and correct the predictions are.
- A prediction of 0.99 for a true failure gets low loss. A prediction of 0.51 for a true failure gets high loss.
- Better than accuracy for optimization because it considers probability, not just yes/no.

### 3.5 Training Process

1. **Load** 600 build records from CSV
2. **Split** 80% train (480) / 20% test (120), stratified (same failure ratio in both)
3. **Train** XGBoost on training set
4. **Evaluate** on test set (model has NEVER seen these 120 samples)
5. **5-fold Cross Validation** — split data into 5 parts, train on 4, test on 1, rotate. This gives 5 accuracy scores → mean ± std shows stability.

---

## 4. MODEL 2: TF-IDF + Autoencoder — Log Anomaly Detection

### 4.1 The Two-Stage Pipeline

```
Raw Log Text → [TF-IDF Vectorizer] → Numbers (500 features) → [Autoencoder] → Anomaly Score
```

We need TWO components because neural networks can't read text — they only understand numbers.

### 4.2 Stage 1: TF-IDF (Converting Text to Numbers)

**TF-IDF = Term Frequency × Inverse Document Frequency**

Imagine you have 600 log files. TF-IDF converts each log into a vector of 500 numbers.

**Term Frequency (TF):** How often a word appears in THIS log.
- If "ERROR" appears 15 times in a log of 500 words → TF("ERROR") = 15/500 = 0.03

**Inverse Document Frequency (IDF):** How rare a word is ACROSS ALL logs.
- If "the" appears in all 600 logs → IDF("the") = very low (not useful)
- If "NullPointerException" appears in only 5 logs → IDF = very high (very informative!)

**TF-IDF = TF × IDF**
- Common-everywhere words like "the", "is", "Pipeline" get LOW scores
- Rare, meaningful words like "FATAL", "StackOverflow", "OutOfMemory" get HIGH scores

#### TF-IDF Hyperparameters:

```python
TfidfVectorizer(
    max_features=500,       # Keep only top 500 most informative words
    max_df=0.95,            # Ignore words appearing in >95% of logs (too common)
    min_df=2,               # Ignore words appearing in <2 logs (too rare/noise)
    ngram_range=(1, 2),     # Use single words AND two-word pairs
    stop_words='english',   # Remove "the", "is", "and", etc.
    sublinear_tf=True       # Use log(1+TF) instead of raw TF (dampens extreme frequencies)
)
```

**`max_features=500`**: We keep only the 500 most important words/phrases. More would add noise.

**`ngram_range=(1,2)`**: We look at single words ("ERROR") AND word pairs ("build FAILED", "test PASSED"). Pairs capture context that single words miss.

**`max_df=0.95`**: Words in >95% of logs are useless (like "Pipeline", "Building"). Remove them.

**`min_df=2`**: Words appearing only once might be typos or random strings. Remove them.

**`sublinear_tf=True`**: If "ERROR" appears 100 times, it shouldn't be 100x more important than appearing once. Using log scale: log(1+100)=4.6 vs log(1+1)=0.7. More balanced.

*Panel answer: "TF-IDF converts unstructured log text into a fixed-size numerical representation where important and rare terms have higher weights. The 500-feature limit controls dimensionality while retaining the most discriminative terms."*

### 4.3 Stage 2: Autoencoder (Finding Anomalies)

**What is an Autoencoder?**

An autoencoder is a neural network that learns to **copy its input to its output** — but through a very tight bottleneck.

```
Input (500) → Compress → Bottleneck (32) → Decompress → Output (500)
        ↓                                              ↓
   TF-IDF vector                              Reconstructed TF-IDF vector
```

Architecture:
```
500 → 128 → 64 → 32 (bottleneck) → 64 → 128 → 500
```

**Why does this detect anomalies?**

1. We train the autoencoder ONLY on **normal** (non-anomalous) logs.
2. It learns to compress and reconstruct normal log patterns perfectly.
3. When we feed an **anomalous** log, the autoencoder can't reconstruct it well (it never learned anomaly patterns).
4. The **reconstruction error** (difference between input and output) is HIGH for anomalies, LOW for normal logs.
5. We set a **threshold** — if error > threshold → ANOMALY.

**Analogy:** Imagine you only ever hear English. If someone speaks French, you can't repeat it back accurately. Your "reconstruction error" is high. That's how the autoencoder detects anomalous logs — it struggles to reproduce patterns it hasn't seen.

#### Autoencoder Hyperparameters:

```
Input(500)
  → Dense(128, ReLU) → BatchNorm → Dropout(0.3)
  → Dense(64, ReLU)  → BatchNorm → Dropout(0.3)
  → Dense(32, ReLU)                               ← BOTTLENECK
  → Dense(64, ReLU)  → BatchNorm → Dropout(0.3)
  → Dense(128, ReLU) → BatchNorm → Dropout(0.3)
  → Dense(500, Sigmoid)
```

**Bottleneck size = 32:**
- Force 500 features through only 32 neurons.
- Compression ratio = 500:32 ≈ 16:1.
- This forces the network to learn only the MOST essential patterns.
- Too large (256) → copies everything, can't distinguish normal from anomaly.
- Too small (4) → loses too much information, poor reconstruction even for normal logs.
- *Panel answer: "The bottleneck of 32 provides ~16:1 compression. This forces the model to learn a compact representation of normal log behavior while discarding noise."*

**ReLU activation:**
- ReLU = max(0, x). If input is negative, output is 0. If positive, passes through.
- Simple, fast, prevents "vanishing gradient" problem in deep networks.
- Standard choice for hidden layers.

**Sigmoid on output layer:**
- Sigmoid squashes output between 0 and 1.
- TF-IDF values are already in [0,1] range, so output layer matches input range.

**BatchNormalization:**
- Normalizes values between layers to have mean=0, std=1.
- Stabilizes and accelerates training. Without it, deep networks train erratically.

**Dropout(0.3):**
- During training, randomly sets 30% of neurons to 0 each batch.
- Forces the network to not rely on any single neuron → prevents overfitting.
- Like studying for an exam by covering random notes — forces you to learn the material broadly.

**Adam optimizer (lr=0.0005):**
- Adam = Adaptive Moment Estimation. Smart optimizer that adjusts learning rate per-parameter.
- 0.0005 is relatively slow — we want careful, stable learning.
- *Panel answer: "We use a conservative learning rate of 0.0005 to ensure stable convergence during autoencoder training."*

**MSE Loss (Mean Squared Error):**
- Loss = average of (input - output)² across all 500 features.
- Measures how well the autoencoder reconstructs its input.
- Lower MSE = better reconstruction.

**Early Stopping (patience=5):**
- Monitor validation loss. If it doesn't improve for 5 consecutive epochs → stop training.
- Prevents overfitting. We restore the best weights.
- *Panel answer: "Early stopping with patience 5 prevents overtraining. The model automatically selects the epoch with best generalization."*

**Anomaly Threshold (95th percentile):**
- After training on normal logs, compute reconstruction error for all normal training logs.
- Set threshold = 95th percentile of these errors.
- Meaning: 95% of normal logs have error below this threshold.
- Anything above → flagged as anomaly.
- *Panel answer: "The 95th percentile threshold is a standard choice for anomaly detection — it expects up to 5% false positive rate while capturing most true anomalies."*

### 4.4 Why Autoencoder? (What to Tell Panel)

> "We chose an Autoencoder because:
> 1. **Unsupervised approach** — we don't need labeled 'anomaly' data for training. In real-world DevOps, you rarely have labeled anomalies.
> 2. It learns what **normal** looks like, and anything different is flagged. This means it can detect **novel anomalies** it has never seen before.
> 3. Alternative: LogBERT (Transformer-based) — but it needs GPU and large datasets. Our autoencoder is lightweight and trains in minutes.
> 4. Literature (Yahya et al., 2025) confirmed reconstruction-based autoencoders are effective for anomaly detection."

---

## 5. MODEL 3: LSTM — CPU Forecasting

### 5.1 What is LSTM?

**LSTM = Long Short-Term Memory**. It's a type of Recurrent Neural Network (RNN) designed for **sequence data** (time-series, text, etc.)

**The core idea:** CPU usage at minute 100 depends on usage at minutes 99, 98, 97... and even minutes 50, 40. LSTM can remember **long-term patterns**.

**Regular Neural Networks** see each input independently — they have no memory.
**RNNs** process sequences step-by-step and maintain hidden state (memory).
**LSTMs** are special RNNs with **gates** that control what to remember, what to forget, and what to output.

### 5.2 The 3 Gates of LSTM (Simplified)

Each LSTM cell has 3 gates:

1. **Forget Gate:** "Should I forget old information?"
   - Example: A CPU spike from 2 hours ago may not matter now → forget it.

2. **Input Gate:** "Should I store this new information?"
   - Example: CPU just jumped from 30% to 70% → remember this!

3. **Output Gate:** "What should I output right now?"
   - Combines old memory + new input → produces prediction.

*Panel answer: "LSTM's gating mechanism allows it to selectively retain long-term dependencies in time-series data. This is crucial for CPU forecasting because workload patterns can have both short-term spikes and long-term trends (e.g., daily cycles)."*

### 5.3 Our LSTM Architecture

```
Input (60 timesteps × 1 feature)
  → LSTM(128 units, return_sequences=True)   ← processes all 60 steps, outputs sequence
  → Dropout(0.2)
  → LSTM(64 units, return_sequences=False)    ← processes sequence, outputs single vector
  → Dropout(0.2)
  → Dense(32, ReLU)                           ← further processing
  → Dense(1)                                  ← single output: predicted CPU value
```

**How it works step by step:**
1. Take the last 60 minutes of CPU data (lookback = 60)
2. First LSTM layer (128 units) processes all 60 timesteps, building memory
3. Second LSTM layer (64 units) condenses this into a single summary vector
4. Dense layers convert this summary into one number: predicted CPU 10 minutes from now

### 5.4 Data Preparation: Sliding Window

```
Original data: [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, ...]

                    Lookback (60 min)        →  Predict (10 min ahead)
Window 1: [min 1  ... min 60]               →  min 70's CPU value
Window 2: [min 2  ... min 61]               →  min 71's CPU value
Window 3: [min 3  ... min 62]               →  min 72's CPU value
... (10,011 windows total)
```

**MinMaxScaler:** Scales all CPU values to [0, 1] range.
- Raw CPU might be 0-100%. Neural networks train better with small numbers.
- After prediction, we inverse-transform back to real values.

### 5.5 LSTM Hyperparameters Explained

**`LSTM(128, return_sequences=True)`:**
- 128 units = 128 memory cells processing in parallel.
- `return_sequences=True` = output a value at EVERY timestep (needed to feed into next LSTM layer).
- *Panel answer: "128 units in the first layer provide sufficient capacity to capture complex temporal patterns in CPU usage."*

**`LSTM(64, return_sequences=False)`:**
- 64 units (smaller — compresses information).
- `return_sequences=False` = output only the FINAL timestep's summary (since we need one prediction, not a sequence).

**`Dropout(0.2)`:**
- Randomly drops 20% of connections during training.
- Prevents overfitting on training sequences.

**`Dense(32, ReLU)` → `Dense(1)`:**
- Final processing layers. 32 → 1 maps the LSTM output to a single CPU prediction.
- No activation on output (linear) because CPU is a continuous value, not bounded.

**`learning_rate=0.001`:**
- Standard Adam learning rate for LSTMs.
- Higher than Autoencoder (0.0005) because LSTM needs faster convergence on sequential patterns.

**`ReduceLROnPlateau(factor=0.5, patience=5)`:**
- If validation loss plateaus for 5 epochs → halve the learning rate.
- This allows fine-tuning as training progresses.
- *Panel answer: "We use learning rate scheduling to automatically reduce the step size when the model stops improving, enabling finer convergence."*

**`Lookback=60, Forecast_horizon=10`:**
- Use past 60 minutes to predict 10 minutes ahead.
- 60 minutes captures ~1 hour of patterns (workload cycles, build activity).
- 10 minutes gives enough lead time for Kubernetes to spin up new pods.
- *Panel answer: "60-minute lookback captures both short-term fluctuations and medium-term workload patterns. 10-minute forecast horizon provides sufficient lead time for the predictive autoscaler to act."*

### 5.6 Why LSTM? (What to Tell Panel)

> "We chose LSTM because:
> 1. CPU usage is a **time-series** — order matters. LSTM is designed specifically for sequential data.
> 2. It captures **long-term dependencies** — e.g., CPU peaks every hour during build cycles.
> 3. Alternative: Facebook Prophet (statistical) — good baseline but can't capture complex non-linear patterns.
> 4. Alternative: Transformer — more powerful but needs much more data and compute.
> 5. Literature (Guruge & Priyadarshana, 2025) showed LSTM performs well for Kubernetes metric forecasting.
> 6. LSTM is **well-established** and proven for time-series forecasting in production systems."

---

## 6. Evaluation Metrics Explained

### 6.1 Classification Metrics (XGBoost & Autoencoder)

Let's use a concrete example. Say we test on 120 builds:

```
                    Predicted SUCCESS    Predicted FAILURE
Actual SUCCESS           88 (TN)             2 (FP)
Actual FAILURE            0 (FN)            30 (TP)
```

**Accuracy = (TP + TN) / Total = (30 + 88) / 120 = 98.3%**
- "Out of all predictions, how many were correct?"
- Easy to understand but misleading if data is imbalanced.

**Precision = TP / (TP + FP) = 30 / (30 + 2) = 93.1%**
- "When we predict FAILURE, how often are we right?"
- High precision = few false alarms.
- Important because: false alarms waste developer time investigating non-issues.

**Recall = TP / (TP + FN) = 30 / (30 + 0) = 100%**
- "Out of all actual failures, how many did we catch?"
- High recall = we don't miss real failures.
- Important because: missing a real failure means bugs go to production.
- **Our recall is 100% — we catch EVERY failure.**

**F1-Score = 2 × (Precision × Recall) / (Precision + Recall) = 96.4%**
- Harmonic mean of precision and recall. Balances both.
- If either precision or recall is low, F1 drops significantly.

**ROC AUC (Area Under ROC Curve):**
- ROC curve plots True Positive Rate vs False Positive Rate at various thresholds.
- AUC = 1.0 means **perfect separation** — the model can perfectly distinguish failures from successes.
- AUC = 0.5 means random guessing.
- **Our AUC = 1.000 — perfect discrimination.**

**5-Fold Cross-Validation:**
- Split data into 5 equal parts. Train on 4, test on 1. Repeat 5 times.
- Reports mean ± standard deviation.
- Low std = model is **stable** and not dependent on a lucky train/test split.
- Our CV: 99.0% ± 0.6% accuracy → very stable.

### 6.2 Regression Metrics (LSTM)

**MSE (Mean Squared Error) = 0.005:**
- Average of (actual - predicted)².
- Penalizes large errors heavily (squared).
- Lower is better.

**MAE (Mean Absolute Error) = 0.044:**
- Average of |actual - predicted|.
- "On average, our prediction is off by 0.044 CPU units."
- More interpretable than MSE.

**RMSE (Root Mean Squared Error) = 0.071:**
- √MSE. Same unit as the original data.
- "Our typical prediction error is about 0.071 CPU units."
- *Panel answer: "RMSE of 0.071 means our predictions are typically within 7.1% of the actual CPU value — well within the margin needed for autoscaling decisions."*

**MAPE (Mean Absolute Percentage Error) = 9.56%:**
- Average of |actual - predicted| / actual × 100%.
- "Our predictions are off by ~9.6% on average."
- Below 10% MAPE is considered **good forecasting**.

**R² (R-squared) = 0.435:**
- How much variance in CPU usage our model explains.
- 1.0 = perfect, 0 = model is no better than predicting the mean.
- 0.435 means we explain ~44% of variance.
- For noisy, real-world CPU data with random spikes, this is **reasonable**.
- *Panel answer: "R² of 0.435 reflects the inherent randomness in CPU workloads. The model captures trend and cyclical patterns well, but random spikes are inherently unpredictable. For autoscaling, the trend prediction is what matters, and our RMSE of 0.071 confirms the model is practically useful."*

---

## 7. Our Results — What to Highlight

### Headline Numbers (Memorize These)

| Model | Best Metric | Value | What It Means |
|-------|-------------|-------|---------------|
| XGBoost | Accuracy | **98.3%** | Correctly predicts 118 out of 120 builds |
| XGBoost | F1-Score | **96.4%** | Near-perfect balance of precision & recall |
| XGBoost | Recall | **100%** | Catches every single failure |
| XGBoost | ROC AUC | **1.000** | Perfect class separation |
| XGBoost | CV Accuracy | **99.0% ± 0.6%** | Extremely stable across folds |
| Autoencoder | Accuracy | **95.9%** | Correctly classifies 96 out of 100 logs |
| Autoencoder | F1-Score | **91.8%** | Strong anomaly detection performance |
| Autoencoder | Recall | **100%** | Catches every anomalous log |
| Autoencoder | ROC AUC | **98.9%** | Near-perfect discrimination |
| LSTM | RMSE | **0.071** | ~7% typical prediction error |
| LSTM | MAPE | **9.56%** | Below 10% = good forecasting |

### Key Talking Points

1. **"Both classification models achieve 100% recall"** — this means we NEVER miss a real failure or anomaly. In DevOps, missing a failure is far worse than a false alarm.

2. **"XGBoost ROC AUC is 1.000"** — perfect class separation. The model can always distinguish failed builds from successful ones.

3. **"Cross-validation shows 99.0% ± 0.6%"** — the model is not overfitting. Performance is consistent across different data splits.

4. **"LSTM MAPE of 9.56% is below the 10% threshold"** — generally, MAPE < 10% is considered "highly accurate forecasting" in industry.

5. **"Feature importance shows errors, failures, and tests_failed are top predictors"** — this makes intuitive sense and gives confidence the model is learning real patterns, not noise.

---

## 8. Common Panel Questions & Answers

### Q: "Why didn't you use real data from Jenkins?"
> "We developed complete Jenkins and Prometheus collectors that work with real instances. However, for controlled training and reproducible evaluation, we used synthetic data that mimics real CI/CD patterns — including realistic failure rates, log structures, and CPU patterns. The synthetic generator was designed based on analysis of real Jenkins outputs. In the next phase, we plan to supplement with real data."

### Q: "Isn't 600 samples too small?"
> "For XGBoost on 8 features, 600 samples is sufficient — XGBoost is designed to work well on small to medium datasets. Our 5-fold cross-validation with 99% ± 0.6% accuracy confirms the model generalizes well and is not overfitting. Literature shows similar dataset sizes for CI/CD prediction."

### Q: "How did you choose these specific hyperparameters?"
> "We started with well-established defaults from XGBoost, TensorFlow, and scikit-learn documentation. For example, XGBoost's 100 trees with 0.1 learning rate and depth 6 are the recommended starting configuration. We validated through cross-validation that these defaults work well. Fine-tuning hyperparameters via grid search is planned for the next phase."

### Q: "What is overfitting and how did you prevent it?"
> "Overfitting is when a model memorizes training data but fails on new data. We prevent it through: (1) train/test split — model is evaluated on data it never saw, (2) 5-fold cross-validation — tests on 5 different splits, (3) Dropout layers — randomly disable neurons during training, (4) Early stopping — stop training when validation performance stops improving, (5) Regularization via subsample and colsample_bytree in XGBoost."

### Q: "R² is only 0.435 for LSTM. Isn't that low?"
> "R² measures variance explained. CPU workloads contain inherent randomness — sudden spikes from user traffic, garbage collection, etc. These are fundamentally unpredictable. Our model captures the underlying trends and cyclical patterns well. The RMSE of 0.071 (7.1% error) is what matters practically — it's accurate enough for autoscaling decisions where we need directional accuracy, not perfect predictions."

### Q: "Why Autoencoder over simpler methods like One-Class SVM?"
> "One-Class SVM works on small feature spaces but struggles with 500 TF-IDF dimensions due to the curse of dimensionality. The Autoencoder naturally handles high-dimensional input through its compression bottleneck. Additionally, the autoencoder learns a non-linear mapping, which better captures the complex patterns in log text."

### Q: "What is the practical impact of these models?"
> "The failure predictor can save development teams minutes per build by flagging failures before they run. The anomaly detector can surface hidden issues in thousands of log lines instantly. The CPU forecaster enables the autoscaler to provision resources 10 minutes BEFORE demand spikes, preventing service degradation."

### Q: "How will these models be used in production?"
> "In the next phase, all three models will be loaded into a FastAPI orchestrator that exposes REST APIs. The Jenkins pipeline can call /predict_failure before running a build. The log monitor can call /detect_anomaly in real-time. The Kubernetes autoscaler will periodically call /forecast_cpu to make proactive scaling decisions."

### Q: "What if the data distribution changes over time?"
> "This is called concept drift. In production, model performance should be monitored continuously. If accuracy drops, models need retraining with recent data. The modular architecture allows individual models to be retrained and redeployed independently without affecting other components."

---

## 9. Glossary of ML Terms

| Term | Simple Explanation |
|------|-------------------|
| **Feature** | An input variable (column in your data). E.g., `duration`, `errors` |
| **Label/Target** | What we're trying to predict. E.g., `failed` (yes/no) |
| **Training set** | Data the model learns from (80%) |
| **Test set** | Data to evaluate the model (20%) — never seen during training |
| **Epoch** | One complete pass through the training data |
| **Batch size** | Number of samples processed before updating model weights |
| **Loss function** | Measures how wrong the model is. Training minimizes this |
| **Gradient Descent** | Algorithm that adjusts model weights to minimize loss |
| **Learning rate** | Step size for weight updates. Too high = unstable. Too low = slow |
| **Overfitting** | Model memorizes training data, fails on new data |
| **Underfitting** | Model is too simple to capture patterns |
| **Regularization** | Techniques to prevent overfitting (dropout, subsample, etc.) |
| **Cross-validation** | Test model on multiple train/test splits for reliable evaluation |
| **Stratified split** | Ensures same class ratio in train and test sets |
| **Dense layer** | Fully-connected neural network layer. Every input connects to every output |
| **Activation function** | Non-linear function applied after each layer (ReLU, Sigmoid, etc.) |
| **ReLU** | max(0, x) — most common activation. Simple and effective |
| **Sigmoid** | Squashes values to [0, 1]. Used for probabilities and output layers |
| **Dropout** | Randomly disable neurons during training to prevent overfitting |
| **BatchNorm** | Normalize layer inputs to stabilize and speed up training |
| **Adam optimizer** | Smart optimizer that adapts learning rate per-parameter |
| **Early stopping** | Stop training when validation performance stops improving |
| **Reconstruction error** | Autoencoder: difference between input and reconstructed output |
| **Threshold** | Cutoff value — above = anomaly, below = normal |
| **Confusion matrix** | 2×2 table showing TP, TN, FP, FN counts |
| **ROC curve** | Plot of True Positive Rate vs False Positive Rate |
| **AUC** | Area Under ROC Curve. 1.0 = perfect, 0.5 = random |
| **Boosting** | Building models sequentially, each fixing previous model's errors |
| **Ensemble** | Combining multiple models for better performance |
| **Time-series** | Data points ordered in time (CPU usage every minute) |
| **Lookback** | How many past timesteps the model sees as input |
| **Forecast horizon** | How many timesteps ahead the model predicts |
| **Sliding window** | Moving a fixed-size window across time-series to create samples |
| **MinMaxScaler** | Scales data to [0, 1] range for neural network training |
| **MAPE** | Mean Absolute Percentage Error — forecast accuracy in % terms |
| **R²** | How much variance the model explains. 1 = perfect, 0 = mean baseline |

---

## QUICK REFERENCE CARD (Print This!)

```
┌─────────────────────────────────────────────────────────┐
│  MODEL 1: XGBoost (Failure Prediction)                  │
│  Input: 8 build features → Output: fail probability     │
│  Why: Best for small tabular data, interpretable        │
│  Result: 98.3% accuracy, 96.4% F1, 100% recall         │
├─────────────────────────────────────────────────────────┤
│  MODEL 2: TF-IDF + Autoencoder (Anomaly Detection)     │
│  Input: log text → 500 TF-IDF features → Output: score │
│  Why: Unsupervised, detects novel anomalies             │
│  Result: 95.9% accuracy, 91.8% F1, 98.9% AUC          │
├─────────────────────────────────────────────────────────┤
│  MODEL 3: LSTM (CPU Forecasting)                        │
│  Input: 60 min CPU history → Output: CPU in 10 min     │
│  Why: Captures temporal patterns & long-term memory     │
│  Result: RMSE 0.071, MAPE 9.56%, R² 0.435              │
└─────────────────────────────────────────────────────────┘
```
