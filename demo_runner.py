"""
AIOps Live Demo Runner — Panel Presentation
=============================================
Runs all demos sequentially with formatted output for live presentation.

Usage:
  python demo_runner.py              # Full demo (all sections)
  python demo_runner.py --section 1  # Only Section 1
  python demo_runner.py --quick      # Quick 3-minute overview

Requires: Orchestrator running on port 8001
  Start with: python -m uvicorn orchestrator.main:app --port 8001
"""

import os
import sys
import json
import time
import csv
import argparse

# Ensure UTF-8 output on Windows (box-drawing characters)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
import requests
import numpy as np

BASE_URL = "http://localhost:8001"

# ── Formatting Helpers ─────────────────────────────────────────

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"
CYAN = "\033[96m"


def header(title, section_num=None):
    print()
    print(f"{BOLD}{BLUE}{'═' * 70}{RESET}")
    if section_num:
        print(f"{BOLD}{BLUE}  Section {section_num}: {title}{RESET}")
    else:
        print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'═' * 70}{RESET}")
    print()


def subheader(title):
    print(f"\n  {BOLD}{CYAN}── {title} ──{RESET}\n")


def success(msg):
    print(f"  {GREEN}✓{RESET} {msg}")


def info(msg):
    print(f"  {YELLOW}→{RESET} {msg}")


def result(label, value, highlight=False):
    color = GREEN if highlight else ""
    reset = RESET if highlight else ""
    print(f"    {label}: {color}{BOLD}{value}{RESET}")


def pause(msg="Press Enter to continue..."):
    input(f"\n  {YELLOW}⏸ {msg}{RESET}")


def check_orchestrator():
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# SECTION 1: System Architecture & Data Pipeline
# ═══════════════════════════════════════════════════════════════

def section_1_architecture():
    header("System Architecture & Data Pipeline", 1)

    subheader("1.1 Project Structure")
    components = [
        ("orchestrator/", "FastAPI ML serving layer (4 routers, 6 models)"),
        ("training/", "3 ML training pipelines + synthetic data generator"),
        ("collectors/", "Jenkins, Prometheus, Real-time metric collectors"),
        ("autoscaler/", "Predictive K8s autoscaler (decision engine + scaler)"),
        ("evaluation/", "12 publication-quality evaluation plots"),
        ("demo-todo-app/", "Next.js CI/CD target app with Jenkinsfile"),
        ("kubernetes_manifests/", "K8s deployments, services, RBAC"),
        ("prometheus/", "Monitoring stack configuration"),
    ]
    for path, desc in components:
        info(f"{BOLD}{path:<30}{RESET} {desc}")

    subheader("1.2 Training Data Statistics")
    df_path = "training/data/jenkins/all_builds.csv"
    with open(df_path) as f:
        rows = list(csv.DictReader(f))
    total = len(rows)
    counts = {}
    for r in rows:
        counts[r['result']] = counts.get(r['result'], 0) + 1

    result("Total Jenkins builds", total)
    for k, v in sorted(counts.items()):
        pct = v / total * 100
        result(f"  {k}", f"{v} ({pct:.1f}%)")

    log_dir = "training/data/jenkins/logs/aiops-demo-todo-app"
    log_count = len([f for f in os.listdir(log_dir) if f.endswith('.log')])
    result("Console log files", log_count)

    with open("training/data/prometheus/cpu_timeseries.csv") as f:
        cpu_rows = list(csv.DictReader(f))
    cpu_vals = [float(r['cpu_usage']) for r in cpu_rows]
    result("CPU timeseries points", f"{len(cpu_vals)} (7 days @ 1-min)")
    result("CPU range", f"[{min(cpu_vals):.3f}, {max(cpu_vals):.3f}]")
    result("CPU mean", f"{np.mean(cpu_vals):.3f}")

    subheader("1.3 Trained Models")
    models = {
        "xgboost_failure.bin": "XGBoost — Build Failure Prediction",
        "tfidf.pkl": "TF-IDF Vectorizer — Log Feature Extraction",
        "autoencoder.pth": "PyTorch Autoencoder — Log Anomaly Detection",
        "anomaly_threshold.pkl": "Anomaly Threshold (95th percentile)",
        "lstm_cpu.pth": "PyTorch LSTM — CPU Usage Forecasting",
        "cpu_scaler.pkl": "MinMaxScaler — CPU Normalization",
    }
    for fname, desc in models.items():
        fpath = f"orchestrator/models/{fname}"
        size = os.path.getsize(fpath)
        size_str = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/1024/1024:.1f} MB"
        success(f"{fname:<28} {size_str:>10}  {desc}")


