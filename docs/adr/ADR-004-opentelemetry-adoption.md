# ADR-004: OpenTelemetry Adoption

## Context

The platform must demonstrate observability maturity and future-readiness for distributed systems. It needs trace propagation, metrics, logs, correlation IDs, and integration points for Prometheus, Grafana, Loki, and future production telemetry systems.

## Decision

Adopt OpenTelemetry as the observability instrumentation standard.

OpenTelemetry gives NexusOps AI a vendor-neutral model for traces and metrics while still integrating with common cloud-native tools.

## Alternatives

- **Prometheus-only instrumentation:** strong for metrics, but insufficient for traces and request correlation.
- **Vendor SDKs:** useful in production, but less portable for a portfolio platform.
- **Custom logging only:** simple, but not enough for distributed investigation workflows.

## Consequences

- Trace context can flow across API, worker, provider, and data-layer boundaries.
- Metrics and logs can be correlated with infrastructure resources and incidents.
- Future Datadog, Grafana Cloud, or cloud provider exporters can be added without redesign.
- Instrumentation must be kept consistent to avoid noisy telemetry.
