"""
End-to-End Integration Test for AIOps System
=============================================
Tests the complete pipeline:
  Jenkins Data → Training → Models → FastAPI Orchestrator → Predictions

Run with: python tests/test_e2e.py
Requires: Orchestrator running on port 8001
"""

import os
import sys
import json
import csv
import time
import requests
from datetime import datetime

BASE_URL = "http://localhost:8001"
PASS = "✓ PASS"
FAIL = "✗ FAIL"
SKIP = "⊘ SKIP"

results = []

def test(name, fn):
    """Run a test and record result"""
    try:
        ok, detail = fn()
        status = PASS if ok else FAIL
        results.append((name, status, detail))
        print(f"  {status}  {name}: {detail}")
    except Exception as e:
        results.append((name, FAIL, str(e)))
        print(f"  {FAIL}  {name}: {e}")


def test_data_files_exist():
    """Verify all synthetic training data exists"""
    files = [
        "training/data/jenkins/all_builds.csv",
        "training/data/prometheus/cpu_timeseries.csv",
    ]
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        return False, f"Missing: {missing}"
    
    # Check some log files exist
    log_dir = "training/data/jenkins/logs/aiops-demo-todo-app"
    if not os.path.isdir(log_dir):
        return False, f"Missing log dir: {log_dir}"
    
    log_count = len([f for f in os.listdir(log_dir) if f.endswith('.log')])
    return log_count >= 100, f"{log_count} log files found"


def test_training_data_quality():
    """Verify training data has correct distribution"""
    with open("training/data/jenkins/all_builds.csv") as f:
        rows = list(csv.DictReader(f))
    
    total = len(rows)
    result_counts = {}
    for r in rows:
        result_counts[r['result']] = result_counts.get(r['result'], 0) + 1
    
    has_all_classes = all(c in result_counts for c in ['SUCCESS', 'FAILURE', 'UNSTABLE'])
    failure_pct = result_counts.get('FAILURE', 0) / total * 100
    
    detail = f"{total} builds, distribution: {dict(result_counts)}"
    return has_all_classes and total >= 500, detail


def test_cpu_timeseries_quality():
    """Verify CPU timeseries data"""
    with open("training/data/prometheus/cpu_timeseries.csv") as f:
        rows = list(csv.DictReader(f))
    
    total = len(rows)
    values = [float(r['cpu_usage']) for r in rows]
    min_v, max_v = min(values), max(values)
    mean_v = sum(values) / len(values)
    
    detail = f"{total} points, range=[{min_v:.3f}, {max_v:.3f}], mean={mean_v:.3f}"
    return total >= 5000 and 0.0 <= min_v and max_v <= 1.0, detail


def test_models_exist():
    """Verify all trained model files exist"""
    models = [
        "orchestrator/models/xgboost_failure.bin",
        "orchestrator/models/tfidf.pkl",
        "orchestrator/models/autoencoder.pth",
        "orchestrator/models/anomaly_threshold.pkl",
        "orchestrator/models/lstm_cpu.pth",
        "orchestrator/models/cpu_scaler.pkl",
    ]
    missing = [m for m in models if not os.path.exists(m)]
    sizes = {os.path.basename(m): os.path.getsize(m) for m in models if os.path.exists(m)}
    
    if missing:
        return False, f"Missing: {missing}"
    return True, f"All 6 models present, sizes: {sizes}"


def test_evaluation_outputs():
    """Verify evaluation plots and metrics exist"""
    metrics_file = "evaluation/metrics/all_metrics.json"
    if not os.path.exists(metrics_file):
        return False, "Missing all_metrics.json"
    
    with open(metrics_file) as f:
        metrics = json.load(f)
    
    plots_dir = "evaluation/plots"
    plot_count = len([f for f in os.listdir(plots_dir) if f.endswith('.png')]) if os.path.isdir(plots_dir) else 0
    
    detail = f"{plot_count} plots, metrics keys: {list(metrics.keys())}"
    return plot_count >= 10, detail


def test_orchestrator_root():
    """Test orchestrator root endpoint"""
    r = requests.get(f"{BASE_URL}/", timeout=10)
    data = r.json()
    return r.status_code == 200 and data.get('status') == 'running', f"status={data.get('status')}"


def test_failure_prediction_success():
    """Test failure prediction with SUCCESS-like build"""
    payload = {
        "duration": 65, "warnings": 1, "errors": 0, "failures": 0,
        "log_length": 16000, "tests_failed": 0, "tests_passed": 24, "tests_total": 24
    }
    r = requests.post(f"{BASE_URL}/predict_failure", json=payload, timeout=10)
    data = r.json()
    prob = data['failure_probability']
    return prob < 0.1, f"probability={prob:.4f} (expected < 0.1)"


def test_failure_prediction_failure():
    """Test failure prediction with FAILURE-like build"""
    payload = {
        "duration": 120, "warnings": 5, "errors": 8, "failures": 2,
        "log_length": 25000, "tests_failed": 5, "tests_passed": 19, "tests_total": 24
    }
    r = requests.post(f"{BASE_URL}/predict_failure", json=payload, timeout=10)
    data = r.json()
    prob = data['failure_probability']
    return prob > 0.7, f"probability={prob:.4f} (expected > 0.7)"


def test_anomaly_detection_normal():
    """Test anomaly detection with a normal (SUCCESS) log file"""
    log_path = "training/data/jenkins/logs/aiops-demo-todo-app/build_1.log"
    if not os.path.exists(log_path):
        return False, "Missing build_1.log"
    
    log = open(log_path, encoding='utf-8', errors='replace').read()
    r = requests.post(f"{BASE_URL}/detect_anomaly", json={"log": log}, timeout=30)
    data = r.json()
    return not data['is_anomaly'], f"score={data['anomaly_score']:.6f}, anomaly={data['is_anomaly']}"


