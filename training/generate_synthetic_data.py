"""
Synthetic Data Generator for AIOps Training
============================================
Generates realistic CI/CD build data, log files, and CPU timeseries
for training ML models when real data is insufficient.

Author: AIOps Project
"""

import os
import csv
import random
import math
import numpy as np
from datetime import datetime, timedelta


# ─────────────────────────────────────────────────────────────────
# 1. SYNTHETIC JENKINS BUILD DATA
# ─────────────────────────────────────────────────────────────────

def generate_jenkins_builds(
    n_builds: int = 600,
    failure_rate: float = 0.25,
    unstable_rate: float = 0.08,
    output_path: str = "training/data/jenkins/all_builds.csv",
    seed: int = 42
):
    """
    Generate realistic Jenkins build records.
    
    Distribution of results:
      - SUCCESS  ~67%
      - FAILURE  ~25%
      - UNSTABLE ~8%
    
    Feature correlations designed for meaningful ML training:
      - Failures have: longer duration, more errors/warnings, more test failures
      - Unstable builds: some test failures, moderate warnings
      - Success builds: short duration, low errors, no test failures
    """
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)
    
    builds = []
    base_time = datetime(2025, 1, 1, 8, 0, 0)
    
    for i in range(1, n_builds + 1):
        # Determine build result
        roll = rng.random()
        if roll < failure_rate:
            result = "FAILURE"
        elif roll < failure_rate + unstable_rate:
            result = "UNSTABLE"
        else:
            result = "SUCCESS"
        
        # --- Duration (seconds) ---
        if result == "SUCCESS":
            duration = max(15, np_rng.normal(65, 30))
        elif result == "UNSTABLE":
            duration = max(20, np_rng.normal(85, 35))
        else:  # FAILURE
            # Some failures are fast (early abort) some are long (timeout)
            if rng.random() < 0.3:
                duration = max(5, np_rng.normal(25, 15))   # early abort
            else:
                duration = max(30, np_rng.normal(120, 45)) # long failures
        duration = round(duration, 3)
        
        # --- Tests ---
        total_tests = 24  # matching the real project
        if result == "SUCCESS":
            # Most successes pass all, but some have 0 test failures with flaky runs
            tests_failed = 0 if rng.random() < 0.85 else rng.randint(0, 1)
            tests_passed = total_tests - tests_failed
        elif result == "UNSTABLE":
            tests_failed = rng.randint(1, 5)
            tests_passed = total_tests - tests_failed
        else:  # FAILURE
            if rng.random() < 0.35:
                # Build failed before tests ran
                tests_failed = 0
                tests_passed = 0
                total_tests = 0
            else:
                tests_failed = rng.randint(2, 12)
                tests_passed = max(0, total_tests - tests_failed)
        tests_skipped = 0
        
        # --- Warnings --- (overlap between classes for realism)
        if result == "SUCCESS":
            warnings = rng.choices([0, 1, 2, 3, 4, 5], weights=[20, 35, 20, 12, 8, 5])[0]
        elif result == "UNSTABLE":
            warnings = rng.randint(1, 8)
        else:
            warnings = rng.randint(1, 12)
        
        # --- Errors --- (some overlap for realistic separation)
        if result == "SUCCESS":
            errors = rng.choices([0, 1, 2, 3], weights=[30, 45, 15, 10])[0]
        elif result == "UNSTABLE":
            errors = rng.randint(1, 6)
        else:
            errors = rng.randint(2, 20)
        
        # --- Failures (build step failures) --- with overlap for realism
        if result == "SUCCESS":
            failures = rng.choices([0, 1], weights=[92, 8])[0]  # rare false alarm
        elif result == "UNSTABLE":
            failures = rng.choices([0, 1, 2], weights=[40, 40, 20])[0]
        else:
            failures = rng.choices([0, 1, 2, 3, 4], weights=[10, 30, 30, 20, 10])[0]
        
        # --- Log length --- (overlapping distributions)
        if result == "SUCCESS":
            log_length = int(max(5000, np_rng.normal(16000, 3000)))
        elif result == "UNSTABLE":
            log_length = int(max(8000, np_rng.normal(19000, 4000)))
        else:
            if tests_failed == 0 and tests_passed == 0:
                log_length = int(max(1000, np_rng.normal(6000, 3000)))
            else:
                log_length = int(max(10000, np_rng.normal(22000, 5000)))
        
        # --- Timestamp ---
        time_offset = timedelta(minutes=rng.randint(3, 10) * i)
        timestamp = base_time + time_offset
        ts_epoch = timestamp.timestamp()
        
        # --- URL ---
        url = f"http://localhost:8080/job/aiops-demo-todo-app/{i}/"
        
        builds.append({
            "job_name": "aiops-demo-todo-app",
            "build_number": i,
            "result": result,
            "duration": duration,
            "timestamp": ts_epoch,
            "url": url,
            "tests_failed": float(tests_failed),
            "tests_passed": float(tests_passed),
            "tests_skipped": float(tests_skipped),
            "tests_total": float(tests_failed + tests_passed + tests_skipped),
            "warnings": warnings,
            "errors": errors,
            "failures": failures,
            "log_length": log_length,
        })
    
    # Write CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = list(builds[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(builds)
    
    # Summary
    results_count = {}
    for b in builds:
        results_count[b["result"]] = results_count.get(b["result"], 0) + 1
    
    print(f"Generated {n_builds} synthetic Jenkins builds → {output_path}")
    for k, v in sorted(results_count.items()):
        print(f"  {k}: {v} ({v/n_builds*100:.1f}%)")
    
    return builds


