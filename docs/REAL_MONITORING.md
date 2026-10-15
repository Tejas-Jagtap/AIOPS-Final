# Real Prometheus Monitoring for Demo Todo App

This guide explains how to set up and use real Prometheus monitoring for the demo-todo-app.

## Overview

The demo-todo-app now exposes a `/api/metrics` endpoint that returns Prometheus-format metrics, including:

- **http_requests_total** - Counter of total HTTP requests
- **http_request_duration_seconds** - Total request duration in seconds
- **app_todos_total** - Current number of todos
- **app_todos_completed** - Number of completed todos
- **app_errors_total** - Counter of errors
- **app_uptime_seconds** - Application uptime
- **nodejs_memory_heap_used_mb** - Memory usage

## Quick Start

### 1. Start the Demo Todo App

```powershell
cd G:\Mtech-Project\AIOPS\demo-todo-app
npm run dev
```

The app will be available at `http://localhost:3000`

### 2. Verify Metrics Endpoint

Open in browser or use curl:

```
http://localhost:3000/api/metrics
```

You should see Prometheus-format metrics like:

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total 42

# HELP app_todos_total Current number of todos
# TYPE app_todos_total gauge
app_todos_total 5
```

### 3. Start Prometheus (Optional)

If you want to use Prometheus to scrape and store the metrics:

```powershell
cd G:\Mtech-Project\AIOPS\prometheus
docker-compose -f docker-compose-simple.yml up -d
```

Prometheus will be available at `http://localhost:9090`

### 4. Generate Load

Run the load generator to create realistic traffic:

```powershell
cd G:\Mtech-Project\AIOPS
python scripts/load_generator.py
```

This will:

- Create, update, and delete todos
- Generate varied request patterns
- Run for 5 minutes (configurable)

### 5. Collect Metrics for Training

Run the real-time collector to save metrics to CSV:

```powershell
cd G:\Mtech-Project\AIOPS
python collectors/realtime_collector.py --duration 10 --interval 15
```

Options:

- `--duration` - Collection duration in minutes (default: 10)
- `--interval` - Collection interval in seconds (default: 15)

Output will be saved to: `training/data/prometheus/real_app_metrics_<timestamp>.csv`

## Files Created/Modified

### New/Modified App Files

- `demo-todo-app/app/api/metrics/route.ts` - Prometheus metrics endpoint
- `demo-todo-app/app/api/todos/route.ts` - Updated with metrics tracking
- `demo-todo-app/app/api/todos/[id]/route.ts` - Updated with metrics tracking

### New Scripts

- `scripts/load_generator.py` - Generates realistic app traffic
- `collectors/realtime_collector.py` - Collects live metrics to CSV

### Prometheus Configuration

- `prometheus/prometheus-windows.yml` - Updated to scrape demo-todo-app

## Metrics Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Demo Todo App                          │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐  │
│  │ /api/todos  │──▶│   Metrics   │──▶│ /api/metrics │  │
│  │ /api/health │   │   Module    │   │  (Prometheus │  │
│  └─────────────┘   └─────────────┘   │   format)    │  │
│                                       └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │           Prometheus                  │
        │  (scrapes /api/metrics every 15s)    │
        └──────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │     Real-time Collector Script       │
        │  (saves to CSV for LSTM training)    │
        └──────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │     Training Data (CSV)              │
        │  training/data/prometheus/           │
        │  real_app_metrics_*.csv              │
        └──────────────────────────────────────┘
```

## Using Metrics for LSTM Training

The collected CSV files contain timestamped metrics that can be used for:

1. **CPU/Memory Forecasting** - Predict future resource usage
2. **Anomaly Detection** - Detect unusual patterns
3. **Request Load Prediction** - Forecast traffic patterns

Example Python code to load the data:

```python
import pandas as pd

# Load collected metrics
df = pd.read_csv('training/data/prometheus/real_app_metrics_*.csv')

# Convert timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Use for LSTM training
features = ['http_requests_total', 'app_todos_total',
            'nodejs_memory_heap_used_mb', 'app_uptime_seconds']
X = df[features].values
```

## Troubleshooting

### App not responding

```powershell
# Check if port 3000 is in use
netstat -ano | findstr :3000

# Kill existing process
taskkill /PID <pid> /F
```

### Prometheus not connecting

Make sure `host.docker.internal:3000` is accessible from Docker. On some Windows setups, you may need to use your actual IP address instead.

### No metrics data

1. Make sure the app is running: `npm run dev`
2. Access `/api/todos` to generate some metrics
3. Check `/api/metrics` for current values
