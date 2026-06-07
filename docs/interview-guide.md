# Interview Guide

This guide helps explain NexusOps AI during cloud engineering, platform engineering, SRE, backend, and AIOps interviews.

## Why FastAPI?

FastAPI provides typed request and response contracts, OpenAPI documentation, async support, dependency injection, and a clean way to express authentication and RBAC checks. It fits the Python ecosystem used for AI, infrastructure automation, and data workflows.

## Why PostgreSQL?

The platform stores highly relational data: clusters, namespaces, deployments, pods, services, incidents, telemetry summaries, Terraform scans, cost reports, investigations, and audit events. PostgreSQL gives strong consistency, relationships, indexes, migrations, JSON metadata fields, and a clear scaling path.

## Why Provider Abstraction?

Provider abstraction keeps real integrations and demo flows on the same domain model. Kubernetes and demo infrastructure providers feed the same APIs and persistence model. This makes demos credible because the UI exercises real application paths rather than static mock data.

## Why OpenTelemetry?

OpenTelemetry is vendor-neutral and works across traces, metrics, and logs. It aligns with cloud-native operations and allows future export to Grafana, Datadog, cloud providers, or managed observability platforms without redesigning instrumentation.

## How Celery Is Used

Celery supports long-running and scheduled workflows such as discovery syncs, telemetry generation, Terraform analysis, cost analysis, and future provider ingestion. It separates API latency from background processing and allows worker scaling by queue.

## How Infrastructure Discovery Works

Discovery providers read infrastructure resources from Kubernetes or demo scenarios. The service layer normalizes resources into clusters, namespaces, deployments, pods, services, ReplicaSets, and nodes. Repositories persist relationships so topology can be reconstructed for API and UI consumers.

## How AI Investigation Works

The investigation workflow starts from an incident, gathers related infrastructure resources, collects metrics/logs/events/traces, builds a structured context, retrieves relevant history through RAG, and asks an LLM provider or deterministic fallback for root cause, evidence, confidence, and remediation.

## Security Tradeoffs

The project uses JWT bearer tokens, RBAC dependencies, audit events, OPA policies, and production configuration checks. This is strong enough for a portfolio platform. For production SaaS, the next step would be persisted sessions, refresh-token family rotation, OIDC, secure HttpOnly cookies, tenant-aware authorization, and rate limiting.

## Scaling Tradeoffs

The current architecture is intentionally practical: PostgreSQL for source-of-truth records, Redis/Celery for background work, Qdrant for vector search, and telemetry-native tools for observability. At higher scale, raw telemetry should move to specialized stores while PostgreSQL keeps normalized metadata, summaries, and references.

## How To Defend The Architecture

- The project is not a CRUD app; it demonstrates platform workflows across infrastructure, telemetry, AI, security, and cost.
- Demo providers are not shortcuts; they validate the same domain model used by real providers.
- The backend is layered so APIs, services, repositories, schemas, and models have clear responsibilities.
- The UI is API-backed and uses React Query to keep data fetching explicit.
- Security and auditability are present but honestly documented with future production recommendations.
- Scalability is documented as an evolution path rather than speculative overengineering.

## Strong Closing Summary

NexusOps AI shows that I can design and implement cloud platform software that integrates infrastructure discovery, observability, policy analysis, AI workflows, background processing, and enterprise UI patterns while preserving maintainability and clear operational boundaries.