# ═══════════════════════════════════════════════════════════════
# SECTION 2: ML Model Performance (Evaluation Results)
# ═══════════════════════════════════════════════════════════════

def section_2_evaluation():
    header("ML Model Performance & Evaluation", 2)

    with open("evaluation/metrics/all_metrics.json") as f:
        metrics = json.load(f)

    subheader("2.1 XGBoost — Build Failure Prediction")
    xgb = metrics['xgboost_failure_prediction']
    result("Accuracy", f"{xgb['test_accuracy']:.4f}", highlight=True)
    result("Precision", f"{xgb['test_precision']:.4f}")
    result("Recall", f"{xgb['test_recall']:.4f}")
    result("F1 Score", f"{xgb['test_f1']:.4f}", highlight=True)
    result("ROC AUC", f"{xgb['test_roc_auc']:.4f}", highlight=True)
    result("5-Fold CV Accuracy", f"{xgb['cv_accuracy_mean']:.4f} ± {xgb['cv_accuracy_std']:.4f}")
    result("5-Fold CV ROC AUC", f"{xgb['cv_roc_auc_mean']:.4f} ± {xgb['cv_roc_auc_std']:.4f}")

    subheader("2.2 TF-IDF + Autoencoder — Log Anomaly Detection")
    anom = metrics['anomaly_detection']
    result("Accuracy", f"{anom['test_accuracy']:.4f}", highlight=True)
    result("Precision", f"{anom['test_precision']:.4f}")
    result("Recall", f"{anom['test_recall']:.4f}")
    result("F1 Score", f"{anom['test_f1']:.4f}", highlight=True)
    result("ROC AUC", f"{anom['test_roc_auc']:.4f}", highlight=True)
    result("Anomaly Threshold", f"{anom['threshold']:.6f}")

    subheader("2.3 LSTM — CPU Usage Forecasting")
    lstm = metrics['cpu_forecasting']
    result("RMSE", f"{lstm['rmse']:.4f}", highlight=True)
    result("MAE", f"{lstm['mae']:.4f}")
    result("MAPE", f"{lstm['mape']:.2f}%")
    result("R²", f"{lstm['r2']:.4f}", highlight=True)

    subheader("2.4 Evaluation Plots Generated")
    plots_dir = "evaluation/plots"
    for fname in sorted(os.listdir(plots_dir)):
        if fname.endswith('.png'):
            size = os.path.getsize(os.path.join(plots_dir, fname))
            success(f"{fname:<45} ({size/1024:.0f} KB)")


# ═══════════════════════════════════════════════════════════════
# SECTION 3: Live API Demo
# ═══════════════════════════════════════════════════════════════