# ─────────────────────────────────────────────────────────────────
# 2. SYNTHETIC LOG FILES
# ─────────────────────────────────────────────────────────────────

# Templates for realistic Jenkins console log snippets
SUCCESS_LOG_TEMPLATE = """Started by user admin
Running as SYSTEM
Building in workspace /var/jenkins_home/workspace/aiops-demo-todo-app
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in /var/jenkins_home/workspace/aiops-demo-todo-app
[Pipeline] {{
[Pipeline] stage
[Pipeline] {{ (Checkout)
[Pipeline] checkout scm
Cloning the remote Git repository
Cloning repository https://github.com/Tejas-Jagtap/aiops-demo-todo-app.git
Fetching upstream changes from https://github.com/Tejas-Jagtap/aiops-demo-todo-app.git
Checking out Revision {commit_hash}
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Install Dependencies)
npm warn deprecated inflight@1.0.6
npm warn deprecated glob@7.2.3
added 350 packages in {install_time}s
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Lint)
✔ No ESLint warnings or errors
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Test)
PASS src/__tests__/TodoList.test.tsx
PASS src/__tests__/api/todos.test.ts
Test Suites: 2 passed, 2 total
Tests:       24 passed, 24 total
Snapshots:   0 total
Time:        {test_time}s
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Build)
Creating an optimized production build...
Compiled successfully.
Route (app)                              Size     First Load JS
┌ ○ /                                    5.24 kB        89.2 kB
├ ○ /api/metrics                         0 B                0 B
└ ○ /api/todos                           0 B                0 B
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Archive)
Archiving artifacts
[Pipeline] }}
[Pipeline] }}
[Pipeline] End of Pipeline
Finished: SUCCESS
"""

FAILURE_LOG_TEMPLATE = """Started by user admin
Running as SYSTEM
Building in workspace /var/jenkins_home/workspace/aiops-demo-todo-app
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in /var/jenkins_home/workspace/aiops-demo-todo-app
[Pipeline] {{
[Pipeline] stage
[Pipeline] {{ (Checkout)
[Pipeline] checkout scm
Cloning repository https://github.com/Tejas-Jagtap/aiops-demo-todo-app.git
{checkout_error}
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Install Dependencies)
npm warn deprecated inflight@1.0.6
{install_error}
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
npm ERR! Found: react@{react_version}
npm ERR! Could not resolve dependency:
npm ERR! peer react@"^17.0.0" from some-package@1.0.0
ERROR: npm install failed with exit code {exit_code}
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Lint)
ERROR: ESLint found {lint_errors} error(s) and {lint_warnings} warning(s)
./src/components/TodoList.tsx
  Line {line1}:{col1}  Error: '{var1}' is defined but never used  no-unused-vars
  Line {line2}:{col2}  Error: Missing return type on function  @typescript-eslint/explicit-function-return-type
  Line {line3}:{col3}  Warning: Unexpected console statement  no-console
{extra_lint}
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Test)
FAIL src/__tests__/TodoList.test.tsx
  ● TodoList > should render todo items
    TypeError: Cannot read properties of undefined (reading 'map')
      at TodoList (/var/jenkins_home/workspace/aiops-demo-todo-app/src/components/TodoList.tsx:{err_line}:25)

FAIL src/__tests__/api/todos.test.ts
  ● API > POST /api/todos > should create a todo
    Expected status code 201, received 500
    Error: Internal Server Error
      at Object.<anonymous> (/var/jenkins_home/workspace/aiops-demo-todo-app/src/__tests__/api/todos.test.ts:45:19)

Test Suites: 2 failed, 2 total
Tests:       {tests_failed} failed, {tests_passed} passed, {tests_total} total
Time:        {test_time}s

ERROR: Build FAILURE - test stage failed
java.lang.Exception: Build failed due to test failures
    at org.jenkinsci.plugins.workflow.steps.ErrorStep$Execution.run(ErrorStep.java:64)
[Pipeline] }}
[Pipeline] End of Pipeline
ERROR: script returned exit code 1
Finished: FAILURE
"""

