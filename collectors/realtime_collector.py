"""
Real-Time App Metrics Collector
Collects live metrics from the demo-todo-app for LSTM training
"""

import requests
import csv
import time
import os
from datetime import datetime
from pathlib import Path

# Configuration
APP_METRICS_URL = "http://localhost:3000/api/metrics"
PROMETHEUS_URL = "http://localhost:9090"
OUTPUT_DIR = Path("G:/Mtech-Project/AIOPS/training/data/prometheus")

def parse_prometheus_metrics(text):
    """Parse Prometheus text format into a dictionary"""
    metrics = {}
    for line in text.strip().split('\n'):
        if line.startswith('#') or not line.strip():
            continue
        try:
            # Handle metrics with labels
            if '{' in line:
                metric_name = line.split('{')[0]
                value = float(line.split()[-1])
                label_part = line.split('{')[1].split('}')[0]
                full_name = f"{metric_name}_{label_part.replace('=', '_').replace('\"', '')}"
                metrics[full_name] = value
            else:
                parts = line.split()
                if len(parts) >= 2:
                    metric_name = parts[0]
                    value = float(parts[1])
                    metrics[metric_name] = value
        except (ValueError, IndexError):
            continue
    return metrics


def collect_from_app():
    """Collect metrics directly from the app's /api/metrics endpoint"""
    try:
        response = requests.get(APP_METRICS_URL, timeout=5)
        if response.status_code == 200:
            return parse_prometheus_metrics(response.text)
    except Exception as e:
        print(f"Error collecting from app: {e}")
    return {}


def collect_from_prometheus(query):
    """Query Prometheus for a specific metric"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={'query': query},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                results = data.get('data', {}).get('result', [])
                if results:
                    return float(results[0]['value'][1])
    except Exception as e:
        pass
    return None


def collect_metrics():
    """Collect all available metrics"""
    timestamp = datetime.now().isoformat()
    
    # Get app metrics
    app_metrics = collect_from_app()
    
    # Combine all metrics
    all_metrics = {
        'timestamp': timestamp,
        **app_metrics
    }
    
    return all_metrics


def run_collector(duration_minutes=10, interval_seconds=15):
    """
    Run the metrics collector for a specified duration
    """
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Output file with timestamp
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"real_app_metrics_{timestamp_str}.csv"
    
    print("="*60)
    print("📊 REAL-TIME APP METRICS COLLECTOR")
    print("="*60)
    print(f"App Metrics URL: {APP_METRICS_URL}")
    print(f"Collection Interval: {interval_seconds}s")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Output File: {output_file}")
    print("="*60)
    
    # Check if app is accessible
    try:
        response = requests.get(APP_METRICS_URL, timeout=5)
        if response.status_code == 200:
            print("✅ App metrics endpoint is accessible")
            print("\nInitial metrics:")
            metrics = parse_prometheus_metrics(response.text)
            for key, value in sorted(metrics.items()):
                print(f"   {key}: {value}")
        else:
            print(f"⚠️  App returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to app: {e}")
        print("\n   Make sure the demo-todo-app is running:")
        print("   cd demo-todo-app && npm run dev")
        return
    
    print("\n🚀 Starting collection... (Press Ctrl+C to stop)\n")
    
    end_time = time.time() + (duration_minutes * 60)
    samples_collected = 0
    all_data = []
    all_columns = set()
    
    try:
        while time.time() < end_time:
            metrics = collect_metrics()
            
            if metrics:
                all_data.append(metrics)
                all_columns.update(metrics.keys())
                samples_collected += 1
                
                # Print progress
                http_requests = metrics.get('http_requests_total', 0)
                http_errors = metrics.get('app_errors_total', 0)
                todos = metrics.get('app_todos_total', 0)
                uptime = metrics.get('app_uptime_seconds', 0)
                memory = metrics.get('nodejs_memory_heap_used_mb', 0)
                
                print(f"[{samples_collected}] Requests: {http_requests}, "
                      f"Errors: {http_errors}, "
                      f"Todos: {todos}, "
                      f"Memory: {memory:.1f}MB, "
                      f"Uptime: {uptime:.0f}s")
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection stopped by user")
    
    # Write collected data to CSV
    if all_data:
        # Sort columns for consistent ordering
        columns = sorted(list(all_columns))
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in all_data:
                # Fill missing values with 0
                filled_row = {col: row.get(col, 0) for col in columns}
                writer.writerow(filled_row)
        
        print("\n" + "="*60)
        print("📊 COLLECTION SUMMARY")
        print("="*60)
        print(f"   Samples Collected: {samples_collected}")
        print(f"   Metrics per Sample: {len(columns)}")
        print(f"   Output File: {output_file}")
        print("\n   Metrics collected:")
        for col in sorted(columns):
            if col != 'timestamp':
                print(f"   - {col}")
        print("="*60)
    else:
        print("\n❌ No metrics collected")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect real app metrics')
    parser.add_argument('--duration', type=int, default=10,
                        help='Collection duration in minutes (default: 10)')
    parser.add_argument('--interval', type=int, default=15,
                        help='Collection interval in seconds (default: 15)')
    
    args = parser.parse_args()
    
    run_collector(
        duration_minutes=args.duration,
        interval_seconds=args.interval
    )