def section_3_live_api():
    header("Live API Demonstration", 3)

    if not check_orchestrator():
        print(f"  {RED}✗ Orchestrator not running!{RESET}")
        print(f"  Start with: python -m uvicorn orchestrator.main:app --port 8001")
        return

    # ── 3.1 System Health ──
    subheader("3.1 System Health Check")
    r = requests.get(f"{BASE_URL}/")
    data = r.json()
    result("Service", data['service'])
    result("Version", data['version'])
    result("Status", data['status'], highlight=True)
    info(f"Available endpoints: {', '.join(data['endpoints'].keys())}")
    info(f"API Docs: {BASE_URL}/docs")

    # ── 3.2 Failure Prediction ──
    subheader("3.2 Build Failure Prediction")

    info("Scenario A: A healthy SUCCESS build")
    payload = {
        "duration": 65, "warnings": 1, "errors": 0, "failures": 0,
        "log_length": 16000, "tests_failed": 0, "tests_passed": 24
    }
    info(f"Input: duration=65s, warnings=1, errors=0, tests_failed=0")
    r = requests.post(f"{BASE_URL}/predict_failure", json=payload)
    prob = r.json()['failure_probability']
    result("Failure Probability", f"{prob:.6f} → {'SUCCESS ✓' if prob < 0.5 else 'FAILURE ✗'}", highlight=True)

    print()
    info("Scenario B: A failing build with many errors")
    payload = {
        "duration": 180, "warnings": 8, "errors": 15, "failures": 3,
        "log_length": 25000, "tests_failed": 8, "tests_passed": 16
    }
    info(f"Input: duration=180s, warnings=8, errors=15, tests_failed=8")
    r = requests.post(f"{BASE_URL}/predict_failure", json=payload)
    prob = r.json()['failure_probability']
    result("Failure Probability", f"{prob:.6f} → {'SUCCESS ✓' if prob < 0.5 else 'FAILURE ✗'}", highlight=True)

    # ── 3.3 Anomaly Detection ──
    subheader("3.3 Log Anomaly Detection")

    # Load real logs
    import pandas as pd
    df = pd.read_csv("training/data/jenkins/all_builds.csv")

    # Normal log
    success_bn = df[df['result'] == 'SUCCESS']['build_number'].iloc[0]
    with open(f"training/data/jenkins/logs/aiops-demo-todo-app/build_{success_bn}.log",
              'r', encoding='utf-8', errors='ignore') as f:
        normal_log = f.read()

    info(f"Scenario A: SUCCESS build #{success_bn} log ({len(normal_log)} chars)")
    r = requests.post(f"{BASE_URL}/detect_anomaly", json={"log": normal_log})
    data = r.json()
    result("Anomaly Score", f"{data['anomaly_score']:.6f}")
    result("Is Anomaly?", f"{'YES ✗' if data['is_anomaly'] else 'NO ✓'}", highlight=True)

    # Failure log
    failure_bn = df[df['result'] == 'FAILURE']['build_number'].iloc[0]
    with open(f"training/data/jenkins/logs/aiops-demo-todo-app/build_{failure_bn}.log",
              'r', encoding='utf-8', errors='ignore') as f:
        fail_log = f.read()

    print()
    info(f"Scenario B: FAILURE build #{failure_bn} log ({len(fail_log)} chars)")
    r = requests.post(f"{BASE_URL}/detect_anomaly", json={"log": fail_log})
    data = r.json()
    result("Anomaly Score", f"{data['anomaly_score']:.6f}")
    result("Is Anomaly?", f"{'YES ✓ (Anomaly Detected!)' if data['is_anomaly'] else 'NO ✗'}", highlight=True)

    # ── 3.4 CPU Forecasting ──
    subheader("3.4 CPU Usage Forecasting")

    with open("training/data/prometheus/cpu_timeseries.csv") as f:
        cpu_rows = list(csv.DictReader(f))

    # Use different time windows
    windows = [
        ("Morning peak (9am-10am)", 540, 600),
        ("Afternoon (2pm-3pm)", 840, 900),
        ("Night (12am-1am)", 0, 60),
    ]
    for label, start, end in windows:
        cpu_history = [float(r['cpu_usage']) for r in cpu_rows[start:end]]
        avg_input = np.mean(cpu_history)
        r = requests.post(f"{BASE_URL}/forecast_cpu", json={"cpu_history": cpu_history})
        predicted = r.json()['predicted_cpu']
        info(f"{label}: avg_input={avg_input:.3f}")
        result("Predicted CPU (10min ahead)", f"{predicted:.4f}", highlight=True)

    # ── 3.5 Autoscaling Decision ──
    subheader("3.5 Predictive Autoscaling")
    info("K8s cluster status: Not connected (expected in local demo)")
    payload = {
        "deployment_name": "demo-todo-app",
        "predicted_cpu": 0.85,
        "anomaly_score": 0.002,
        "failure_probability": 0.75
    }
    r = requests.post(f"{BASE_URL}/autoscale", json=payload)
    result("Status Code", r.status_code)
    result("Response", r.json().get('detail', r.json()))
    info("In production: Would scale from 2→4 replicas based on high CPU + anomaly + failure signals")


# ═══════════════════════════════════════════════════════════════
# SECTION 4: CI/CD Pipeline & Integration
# ═══════════════════════════════════════════════════════════════

