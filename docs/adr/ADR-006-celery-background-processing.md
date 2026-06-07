# ADR-006: Celery Background Processing

## Context

Infrastructure discovery, telemetry ingestion, Terraform analysis, cost analysis, and AI investigation can be slow or scheduled. These workflows should not depend on synchronous request lifetimes.

## Decision

Use Celery with Redis for background processing and scheduled work.

Celery is mature, familiar in Python systems, supports workers and beat scheduling, and keeps long-running workflows outside request handlers.

## Alternatives

- **FastAPI background tasks:** simple, but tied to web process lifecycle and not suitable for robust scheduled work.
- **Dramatiq/RQ:** simpler queues, but Celery has broader operational familiarity and scheduling features.
- **Kafka-only workers:** useful for event streaming, but too much operational weight for current workflow orchestration.

## Consequences

- Sync jobs and analysis workflows can scale independently from the API.
- Redis keeps the local stack simple.
- Production deployments should configure retries, dead-letter handling, worker autoscaling, and queue-specific concurrency.