def test_anomaly_detection_failure():
    """Test anomaly detection with a FAILURE log file"""
    # Find a failure build
    with open("training/data/jenkins/all_builds.csv") as f:
        for row in csv.DictReader(f):
            if row['result'] == 'FAILURE':
                build_num = row['build_number']
                break
    
    log_path = f"training/data/jenkins/logs/aiops-demo-todo-app/build_{build_num}.log"
    log = open(log_path, encoding='utf-8', errors='replace').read()
    r = requests.post(f"{BASE_URL}/detect_anomaly", json={"log": log}, timeout=30)
    data = r.json()
    return data['is_anomaly'], f"score={data['anomaly_score']:.6f}, anomaly={data['is_anomaly']}"


def test_cpu_forecast():
    """Test CPU forecasting with real timeseries data"""
    with open("training/data/prometheus/cpu_timeseries.csv") as f:
        rows = list(csv.DictReader(f))
    
    cpu_history = [float(r['cpu_usage']) for r in rows[500:560]]
    r = requests.post(f"{BASE_URL}/forecast_cpu", json={"cpu_history": cpu_history}, timeout=30)
    data = r.json()
    predicted = data['predicted_cpu']
    return 0.0 <= predicted <= 1.0, f"predicted_cpu={predicted:.4f}"


def test_autoscale_unavailable():
    """Test autoscale returns 503 when K8s not available"""
    payload = {
        "deployment_name": "demo-todo-app",
        "predicted_cpu": 0.85,
        "anomaly_score": 0.002,
        "failure_probability": 0.75
    }
    r = requests.post(f"{BASE_URL}/autoscale", json=payload, timeout=10)
    # 500/503 if no K8s cluster, 200 if K8s running - all are valid
    return r.status_code in [200, 500, 503], f"status_code={r.status_code}"


def test_full_pipeline():
    """
    Full pipeline test:
    1. Take a FAILURE build's features
    2. Predict failure
    3. Detect anomaly from its log
    4. Forecast CPU
    5. Attempt autoscale decision
    """
    # 1. Get a FAILURE build
    with open("training/data/jenkins/all_builds.csv") as f:
        for row in csv.DictReader(f):
            if row['result'] == 'FAILURE':
                build = row
                break
    
    # 2. Predict failure
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
    r_fail = requests.post(f"{BASE_URL}/predict_failure", json=payload, timeout=10)
    failure_prob = r_fail.json()['failure_probability']
    
    # 3. Detect anomaly
    bn = build['build_number']
    log = open(f"training/data/jenkins/logs/aiops-demo-todo-app/build_{bn}.log",
               encoding='utf-8', errors='replace').read()
    r_anom = requests.post(f"{BASE_URL}/detect_anomaly", json={"log": log}, timeout=30)
    anomaly = r_anom.json()
    
    # 4. Forecast CPU
    with open("training/data/prometheus/cpu_timeseries.csv") as f:
        rows = list(csv.DictReader(f))
    cpu_history = [float(r['cpu_usage']) for r in rows[-60:]]
    r_cpu = requests.post(f"{BASE_URL}/forecast_cpu", json={"cpu_history": cpu_history}, timeout=30)
    predicted_cpu = r_cpu.json()['predicted_cpu']
    
    detail = (f"Build #{bn}: failure_prob={failure_prob:.4f}, "
              f"anomaly_score={anomaly['anomaly_score']:.6f}, "
              f"predicted_cpu={predicted_cpu:.4f}")
    
    # All predictions should be reasonable
    ok = (failure_prob > 0.5 and anomaly['is_anomaly'] and 0 <= predicted_cpu <= 1)
    return ok, detail


if __name__ == "__main__":
    print("=" * 70)
    print("AIOps End-to-End Integration Test")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target: {BASE_URL}")
    print("=" * 70)
    
    # Check orchestrator is running
    print("\n[0] Checking orchestrator connectivity...")
    try:
        requests.get(f"{BASE_URL}/", timeout=5)
        print(f"  {PASS}  Orchestrator reachable\n")
    except requests.ConnectionError:
        print(f"  {FAIL}  Cannot connect to orchestrator at {BASE_URL}")
        print("  Start with: python -m uvicorn orchestrator.main:app --port 8001")
        sys.exit(1)
    
    # Section 1: Data Layer
    print("[1] DATA LAYER")
    test("Training data files exist", test_data_files_exist)
    test("Training data quality", test_training_data_quality)
    test("CPU timeseries quality", test_cpu_timeseries_quality)
    
    # Section 2: Model Layer
    print("\n[2] MODEL LAYER")
    test("All model files exist", test_models_exist)
    test("Evaluation outputs exist", test_evaluation_outputs)
    
    # Section 3: API Layer
    print("\n[3] API LAYER")
    test("Root endpoint", test_orchestrator_root)
    test("Failure prediction (SUCCESS)", test_failure_prediction_success)
    test("Failure prediction (FAILURE)", test_failure_prediction_failure)
    test("Anomaly detection (normal log)", test_anomaly_detection_normal)
    test("Anomaly detection (failure log)", test_anomaly_detection_failure)
    test("CPU forecast", test_cpu_forecast)
    test("Autoscale (no K8s)", test_autoscale_unavailable)
    
    # Section 4: Full Pipeline
    print("\n[4] FULL PIPELINE")
    test("End-to-end pipeline", test_full_pipeline)
    
    # Summary
    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    total = len(results)
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    print("=" * 70)
    
    if failed > 0:
        print("\nFailed tests:")
        for name, status, detail in results:
            if status == FAIL:
                print(f"  - {name}: {detail}")
    
    sys.exit(0 if failed == 0 else 1)
