# NexusOps AI Architecture

This document summarizes the production-style architecture used by NexusOps AI and the major data flows that make the platform demonstrable without requiring external cloud credentials.

## System Architecture

```mermaid
flowchart LR
  User[Platform Engineer] --> Frontend[React + TypeScript Console]
  Frontend --> API[FastAPI API Gateway]
  API --> Services[Domain Service Layer]
  Services --> Repos[Repository Layer]
  Repos --> Postgres[(PostgreSQL)]
  Services --> Redis[(Redis)]
  Services --> Qdrant[(Qdrant Vector DB)]
  Services --> OPA[Open Policy Agent]
  Services --> Prometheus[Prometheus]
  Services --> OTel[OpenTelemetry Collector]
  Services --> LLM[OpenAI or Ollama]
  Workers[Celery Workers] --> Services
  Beat[Celery Beat] --> Workers
  Kubernetes[Kubernetes API] --> Services
  Terraform[Terraform Files + State] --> Services
```

## Infrastructure Discovery Flow

```mermaid
sequenceDiagram
  participant User
  participant API
  participant Provider as InfrastructureProvider
  participant Service as Discovery Service
  participant DB as PostgreSQL

  User->>API: POST /demo/generate or POST /clusters/{id}/sync
  API->>Service: start discovery
  Service->>Provider: discover()
  Provider-->>Service: normalized snapshot
  Service->>DB: upsert clusters, namespaces, workloads, pods, services, nodes
  DB-->>API: persisted topology
  API-->>User: typed cluster/topology response
```

## Observability Flow

```mermaid
flowchart TD
  Sources[Demo, Prometheus, Loki-compatible logs, OTel traces] --> Provider[TelemetryProvider]
  Provider --> TelemetryService[Telemetry Service]
  TelemetryService --> Metrics[(Metric)]
  TelemetryService --> Logs[(LogEntry)]
  TelemetryService --> Events[(InfrastructureEvent)]
  TelemetryService --> Traces[(Trace)]
  Metrics --> API[Telemetry APIs]
  Logs --> API
  Events --> API
  Traces --> API
  API --> UI[Dashboard, Incidents, AI Investigation]
```

## AI Investigation Flow

```mermaid
sequenceDiagram
  participant User
  participant API
  participant InvestigationService
  participant EvidenceCollector
  participant ContextBuilder
  participant LLM as LLM Provider
  participant DB as PostgreSQL

  User->>API: POST /investigations
  API->>InvestigationService: create/run
  InvestigationService->>EvidenceCollector: collect metrics, logs, events, traces
  InvestigationService->>ContextBuilder: build topology + incident context
  InvestigationService->>LLM: analyze context
  LLM-->>InvestigationService: RCA JSON or deterministic fallback
  InvestigationService->>DB: persist investigation and evidence
  API-->>User: root cause, confidence, remediation
```

## Terraform Analysis Flow

```mermaid
flowchart LR
  Upload[Terraform Upload or Demo Project] --> Parser[HCL Parser]
  State[Terraform State] --> Drift[Drift Detector]
  Parser --> Resources[(TerraformResource)]
  Resources --> Rules[Security Rule Engine]
  Resources --> OPA[OPA Policy Evaluation]
  Rules --> Findings[(TerraformFinding)]
  OPA --> Violations[(TerraformPolicyViolation)]
  Drift --> DriftRecords[(TerraformDrift)]
  Findings --> API[Security APIs]
  Violations --> API
  DriftRecords --> API
```

## Cost Optimization Flow

```mermaid
flowchart TD
  Infra[Topology: clusters, workloads, pods, services] --> Snapshots[ResourceUtilization Snapshots]
  Telemetry[Metrics: CPU, memory, restarts, requests] --> Snapshots
  Snapshots --> Rules[Optimization Rules]
  Rules --> Findings[(OptimizationFinding)]
  Findings --> Recommendations[(CostRecommendation)]
  Recommendations --> Report[(OptimizationReport)]
  Report --> UI[Cost Optimization Dashboard]
```

## Design Principles

- Providers normalize external and demo data into the same domain model.
- Services own business workflows; repositories own persistence access.
- APIs return typed Pydantic schemas and keep provider details hidden from the frontend.
- Deterministic fallbacks keep demos functional without OpenAI, Ollama, Kubernetes, or cloud credentials.
- Every incident, finding, recommendation, and telemetry signal remains linkable back to infrastructure resources.