def section_4_cicd():
    header("CI/CD Pipeline & Integration", 4)

    subheader("4.1 Jenkins Pipeline Stages")
    stages = [
        ("1. Checkout", "Git clone from repository"),
        ("2. Install Dependencies", "npm install --legacy-peer-deps"),
        ("3. Lint", "ESLint static code analysis"),
        ("4. Test", "Jest unit tests with coverage"),
        ("5. Build", "Next.js production build"),
        ("6. AIOps Analysis", "→ Send build data to orchestrator API"),
    ]
    for stage, desc in stages:
        info(f"{BOLD}{stage:<25}{RESET} {desc}")

    subheader("4.2 AIOps Integration Points")
    flows = [
        "Jenkins webhook → Orchestrator /predict_failure → Early failure warning",
        "Console log → Orchestrator /detect_anomaly → Anomaly alert",
        "Prometheus metrics → Orchestrator /forecast_cpu → CPU prediction",
        "All signals → Orchestrator /autoscale → K8s scaling decision",
    ]
    for i, flow in enumerate(flows, 1):
        success(f"Flow {i}: {flow}")

    subheader("4.3 Kubernetes Architecture")
    info("Deployments:")
    result("  aiops-orchestrator", "FastAPI + ML models (port 8000)")
    result("  aiops-autoscaler", "Prediction loop (60s interval)")
    result("  demo-todo-app", "Target workload (auto-scaled)")
    info("Services:")
    result("  ClusterIP", "Internal service discovery (port 8000)")
    result("  LoadBalancer", "External access")
    info("RBAC:")
    result("  ServiceAccount", "aiops-orchestrator")
    result("  ClusterRole", "get/list/watch/patch deployments + pods")

    subheader("4.4 Monitoring Stack")
    info("Prometheus scrapes /api/metrics from demo-todo-app every 15s")
    info("Metrics: http_requests_total, request_duration, todos_total, errors, memory")
    info("Grafana dashboards available via docker-compose")


# ═══════════════════════════════════════════════════════════════
# SECTION 5: End-to-End Integration Test
# ═══════════════════════════════════════════════════════════════

