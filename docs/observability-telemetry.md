# Observability & Telemetry Platform

NexusOps AI Phase 5 adds a provider-neutral telemetry layer for metrics, logs, infrastructure events, and traces.

The telemetry system is designed for future AI incident investigation: every telemetry record can be correlated back to cluster, namespace, deployment, pod, service, and incident context.

## Domain Model

Persistent telemetry tables:

- `telemetry_sources`: registered producers such as demo generation, Prometheus, Loki, or OpenTelemetry.
- `metrics`: historical numeric time series such as CPU, memory, pod restarts, request counts, and error rates.
- `log_entries`: centralized logs with severity, message, source, resource, and trace correlation fields.
- `infrastructure_events`: normalized Kubernetes/platform events such as rollout, restart, and degraded deployment signals.
- `traces`: OpenTelemetry-compatible spans for service path investigation.

## Provider Architecture

Providers emit a shared `TelemetrySnapshot`:

- `DemoTelemetryProvider`: generates realistic telemetry from persisted infrastructure topology.
- `PrometheusProvider`: scaffold for Prometheus query ingestion.
- `OpenTelemetryProvider`: scaffold for OTLP trace ingestion.

APIs and frontend screens consume the same persisted telemetry regardless of provider.

## Demo Telemetry

Use this endpoint to populate a local environment:

```bash
POST /api/v1/demo/telemetry/generate
```

If no infrastructure exists, the service first generates demo infrastructure through the Phase 4 discovery engine, then generates telemetry from that topology.

Generated demo data includes:

- Cluster-level CPU and memory metrics.
- Network throughput, request count, restart, and error-rate metrics.
- Deployment and pod-correlated logs.
- Kubernetes-style rollout, degraded replica, and restart events.
- Simulated distributed traces across frontend, API gateway, auth, workload, and PostgreSQL spans.

## API Surface

Global telemetry:

- `GET /api/v1/metrics`
- `GET /api/v1/logs`
- `GET /api/v1/events`
- `GET /api/v1/traces`
- `GET /api/v1/telemetry/sources`
- `GET /api/v1/telemetry/summary`

Cluster-scoped telemetry:

- `GET /api/v1/clusters/{cluster_id}/metrics`
- `GET /api/v1/clusters/{cluster_id}/logs`
- `GET /api/v1/clusters/{cluster_id}/events`
- `GET /api/v1/clusters/{cluster_id}/traces`

## Frontend

The dashboard now reads telemetry through React Query instead of placeholder observability data.

Displayed telemetry includes:

- CPU and memory charts.
- Restart and error-rate charts.
- Recent logs.
- Recent infrastructure events.
- Trace summaries.
- Telemetry source and record counts.

The dashboard can generate demo telemetry when no telemetry has been ingested.