UNSTABLE_LOG_TEMPLATE = """Started by user admin
Running as SYSTEM
Building in workspace /var/jenkins_home/workspace/aiops-demo-todo-app
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in /var/jenkins_home/workspace/aiops-demo-todo-app
[Pipeline] {{
[Pipeline] stage
[Pipeline] {{ (Checkout)
[Pipeline] checkout scm
Cloning repository https://github.com/Tejas-Jagtap/aiops-demo-todo-app.git
Checking out Revision {commit_hash}
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Install Dependencies)
npm warn deprecated inflight@1.0.6
npm warn deprecated glob@7.2.3
added 350 packages in {install_time}s
2 moderate severity vulnerabilities
To address all issues, run: npm audit fix
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Lint)
WARNING: ESLint found 0 error(s) and {lint_warnings} warning(s)
./src/components/TodoList.tsx
  Line 15:5  Warning: Unexpected console statement  no-console
  Line 28:3  Warning: React Hook useEffect has missing dependencies  react-hooks/exhaustive-deps
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Test)
PASS src/__tests__/TodoList.test.tsx
FAIL src/__tests__/api/todos.test.ts
  ● API > DELETE /api/todos > should handle non-existent todo
    Expected: 404
    Received: 200

Test Suites: 1 failed, 1 passed, 2 total
Tests:       {tests_failed} failed, {tests_passed} passed, {tests_total} total
Snapshots:   0 total
Time:        {test_time}s
[Pipeline] }}
[Pipeline] stage
[Pipeline] {{ (Build)
Creating an optimized production build...
Compiled with warnings.
WARNING: Some chunks are larger than recommended size
[Pipeline] }}
[Pipeline] }}
[Pipeline] End of Pipeline
Finished: UNSTABLE
"""


def _random_commit_hash(rng):
    return ''.join(rng.choices('0123456789abcdef', k=40))


