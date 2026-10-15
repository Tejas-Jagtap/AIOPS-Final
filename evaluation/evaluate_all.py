"""
AIOps Evaluation Module — Publication Quality Results
=====================================================
Generates all evaluation plots, confusion matrices, ROC curves,
and metrics tables for thesis/research paper figures.

Author: AIOps Project
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, auc,
    precision_recall_curve, accuracy_score, precision_score,
    recall_score, f1_score, roc_auc_score, mean_squared_error,
    mean_absolute_error
)
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from xgboost import XGBClassifier
import joblib
import glob
import torch
import torch.nn as nn

# Plotting style
plt.rcParams.update({
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'font.family': 'serif',
})

OUTPUT_DIR = 'evaluation/plots'
METRICS_DIR = 'evaluation/metrics'
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)


# ── PyTorch Model Definitions (must match training) ──

class Autoencoder(nn.Module):
    def __init__(self, input_dim, encoding_dim=32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.BatchNorm1d(128), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.BatchNorm1d(64), nn.Dropout(0.3),
            nn.Linear(64, encoding_dim), nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64), nn.ReLU(), nn.BatchNorm1d(64), nn.Dropout(0.3),
            nn.Linear(64, 128), nn.ReLU(), nn.BatchNorm1d(128), nn.Dropout(0.3),
            nn.Linear(128, input_dim), nn.Sigmoid(),
        )
    def forward(self, x):
        return self.decoder(self.encoder(x))


class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size_1=128, hidden_size_2=64, dense_size=32):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_size_1, batch_first=True)
        self.dropout1 = nn.Dropout(0.2)
        self.lstm2 = nn.LSTM(hidden_size_1, hidden_size_2, batch_first=True)
        self.dropout2 = nn.Dropout(0.2)
        self.fc1 = nn.Linear(hidden_size_2, dense_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(dense_size, 1)
    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.dropout1(out)
        out, _ = self.lstm2(out)
        out = self.dropout2(out[:, -1, :])
        out = self.relu(self.fc1(out))
        return self.fc2(out)


# ═══════════════════════════════════════════════════════════════
# 1. XGBOOST FAILURE PREDICTION EVALUATION
# ═══════════════════════════════════════════════════════════════

def evaluate_xgboost():
    """Full evaluation of XGBoost failure prediction model"""
    print("\n" + "=" * 60)
    print("1. XGBoost Failure Prediction — Evaluation")
    print("=" * 60)

    # Load data
    df = pd.read_csv('training/data/jenkins/all_builds.csv')
    df['failed'] = (df['result'] == 'FAILURE').astype(int)

    feature_columns = ['duration', 'warnings', 'errors', 'failures',
                       'log_length', 'tests_failed', 'tests_passed', 'tests_total']
    for col in feature_columns:
        df[col] = df[col].fillna(0)

    X = df[feature_columns]
    y = df['failed']

    # Load model
    model = joblib.load('orchestrator/models/xgboost_failure.bin')

    # Train/Test split (same seed as training)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # --- 1a. Confusion Matrix ---
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    classes = ['SUCCESS', 'FAILURE']
    ax.set(xticks=[0, 1], yticks=[0, 1],
           xticklabels=classes, yticklabels=classes,
           ylabel='True Label', xlabel='Predicted Label',
           title='XGBoost Failure Prediction\nConfusion Matrix')
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f'{cm[i, j]}', ha='center', va='center',
                    color='white' if cm[i, j] > cm.max() / 2 else 'black',
                    fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/xgboost_confusion_matrix.png')
    plt.close()
    print(f"  ✓ Confusion matrix saved")

    # --- 1b. ROC Curve ---
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    roc_auc_val = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color='#2196F3', lw=2,
            label=f'XGBoost (AUC = {roc_auc_val:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5)
    ax.set(xlim=[-0.02, 1.02], ylim=[-0.02, 1.05],
           xlabel='False Positive Rate', ylabel='True Positive Rate',
           title='ROC Curve — Failure Prediction')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/xgboost_roc_curve.png')
    plt.close()
    print(f"  ✓ ROC curve saved (AUC = {roc_auc_val:.3f})")

    # --- 1c. Precision-Recall Curve ---
    precision_vals, recall_vals, _ = precision_recall_curve(y_test, y_proba)
    pr_auc = auc(recall_vals, precision_vals)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall_vals, precision_vals, color='#4CAF50', lw=2,
            label=f'XGBoost (PR-AUC = {pr_auc:.3f})')
    ax.set(xlabel='Recall', ylabel='Precision',
           title='Precision-Recall Curve — Failure Prediction')
    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/xgboost_pr_curve.png')
    plt.close()
    print(f"  ✓ Precision-Recall curve saved")

    # --- 1d. Feature Importance ---
    importance = pd.DataFrame({
        'Feature': feature_columns,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=True)

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.barh(importance['Feature'], importance['Importance'],
                   color='#FF9800', edgecolor='#E65100')
    ax.set(xlabel='Feature Importance (Gain)',
           title='XGBoost Feature Importance')
    ax.grid(True, axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/xgboost_feature_importance.png')
    plt.close()
    print(f"  ✓ Feature importance saved")

    # --- 1e. 5-Fold Cross Validation ---
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = {'accuracy': [], 'precision': [], 'recall': [], 'f1': [], 'roc_auc': []}

    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):
        X_cv_train, X_cv_val = X.iloc[train_idx], X.iloc[val_idx]
        y_cv_train, y_cv_val = y.iloc[train_idx], y.iloc[val_idx]

        n_neg = (y_cv_train == 0).sum()
        n_pos = (y_cv_train == 1).sum()
        spw = n_neg / n_pos if n_pos > 0 else 1

        cv_model = XGBClassifier(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            scale_pos_weight=spw, random_state=42, eval_metric='logloss'
        )
        cv_model.fit(X_cv_train, y_cv_train)

        y_cv_pred = cv_model.predict(X_cv_val)
        y_cv_proba = cv_model.predict_proba(X_cv_val)[:, 1]

        cv_scores['accuracy'].append(accuracy_score(y_cv_val, y_cv_pred))
        cv_scores['precision'].append(precision_score(y_cv_val, y_cv_pred, zero_division=0))
        cv_scores['recall'].append(recall_score(y_cv_val, y_cv_pred, zero_division=0))
        cv_scores['f1'].append(f1_score(y_cv_val, y_cv_pred, zero_division=0))
        cv_scores['roc_auc'].append(roc_auc_score(y_cv_val, y_cv_proba))

    xgb_metrics = {
        'model': 'XGBoost Failure Prediction',
        'test_accuracy': float(accuracy_score(y_test, y_pred)),
        'test_precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'test_recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'test_f1': float(f1_score(y_test, y_pred, zero_division=0)),
        'test_roc_auc': float(roc_auc_val),
        'cv_accuracy_mean': float(np.mean(cv_scores['accuracy'])),
        'cv_accuracy_std': float(np.std(cv_scores['accuracy'])),
        'cv_f1_mean': float(np.mean(cv_scores['f1'])),
        'cv_f1_std': float(np.std(cv_scores['f1'])),
        'cv_roc_auc_mean': float(np.mean(cv_scores['roc_auc'])),
        'cv_roc_auc_std': float(np.std(cv_scores['roc_auc'])),
    }

    print(f"\n  5-Fold CV Results:")
    print(f"    Accuracy: {xgb_metrics['cv_accuracy_mean']:.4f} ± {xgb_metrics['cv_accuracy_std']:.4f}")
    print(f"    F1:       {xgb_metrics['cv_f1_mean']:.4f} ± {xgb_metrics['cv_f1_std']:.4f}")
    print(f"    ROC AUC:  {xgb_metrics['cv_roc_auc_mean']:.4f} ± {xgb_metrics['cv_roc_auc_std']:.4f}")

    return xgb_metrics


# ═══════════════════════════════════════════════════════════════
# 2. LOG ANOMALY DETECTION EVALUATION
# ═══════════════════════════════════════════════════════════════

def evaluate_anomaly_detection():
    """Full evaluation of TF-IDF + Autoencoder anomaly detection"""
    print("\n" + "=" * 60)
    print("2. Log Anomaly Detection — Evaluation")
    print("=" * 60)

    # Load log files
    log_files = glob.glob('training/data/jenkins/logs/**/*.log', recursive=True)
    logs, labels = [], []
    for lf in log_files:
        with open(lf, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            logs.append(text)
            labels.append(1 if ('FAILURE' in text or text.count('ERROR') > 10) else 0)
    labels = np.array(labels)

    # Load models
    vectorizer = joblib.load('orchestrator/models/tfidf.pkl')
    checkpoint = torch.load('orchestrator/models/autoencoder.pth', map_location='cpu', weights_only=False)
    autoencoder = Autoencoder(checkpoint['input_dim'], checkpoint['encoding_dim'])
    autoencoder.load_state_dict(checkpoint['model_state_dict'])
    autoencoder.eval()
    threshold_data = joblib.load('orchestrator/models/anomaly_threshold.pkl')
    threshold = threshold_data['threshold']

    # Transform all logs
    X_all = vectorizer.transform(logs).toarray()

    # Split same as training
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, labels, test_size=0.2, random_state=42, stratify=labels
    )

    # Errors on test set
    with torch.no_grad():
        test_recon = autoencoder(torch.FloatTensor(X_test)).numpy()
    test_errors = np.mean(np.power(X_test - test_recon, 2), axis=1)
    y_pred = (test_errors > threshold).astype(int)

    # --- 2a. Confusion Matrix ---
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Oranges)
    ax.figure.colorbar(im, ax=ax)
    classes = ['Normal', 'Anomaly']
    ax.set(xticks=[0, 1], yticks=[0, 1],
           xticklabels=classes, yticklabels=classes,
           ylabel='True Label', xlabel='Predicted Label',
           title='Log Anomaly Detection\nConfusion Matrix')
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f'{cm[i, j]}', ha='center', va='center',
                    color='white' if cm[i, j] > cm.max() / 2 else 'black',
                    fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/anomaly_confusion_matrix.png')
    plt.close()
    print(f"  ✓ Confusion matrix saved")

    # --- 2b. ROC Curve ---
    fpr, tpr, _ = roc_curve(y_test, test_errors)
    roc_auc_val = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color='#FF5722', lw=2,
            label=f'Autoencoder (AUC = {roc_auc_val:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5)
    ax.set(xlim=[-0.02, 1.02], ylim=[-0.02, 1.05],
           xlabel='False Positive Rate', ylabel='True Positive Rate',
           title='ROC Curve — Log Anomaly Detection')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/anomaly_roc_curve.png')
    plt.close()
    print(f"  ✓ ROC curve saved (AUC = {roc_auc_val:.3f})")

    # --- 2c. Reconstruction Error Distribution ---
    normal_errors = test_errors[y_test == 0]
    anomaly_errors = test_errors[y_test == 1]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(normal_errors, bins=40, alpha=0.7, color='#4CAF50', label='Normal Logs', density=True)
    ax.hist(anomaly_errors, bins=40, alpha=0.7, color='#f44336', label='Anomalous Logs', density=True)
    ax.axvline(x=threshold, color='#333', linestyle='--', lw=2, label=f'Threshold = {threshold:.4f}')
    ax.set(xlabel='Reconstruction Error (MSE)', ylabel='Density',
           title='Reconstruction Error Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/anomaly_error_distribution.png')
    plt.close()
    print(f"  ✓ Error distribution saved")

    anomaly_metrics = {
        'model': 'TF-IDF + Autoencoder Anomaly Detection',
        'test_accuracy': float(accuracy_score(y_test, y_pred)),
        'test_precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'test_recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'test_f1': float(f1_score(y_test, y_pred, zero_division=0)),
        'test_roc_auc': float(roc_auc_val),
        'threshold': float(threshold),
        'n_logs': len(logs),
        'anomaly_rate': float(np.mean(labels)),
    }

    print(f"\n  Test Metrics:")
    print(f"    Accuracy:  {anomaly_metrics['test_accuracy']:.4f}")
    print(f"    Precision: {anomaly_metrics['test_precision']:.4f}")
    print(f"    Recall:    {anomaly_metrics['test_recall']:.4f}")
    print(f"    F1 Score:  {anomaly_metrics['test_f1']:.4f}")
    print(f"    ROC AUC:   {anomaly_metrics['test_roc_auc']:.4f}")

    return anomaly_metrics


# ═══════════════════════════════════════════════════════════════
# 3. LSTM CPU FORECASTING EVALUATION
# ═══════════════════════════════════════════════════════════════

def evaluate_cpu_forecasting():
    """Full evaluation of LSTM CPU forecasting model"""
    print("\n" + "=" * 60)
    print("3. LSTM CPU Forecasting — Evaluation")
    print("=" * 60)

    from sklearn.preprocessing import MinMaxScaler

    # Load data
    df = pd.read_csv('training/data/prometheus/cpu_timeseries.csv')
    cpu_values = df['cpu_usage'].values.reshape(-1, 1)

    # Load model & scaler
    checkpoint = torch.load('orchestrator/models/lstm_cpu.pth', map_location='cpu', weights_only=False)
    lstm_model = LSTMModel()
    lstm_model.load_state_dict(checkpoint['model_state_dict'])
    lstm_model.eval()
    scaler = joblib.load('orchestrator/models/cpu_scaler.pkl')

    # Prepare sequences (same as training)
    LOOKBACK = 60
    FORECAST_HORIZON = 10

    cpu_scaled = scaler.transform(cpu_values)
    X, y = [], []
    for i in range(len(cpu_scaled) - LOOKBACK - FORECAST_HORIZON + 1):
        X.append(cpu_scaled[i:(i + LOOKBACK), 0])
        y.append(cpu_scaled[i + LOOKBACK + FORECAST_HORIZON - 1, 0])
    X = np.array(X).reshape(-1, LOOKBACK, 1)
    y = np.array(y)

    # Split same as training
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, shuffle=False
    )

    # Predict
    with torch.no_grad():
        y_pred_scaled = lstm_model(torch.FloatTensor(X_test)).squeeze(-1).numpy()

    # Inverse transform
    y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
    y_pred_actual = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()

    # Metrics
    mse = mean_squared_error(y_test_actual, y_pred_actual)
    mae = mean_absolute_error(y_test_actual, y_pred_actual)
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs((y_test_actual - y_pred_actual) / (y_test_actual + 1e-8))) * 100

    # R² score
    ss_res = np.sum((y_test_actual - y_pred_actual) ** 2)
    ss_tot = np.sum((y_test_actual - np.mean(y_test_actual)) ** 2)
    r2 = 1 - (ss_res / ss_tot)

    # --- 3a. Actual vs Predicted (first 300 points) ---
    n_plot = min(300, len(y_test_actual))
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(range(n_plot), y_test_actual[:n_plot], color='#2196F3', lw=1.5, alpha=0.8, label='Actual')
    ax.plot(range(n_plot), y_pred_actual[:n_plot], color='#f44336', lw=1.5, alpha=0.8, label='Predicted')
    ax.fill_between(range(n_plot),
                    y_pred_actual[:n_plot] - 2 * rmse,
                    y_pred_actual[:n_plot] + 2 * rmse,
                    alpha=0.15, color='#f44336', label='±2σ')
    ax.set(xlabel='Time Step (minutes)', ylabel='CPU Usage',
           title=f'LSTM CPU Forecasting: Actual vs Predicted (RMSE={rmse:.4f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/lstm_actual_vs_predicted.png')
    plt.close()
    print(f"  ✓ Actual vs Predicted saved")

    # --- 3b. Residual plot ---
    residuals = y_test_actual - y_pred_actual
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].scatter(y_pred_actual, residuals, alpha=0.3, s=10, color='#9C27B0')
    axes[0].axhline(0, color='black', lw=1)
    axes[0].set(xlabel='Predicted CPU', ylabel='Residual',
                title='Residual Plot')
    axes[0].grid(True, alpha=0.3)

    axes[1].hist(residuals, bins=50, color='#9C27B0', alpha=0.7, density=True, edgecolor='white')
    axes[1].set(xlabel='Residual', ylabel='Density',
                title='Residual Distribution')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/lstm_residuals.png')
    plt.close()
    print(f"  ✓ Residual plots saved")

    # --- 3c. Scatter plot with perfect line ---
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_test_actual, y_pred_actual, alpha=0.3, s=10, color='#009688')
    ax.plot([y_test_actual.min(), y_test_actual.max()],
            [y_test_actual.min(), y_test_actual.max()],
            'r--', lw=2, label='Perfect Prediction')
    ax.set(xlabel='Actual CPU Usage', ylabel='Predicted CPU Usage',
           title=f'CPU Forecasting: Actual vs Predicted (R²={r2:.3f})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/lstm_scatter.png')
    plt.close()
    print(f"  ✓ Scatter plot saved")

    lstm_metrics = {
        'model': 'LSTM CPU Forecasting',
        'mse': float(mse),
        'mae': float(mae),
        'rmse': float(rmse),
        'mape': float(mape),
        'r2': float(r2),
        'n_sequences': len(X),
        'lookback': LOOKBACK,
        'forecast_horizon': FORECAST_HORIZON,
    }

    print(f"\n  Test Metrics:")
    print(f"    MSE:   {mse:.6f}")
    print(f"    MAE:   {mae:.4f}")
    print(f"    RMSE:  {rmse:.4f}")
    print(f"    MAPE:  {mape:.2f}%")
    print(f"    R²:    {r2:.4f}")

    return lstm_metrics


# ═══════════════════════════════════════════════════════════════
# 4. COMBINED SUMMARY FIGURES
# ═══════════════════════════════════════════════════════════════

def create_summary_figures(xgb_metrics, anomaly_metrics, lstm_metrics):
    """Create summary comparison figures for thesis"""
    print("\n" + "=" * 60)
    print("4. Summary Figures")
    print("=" * 60)

    # --- 4a. Model Comparison Bar Chart ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Classification models comparison
    models = ['XGBoost\n(Failure)', 'Autoencoder\n(Anomaly)']
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'ROC AUC']
    xgb_vals = [xgb_metrics['test_accuracy'], xgb_metrics['test_precision'],
                xgb_metrics['test_recall'], xgb_metrics['test_f1'], xgb_metrics['test_roc_auc']]
    ae_vals = [anomaly_metrics['test_accuracy'], anomaly_metrics['test_precision'],
               anomaly_metrics['test_recall'], anomaly_metrics['test_f1'], anomaly_metrics['test_roc_auc']]

    x = np.arange(len(metrics_names))
    width = 0.35
    bars1 = axes[0].bar(x - width/2, xgb_vals, width, label='XGBoost', color='#2196F3', edgecolor='white')
    bars2 = axes[0].bar(x + width/2, ae_vals, width, label='Autoencoder', color='#FF5722', edgecolor='white')
    axes[0].set_ylabel('Score')
    axes[0].set_title('Classification Model Comparison')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics_names, rotation=15)
    axes[0].legend()
    axes[0].set_ylim(0, 1.15)
    axes[0].grid(True, axis='y', alpha=0.3)
    for bar in bars1:
        axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
                     f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
                     f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=8)

    # LSTM regression metrics
    reg_metrics = ['MSE', 'MAE', 'RMSE', 'MAPE(%)/100']
    reg_vals = [lstm_metrics['mse'], lstm_metrics['mae'],
                lstm_metrics['rmse'], lstm_metrics['mape'] / 100]
    colors = ['#4CAF50', '#8BC34A', '#CDDC39', '#FFC107']
    bars3 = axes[1].bar(reg_metrics, reg_vals, color=colors, edgecolor='white')
    axes[1].set_ylabel('Value')
    axes[1].set_title(f'LSTM Forecasting Metrics (R² = {lstm_metrics["r2"]:.3f})')
    axes[1].grid(True, axis='y', alpha=0.3)
    for bar in bars3:
        axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.002,
                     f'{bar.get_height():.4f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/model_comparison_summary.png')
    plt.close()
    print(f"  ✓ Model comparison chart saved")

    # --- 4b. System Architecture Metrics Table ---
    summary_table = {
        'Module': ['Failure Prediction', 'Anomaly Detection', 'CPU Forecasting'],
        'Algorithm': ['XGBoost', 'TF-IDF + Autoencoder', 'LSTM'],
        'Key Metric': [
            f"F1 = {xgb_metrics['test_f1']:.3f}",
            f"F1 = {anomaly_metrics['test_f1']:.3f}",
            f"RMSE = {lstm_metrics['rmse']:.4f}"
        ],
        'ROC AUC / R²': [
            f"{xgb_metrics['test_roc_auc']:.3f}",
            f"{anomaly_metrics['test_roc_auc']:.3f}",
            f"{lstm_metrics['r2']:.3f}"
        ],
    }
    summary_df = pd.DataFrame(summary_table)

    fig, ax = plt.subplots(figsize=(10, 3))
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=summary_df.values, colLabels=summary_df.columns,
                     loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)

    # Style header
    for j in range(len(summary_df.columns)):
        table[(0, j)].set_facecolor('#37474F')
        table[(0, j)].set_text_props(color='white', fontweight='bold')

    ax.set_title('AIOps System — Model Performance Summary', fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/performance_summary_table.png')
    plt.close()
    print(f"  ✓ Performance summary table saved")

    return summary_df


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("AIOps System — Full Evaluation Suite")
    print("=" * 60)

    # Run all evaluations
    xgb_metrics = evaluate_xgboost()
    anomaly_metrics = evaluate_anomaly_detection()
    lstm_metrics = evaluate_cpu_forecasting()

    # Create summary figures
    summary_df = create_summary_figures(xgb_metrics, anomaly_metrics, lstm_metrics)

    # Save all metrics to JSON
    all_metrics = {
        'xgboost_failure_prediction': xgb_metrics,
        'anomaly_detection': anomaly_metrics,
        'cpu_forecasting': lstm_metrics,
    }
    with open(f'{METRICS_DIR}/all_metrics.json', 'w') as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Evaluation complete!")
    print(f"  Plots: {OUTPUT_DIR}/")
    print(f"  Metrics: {METRICS_DIR}/all_metrics.json")
    print(f"{'=' * 60}")

    # Print summary table
    print(f"\n{summary_df.to_string(index=False)}")


if __name__ == '__main__':
    main()
