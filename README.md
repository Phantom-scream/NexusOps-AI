# NexusOps AI

> **Enterprise-Grade AI-Powered Multi-Cloud AIOps & Infrastructure Intelligence Platform**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-red.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-compatible-326CE5.svg)](https://kubernetes.io)

---

## Overview

NexusOps AI is a production-grade AIOps platform that brings together Kubernetes infrastructure intelligence, AI-driven incident investigation, security compliance scanning, and cost optimization into a unified observability experience — purpose-built for cloud-native engineering teams.

Inspired by platforms like Datadog, IBM Cloud Pak for Watson AIOps, and Red Hat Advanced Cluster Management, NexusOps AI is designed for engineering teams operating at scale across multi-cluster, multi-cloud environments.

---

## Core Capabilities

| Module | Description |
|---|---|
| **Infrastructure Discovery** | Real-time Kubernetes cluster ingestion, topology mapping, resource inventory |
| **Observability Pipeline** | OpenTelemetry-based log/metric/trace ingestion with event normalization |
| **AI Incident Investigation** | LLM-powered root cause analysis, failure correlation, remediation generation |
| **Terraform Security Analysis** | Drift detection, IAM/RBAC risk scanning, OPA policy evaluation |
| **Cost Optimization Engine** | Resource utilization analysis, overprovisioning detection, savings recommendations |
| **AI Remediation Engine** | Kubernetes YAML patch generation, Terraform fix suggestions, PR abstraction |
| **RAG Infrastructure Intelligence** | Vector-indexed manifests, logs, incidents for semantic infrastructure Q&A |
| **Real-time Dashboard** | WebSocket-powered cluster/incident/security/cost dashboards |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NexusOps AI Platform                      │
├──────────────────────────────────┬──────────────────────────────┤
│           Frontend (React)        │      API Gateway (FastAPI)   │
│   Dashboard / Topology / Chat     │   REST + WebSocket + OpenAPI │
├──────────────────────────────────┴──────────────────────────────┤
│                          Service Layer                            │
│  ClusterSvc │ IncidentSvc │ SecuritySvc │ CostSvc │ AI Engine    │
├─────────────────────────────────────────────────────────────────┤
│                        Data & Event Layer                         │
│  PostgreSQL │ Redis │ Qdrant │ Kafka/Redpanda │ OpenTelemetry   │
├─────────────────────────────────────────────────────────────────┤
│                     Infrastructure Layer                          │
│  Kubernetes API │ Terraform Parser │ Trivy │ OPA │ LLM Backends  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

**Frontend:** React 18, TypeScript, Vite, TailwindCSS, React Query, Zustand, Recharts, Framer Motion

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Celery, asyncio

**Databases:** PostgreSQL 16, Redis 7, Qdrant (Vector DB)

**AI Stack:** LangChain, OpenAI API, Ollama (local LLM), RAG pipelines, text-embedding-ada-002

**Event Streaming:** Redpanda (Kafka-compatible)

**Observability:** OpenTelemetry, Prometheus, Grafana, Loki

**Security:** Trivy, Open Policy Agent (OPA)

**Infrastructure:** Docker, Docker Compose, Kubernetes, Helm, Terraform

**CI/CD:** GitHub Actions

---

## Quick Start

### Prerequisites

- Docker 24+
- Docker Compose v2
- Node.js 20+
- Python 3.12+
- An OpenAI API key (or Ollama for local LLMs)

### 1. Clone & Configure

```bash
git clone https://github.com/Phantom-scream/NexusOps-AI.git
cd NexusOps-AI
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 2. Start Full Stack (Docker)

```bash
make dev
# or
docker compose up -d
```

### 3. Access Services

| Service | URL |
|---|---|
| Frontend Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
| Qdrant UI | http://localhost:6333/dashboard |

### 4. Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
nexusops-ai/
├── backend/                    # FastAPI backend service
│   ├── app/
│   │   ├── api/v1/             # REST API routes
│   │   ├── core/               # Config, DB, security, logging
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic layer
│   │   ├── repositories/       # Data access layer
│   │   ├── ai/                 # LLM clients, RAG, prompt templates
│   │   ├── workers/            # Celery async tasks
│   │   ├── infrastructure/     # Kubernetes client, Terraform parser
│   │   ├── security/           # Trivy, OPA integrations
│   │   ├── observability/      # OTel metrics, tracing, logging
│   │   └── events/             # Kafka/Redpanda event streaming
│   └── tests/
├── frontend/                   # React TypeScript frontend
│   └── src/
│       ├── components/         # Reusable UI components
│       ├── pages/              # Page-level route components
│       ├── services/           # API clients
│       ├── hooks/              # Custom React hooks
│       ├── stores/             # Zustand state stores
│       └── types/              # TypeScript type definitions
├── infrastructure/
│   ├── kubernetes/             # K8s manifests
│   ├── helm/                   # Helm charts
│   └── terraform/              # Terraform templates
├── docs/                       # Architecture & API documentation
├── scripts/                    # Utility scripts
└── .github/workflows/          # CI/CD pipelines
```

---

## AI Investigation Example

```bash
# Query the AI investigation engine
curl -X POST http://localhost:8000/api/v1/ai/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "cluster_id": "prod-cluster-01",
    "query": "Why is the payments-service pod crashing repeatedly?",
    "context_window_minutes": 60
  }'
```

Response:

```json
{
  "incident_id": "inc-2024-001",
  "severity": "critical",
  "root_cause": "OOMKilled due to memory leak in payments-service v2.3.1...",
  "contributing_factors": ["Recent deployment at 14:32 UTC", "Redis connection pool exhaustion"],
  "remediation": {
    "immediate": "kubectl rollout undo deployment/payments-service",
    "long_term": "Set memory limits to 512Mi, investigate connection pooling"
  },
  "confidence": 0.87
}
```

---

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Infrastructure Discovery](docs/infrastructure-discovery.md)
- [Observability & Telemetry](docs/observability-telemetry.md)
- [API Reference](docs/api.md)
- [Developer Onboarding](docs/onboarding.md)
- [Deployment Guide](docs/deployment.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## License

MIT — see [LICENSE](LICENSE) for details.