def generate_synthetic_logs(
    builds: list,
    output_dir: str = "training/data/jenkins/logs/aiops-demo-todo-app",
    seed: int = 42
):
    """
    Generate synthetic Jenkins console logs for each build.
    Log content correlates with build result for meaningful anomaly detection.
    """
    rng = random.Random(seed)
    os.makedirs(output_dir, exist_ok=True)
    
    normal_count = 0
    anomaly_count = 0
    
    for build in builds:
        build_num = build["build_number"]
        result = build["result"]
        filename = f"build_{build_num}.log"
        filepath = os.path.join(output_dir, filename)
        
        ch = _random_commit_hash(rng)
        
        if result == "SUCCESS":
            log_text = SUCCESS_LOG_TEMPLATE.format(
                commit_hash=ch,
                install_time=rng.randint(8, 25),
                test_time=round(rng.uniform(3.0, 12.0), 1),
            )
            normal_count += 1
            
        elif result == "FAILURE":
            checkout_err = rng.choice([
                "ERROR: Error cloning remote repo",
                f"Checking out Revision {ch}",
                "WARNING: timeout during git fetch",
            ])
            install_err = rng.choice([
                "npm ERR! peer dep missing: typescript@^5.0.0",
                "npm ERR! ENOENT: no such file or directory, open 'package.json'",
                "",
            ])
            extra_lint = rng.choice([
                "  Line 55:10  Error: 'response' is not defined  no-undef\n  Line 72:1  Error: Parsing error: Unexpected token",
                "",
                "  Line 99:5  Error: Do not use 'any' as a type  @typescript-eslint/no-explicit-any",
            ])
            
            tf = int(build["tests_failed"])
            tp = int(build["tests_passed"])
            tt = int(build["tests_total"])
            if tt == 0:
                tf, tp, tt = rng.randint(3, 8), rng.randint(5, 15), 24
                tp = tt - tf
            
            log_text = FAILURE_LOG_TEMPLATE.format(
                commit_hash=ch,
                checkout_error=checkout_err,
                install_error=install_err,
                react_version=rng.choice(["17.0.2", "18.2.0", "19.0.0-rc.1"]),
                exit_code=rng.choice([1, 2, 127]),
                lint_errors=rng.randint(2, 10),
                lint_warnings=rng.randint(1, 5),
                line1=rng.randint(5, 50),  col1=rng.randint(1, 30),
                var1=rng.choice(["unused", "temp", "data", "result"]),
                line2=rng.randint(10, 80), col2=rng.randint(1, 20),
                line3=rng.randint(15, 90), col3=rng.randint(1, 15),
                extra_lint=extra_lint,
                err_line=rng.randint(10, 60),
                tests_failed=tf, tests_passed=tp, tests_total=tt,
                test_time=round(rng.uniform(5.0, 20.0), 1),
            )
            anomaly_count += 1
            
        else:  # UNSTABLE
            tf = int(build["tests_failed"])
            tp = int(build["tests_passed"])
            tt = int(build["tests_total"])
            
            log_text = UNSTABLE_LOG_TEMPLATE.format(
                commit_hash=ch,
                install_time=rng.randint(8, 25),
                lint_warnings=rng.randint(2, 6),
                tests_failed=tf, tests_passed=tp, tests_total=tt,
                test_time=round(rng.uniform(4.0, 15.0), 1),
            )
            anomaly_count += 1
        
        # Add some random noise lines to vary log length
        extra_lines = rng.randint(5, 50)
        noise_lines = []
        for _ in range(extra_lines):
            if result == "SUCCESS":
                noise_lines.append(rng.choice([
                    "[Pipeline] echo",
                    f"> aiops-demo-todo-app@0.1.0 build",
                    f"[INFO] Build step completed in {rng.randint(1,30)}s",
                    f"  {rng.randint(15,25)} passing ({rng.randint(1,12)}s)",
                    "info: No vulnerabilities found",
                    "Build completed successfully",
                    f"[Pipeline] archiveArtifacts",
                    f"Compressing {rng.randint(50,200)} files",
                    "All stages passed",
                    f"Coverage: {rng.randint(75,95)}% Statements",
                    "✓ lint passed",
                    "✓ test passed",
                    "✓ build passed",
                    f"npm run build exited with code 0",
                    f"Duration: {rng.randint(20,120)}s",
                ]))
            elif result == "FAILURE":
                noise_lines.append(rng.choice([
                    f"FATAL: Build step failed with exit code {rng.randint(1,255)}",
                    f"ERROR: Process exited with non-zero status {rng.choice([1,2,127,137,139])}",
                    "Build was aborted due to errors",
                    f"npm ERR! errno {rng.randint(1,255)}",
                    "FAILURE in pipeline execution",
                    f"java.lang.OutOfMemoryError: Java heap space",
                    f"ERROR: OOM killer terminated process",
                    f"CRITICAL: Timeout after {rng.randint(300,900)}s",
                    f"ERROR: Unable to connect to database server",
                    f"FATAL: Docker daemon not responding",
                    f"BUILD FAILURE at stage {rng.choice(['test', 'lint', 'build', 'deploy'])}",
                    f"stack trace: NullPointerException at line {rng.randint(1,300)}",
                    "segmentation fault (core dumped)",
                    f"ERROR: Connection refused to port {rng.choice([3000,5432,8080,6379])}",
                    f"PANIC: unrecoverable error in module {rng.choice(['auth','db','api','cache'])}",
                ]))
            else:  # UNSTABLE
                noise_lines.append(rng.choice([
                    f"WARNING: Deprecated API usage detected",
                    f"WARN: {rng.randint(1,10)} security vulnerabilities found",
                    f"WARNING: Coverage below threshold: {rng.randint(40,70)}%",
                    f"WARN: Flaky test detected: test_{rng.randint(1,24)}",
                    "Unstable build - some tests were skipped",
                    f"WARNING: Memory usage at {rng.randint(75,95)}%",
                    f"WARN: Response time exceeded {rng.randint(2,10)}s threshold",
                    f"WARNING: Package {rng.choice(['lodash','axios','react'])} has known vulnerability",
                    "Build succeeded with warnings",
                    f"[WARN] {rng.randint(1,5)} deprecated dependencies found",
                ]))
        
        log_text += '\n'.join(noise_lines) + '\n'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(log_text)
    
    print(f"Generated {len(builds)} synthetic log files → {output_dir}")
    print(f"  Normal (SUCCESS): {normal_count}")
    print(f"  Anomaly (FAILURE/UNSTABLE): {anomaly_count}")