def section_5_e2e():
    header("End-to-End Integration Test", 5)

    if not check_orchestrator():
        print(f"  {RED}✗ Orchestrator not running!{RESET}")
        return

    subheader("5.1 Full Pipeline Simulation")

    # Pick a failure build
    with open("training/data/jenkins/all_builds.csv") as f:
        for row in csv.DictReader(f):
            if row['result'] == 'FAILURE':
                build = row
                break

    bn = build['build_number']
    info(f"Selected Build #{bn} (result={build['result']})")
    info(f"  Duration: {float(build['duration']):.0f}s, Errors: {build['errors']}, Tests Failed: {int(float(build['tests_failed']))}")

    # Step 1: Failure Prediction
    print()
    info(f"{BOLD}Step 1: Predict Build Failure{RESET}")
    payload = {
        "duration": int(float(build['duration'])),
        "warnings": int(float(build['warnings'])),
        "errors": int(float(build['errors'])),
        "failures": int(float(build.get('failures', 0))),
        "log_length": int(float(build.get('log_length', 20000))),
        "tests_failed": int(float(build['tests_failed'])),
        "tests_passed": int(float(build['tests_passed'])),
        "tests_total": int(float(build['tests_total']))
    }
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/predict_failure", json=payload)
    t1 = time.time()
    failure_prob = r.json()['failure_probability']
    result("Failure Probability", f"{failure_prob:.6f}", highlight=True)
    result("Latency", f"{(t1-t0)*1000:.0f}ms")

    # Step 2: Anomaly Detection
    info(f"{BOLD}Step 2: Detect Log Anomalies{RESET}")
    log_path = f"training/data/jenkins/logs/aiops-demo-todo-app/build_{bn}.log"
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        log_text = f.read()

    t0 = time.time()
    r = requests.post(f"{BASE_URL}/detect_anomaly", json={"log": log_text})
    t1 = time.time()
    anomaly_data = r.json()
    result("Anomaly Score", f"{anomaly_data['anomaly_score']:.6f}")
    result("Is Anomaly", str(anomaly_data['is_anomaly']), highlight=True)
    result("Latency", f"{(t1-t0)*1000:.0f}ms")

    # Step 3: CPU Forecast
    info(f"{BOLD}Step 3: Forecast CPU Usage{RESET}")
    with open("training/data/prometheus/cpu_timeseries.csv") as f:
        cpu_rows = list(csv.DictReader(f))
    cpu_hist = [float(r['cpu_usage']) for r in cpu_rows[-60:]]

    t0 = time.time()
    r = requests.post(f"{BASE_URL}/forecast_cpu", json={"cpu_history": cpu_hist})
    t1 = time.time()
    predicted_cpu = r.json()['predicted_cpu']
    result("Predicted CPU", f"{predicted_cpu:.4f}", highlight=True)
    result("Latency", f"{(t1-t0)*1000:.0f}ms")

    # Step 4: Autoscale Decision
    info(f"{BOLD}Step 4: Autoscale Decision{RESET}")
    payload = {
        "deployment_name": "demo-todo-app",
        "predicted_cpu": predicted_cpu,
        "anomaly_score": anomaly_data['anomaly_score'],
        "failure_probability": failure_prob
    }
    r = requests.post(f"{BASE_URL}/autoscale", json=payload)
    result("Autoscale Response", r.json())

    # Summary
    subheader("5.2 Pipeline Summary")
    print(f"    ┌─────────────────────────────────────────────────────┐")
    print(f"    │  {BOLD}Build #{bn}{RESET} → {RED}FAILURE detected{RESET}                       │")
    print(f"    │                                                     │")
    print(f"    │  Failure Probability : {BOLD}{failure_prob:.4f}{RESET}                   │")
    print(f"    │  Anomaly Score       : {BOLD}{anomaly_data['anomaly_score']:.6f}{RESET}               │")
    print(f"    │  Predicted CPU       : {BOLD}{predicted_cpu:.4f}{RESET}                   │")
    print(f"    │  Autoscale Action    : {BOLD}Scale Up (when K8s active){RESET}   │")
    print(f"    └─────────────────────────────────────────────────────┘")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

SECTIONS = {
    1: ("System Architecture & Data Pipeline", section_1_architecture),
    2: ("ML Model Performance & Evaluation", section_2_evaluation),
    3: ("Live API Demonstration", section_3_live_api),
    4: ("CI/CD Pipeline & Integration", section_4_cicd),
    5: ("End-to-End Integration Test", section_5_e2e),
}


def main():
    parser = argparse.ArgumentParser(description="AIOps Live Demo Runner")
    parser.add_argument("--section", type=int, choices=range(1, 6),
                        help="Run only a specific section (1-5)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick overview (sections 2 + 3 only)")
    parser.add_argument("--interactive", action="store_true",
                        help="Pause between sections")
    args = parser.parse_args()

    print(f"\n{BOLD}{BLUE}")
    print("  ╔════════════════════════════════════════════════════════════╗")
    print("  ║                                                          ║")
    print("  ║     AIOps: AI-Driven Predictive CI/CD Analytics          ║")
    print("  ║     ─────────────────────────────────────────────         ║")
    print("  ║     MTech Final Year Project — Live Demo                  ║")
    print("  ║     Tejas Jagtap                                          ║")
    print("  ║                                                          ║")
    print("  ╚════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    if args.section:
        sections_to_run = [args.section]
    elif args.quick:
        sections_to_run = [2, 3]
    else:
        sections_to_run = [1, 2, 3, 4, 5]

    for sec_num in sections_to_run:
        name, func = SECTIONS[sec_num]
        func()
        if args.interactive and sec_num != sections_to_run[-1]:
            pause(f"Section {sec_num} complete. Press Enter for next section...")

    header("Demo Complete")
    success(f"All {len(sections_to_run)} sections demonstrated successfully")
    info(f"API Documentation: {BASE_URL}/docs")
    info(f"Evaluation Plots: evaluation/plots/")
    info(f"Metrics JSON: evaluation/metrics/all_metrics.json")
    info(f"E2E Tests: python tests/test_e2e.py")
    print()


if __name__ == "__main__":
    main()
