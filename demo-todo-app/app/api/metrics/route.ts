import { NextResponse } from "next/server";

// Use globalThis to persist metrics across Next.js dev mode hot reloads
interface MetricsState {
  http_requests_total: number;
  http_request_duration_sum: number;
  http_request_duration_count: number;
  app_todos_total: number;
  app_todos_completed: number;
  app_errors_total: number;
  app_start_time: number;
}

declare global {
  // eslint-disable-next-line no-var
  var __metrics: MetricsState | undefined;
}

// Initialize metrics only once (survives hot reloads)
if (!globalThis.__metrics) {
  globalThis.__metrics = {
    http_requests_total: 0,
    http_request_duration_sum: 0,
    http_request_duration_count: 0,
    app_todos_total: 0,
    app_todos_completed: 0,
    app_errors_total: 0,
    app_start_time: Date.now(),
  };
}

const metrics = globalThis.__metrics;

// Increment request counter (call this from other routes)
export function incrementRequests() {
  metrics.http_requests_total++;
}

export function recordDuration(durationMs: number) {
  metrics.http_request_duration_sum += durationMs;
  metrics.http_request_duration_count++;
}

export function setTodoCount(total: number, completed: number) {
  metrics.app_todos_total = total;
  metrics.app_todos_completed = completed;
}

export function incrementErrors() {
  metrics.app_errors_total++;
}

// GET /api/metrics - Prometheus format
export async function GET() {
  const uptime = (Date.now() - metrics.app_start_time) / 1000;
  const avgDuration =
    metrics.http_request_duration_count > 0
      ? metrics.http_request_duration_sum / metrics.http_request_duration_count
      : 0;

  // Get memory usage (Node.js process)
  const memUsage = process.memoryUsage();

  // Prometheus text format
  const prometheusMetrics = `# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{app="demo-todo-app"} ${metrics.http_requests_total}

# HELP http_request_duration_seconds Average HTTP request duration
# TYPE http_request_duration_seconds gauge
http_request_duration_seconds{app="demo-todo-app"} ${avgDuration / 1000}

# HELP app_todos_total Total number of todos
# TYPE app_todos_total gauge
app_todos_total{app="demo-todo-app"} ${metrics.app_todos_total}

# HELP app_todos_completed Number of completed todos
# TYPE app_todos_completed gauge
app_todos_completed{app="demo-todo-app"} ${metrics.app_todos_completed}

# HELP app_errors_total Total number of errors
# TYPE app_errors_total counter
app_errors_total{app="demo-todo-app"} ${metrics.app_errors_total}

# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds gauge
app_uptime_seconds{app="demo-todo-app"} ${uptime}

# HELP nodejs_memory_heap_used_bytes Node.js heap memory used
# TYPE nodejs_memory_heap_used_bytes gauge
nodejs_memory_heap_used_bytes{app="demo-todo-app"} ${memUsage.heapUsed}

# HELP nodejs_memory_heap_total_bytes Node.js heap memory total
# TYPE nodejs_memory_heap_total_bytes gauge
nodejs_memory_heap_total_bytes{app="demo-todo-app"} ${memUsage.heapTotal}

# HELP nodejs_memory_rss_bytes Node.js RSS memory
# TYPE nodejs_memory_rss_bytes gauge
nodejs_memory_rss_bytes{app="demo-todo-app"} ${memUsage.rss}

# HELP up Application is up
# TYPE up gauge
up{app="demo-todo-app"} 1
`;

  return new NextResponse(prometheusMetrics, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}