# ─────────────────────────────────────────────────────────────────
# 3. SYNTHETIC CPU TIMESERIES
# ─────────────────────────────────────────────────────────────────

def generate_cpu_timeseries(
    n_points: int = 10080,  # 7 days at 1-min intervals
    output_path: str = "training/data/prometheus/cpu_timeseries.csv",
    seed: int = 42
):
    """
    Generate realistic CPU timeseries data with:
      - Daily patterns (higher during business hours)
      - Weekly patterns (lower on weekends)
      - Random spikes (simulating load bursts)
      - Gradual trends
    """
    np_rng = np.random.RandomState(seed)
    
    start = datetime(2025, 1, 1, 0, 0, 0)
    timestamps = [start + timedelta(minutes=i) for i in range(n_points)]
    
    cpu_values = []
    for i, ts in enumerate(timestamps):
        hour = ts.hour
        dow = ts.weekday()  # 0=Mon, 6=Sun
        minute_of_day = hour * 60 + ts.minute
        is_weekend = dow >= 5
        
        # Base CPU: ~0.25
        base = 0.25
        
        # Daily pattern: peak 9am–5pm
        daily = 0.20 * math.exp(-0.5 * ((hour - 13) / 4) ** 2)
        
        # Weekend reduction
        if is_weekend:
            daily *= 0.4
        
        # Weekly trend: slight midweek rise
        weekly = 0.05 * math.exp(-0.5 * ((dow - 2) / 1.5) ** 2)
        
        # Random noise
        noise = np_rng.normal(0, 0.04)
        
        # Random spikes (~3% of time)
        spike = 0
        if np_rng.random() < 0.03:
            spike = np_rng.uniform(0.15, 0.40)
        
        # Gradual upward trend over the week
        trend = 0.02 * (i / n_points)
        
        cpu = base + daily + weekly + noise + spike + trend
        cpu = max(0.01, min(0.99, cpu))
        
        cpu_values.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_usage": round(cpu, 6),
            "hour": hour,
            "day_of_week": dow,
            "is_weekend": is_weekend,
            "minute_of_day": minute_of_day,
        })
    
    # Write CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = list(cpu_values[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cpu_values)
    
    vals = [c["cpu_usage"] for c in cpu_values]
    print(f"Generated {n_points} CPU timeseries points → {output_path}")
    print(f"  Range: [{min(vals):.3f}, {max(vals):.3f}]")
    print(f"  Mean:  {np.mean(vals):.3f}")
    print(f"  Std:   {np.std(vals):.3f}")


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AIOps Synthetic Data Generation")
    print("=" * 60)
    
    # 1. Generate Jenkins builds
    print("\n--- Step 1: Jenkins Build Data ---")
    builds = generate_jenkins_builds(n_builds=600)
    
    # 2. Generate log files for those builds
    print("\n--- Step 2: Jenkins Log Files ---")
    generate_synthetic_logs(builds)
    
    # 3. Generate CPU timeseries (for LSTM training)
    print("\n--- Step 3: CPU Timeseries ---")
    generate_cpu_timeseries()
    
    print("\n" + "=" * 60)
    print("All synthetic data generated successfully!")
    print("=" * 60)
