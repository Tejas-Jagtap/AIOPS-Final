# Prometheus Setup Guide for AIOps Project

## Quick Start (5 minutes)

### 1. Start Prometheus

Open PowerShell in this folder and run:

```powershell
cd G:\Mtech-Project\AIOPS\prometheus
docker-compose -f docker-compose-simple.yml up -d
```

### 2. Verify It's Running

Open your browser and go to:

- **Prometheus UI**: http://localhost:9090

You should see the Prometheus web interface.

### 3. Test a Query

In the Prometheus UI:

1. Click on "Graph" tab
2. In the query box, type: `up`
3. Click "Execute"
4. You should see `up{job="prometheus"} = 1`

This means Prometheus is monitoring itself!

---

## Understanding Prometheus Metrics

### What are Metrics?

Metrics are numerical measurements collected over time. Examples:

| Metric                     | Description                | Example Value    |
| -------------------------- | -------------------------- | ---------------- |
| `cpu_usage`                | CPU utilization percentage | 0.75 (75%)       |
| `memory_used`              | Memory in bytes            | 1073741824 (1GB) |
| `http_requests_total`      | Total HTTP requests        | 15432            |
| `request_duration_seconds` | How long requests take     | 0.25             |

### Metric Types

1. **Counter**: Only goes up (e.g., total requests)
2. **Gauge**: Can go up or down (e.g., CPU usage, temperature)
3. **Histogram**: Distribution of values (e.g., request durations)

---

## Collecting Metrics for Your AIOps Project

### Option A: Use Prometheus's Own Metrics (Simplest)

Prometheus monitors itself. You can collect:

- `process_cpu_seconds_total` - CPU time used
- `process_resident_memory_bytes` - Memory used
- `prometheus_http_requests_total` - HTTP requests

### Option B: Generate Synthetic Metrics (For Training)

Since you need training data, you can generate realistic CPU metrics:

```powershell
cd G:\Mtech-Project\AIOPS
python training/generate_synthetic_data.py
```

### Option C: Monitor Your Todo App

Add a metrics endpoint to your Next.js app (advanced).

---

## Querying Prometheus from Python

Your `prometheus_collector.py` connects to Prometheus and fetches metrics:

```python
# Example: Fetch CPU metrics
from collectors.prometheus_collector import PrometheusCollector

collector = PrometheusCollector("http://localhost:9090")

# Query CPU usage over last hour
cpu_data = collector.query_range(
    query="process_cpu_seconds_total",
    start="-1h",
    end="now",
    step="15s"
)
```

---

## Useful Prometheus Queries

| Query                                 | What it shows              |
| ------------------------------------- | -------------------------- |
| `up`                                  | Which targets are up/down  |
| `process_cpu_seconds_total`           | CPU time used by processes |
| `process_resident_memory_bytes`       | Memory used                |
| `rate(process_cpu_seconds_total[5m])` | CPU usage rate over 5 min  |
| `prometheus_http_requests_total`      | Total HTTP requests        |

---

## Stopping Prometheus

```powershell
cd G:\Mtech-Project\AIOPS\prometheus
docker-compose -f docker-compose-simple.yml down
```

---

## Troubleshooting

### "Cannot connect to Prometheus"

- Make sure Docker Desktop is running
- Check if container is running: `docker ps`
- Try: `docker-compose -f docker-compose-simple.yml logs`

### "No data in queries"

- Wait 1-2 minutes for Prometheus to collect data
- Check "Status > Targets" in Prometheus UI

---

## Next Steps

1. Start Prometheus (see Quick Start above)
2. Wait 5-10 minutes for data to accumulate
3. Run the Python collector:
   ```powershell
   cd G:\Mtech-Project\AIOPS
   python collectors/prometheus_collector.py
   ```
4. Use the collected data for LSTM training
