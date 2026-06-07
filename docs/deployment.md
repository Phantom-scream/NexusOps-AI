# Deployment Guide

NexusOps AI supports local Docker Compose development, production container builds, and Kubernetes manifests for platform-style deployment demonstrations.

## Local Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose ps
```

Expected healthy services:

- `api`
- `postgres`
- `redis`
- `opa`
- `otel-collector`

The frontend is available at `http://localhost:3000` and the API docs at `http://localhost:8000/docs`.

## Production Image Validation

```bash
docker build --target production -t nexusops-api:local ./backend
docker build --target production -t nexusops-frontend:local ./frontend
```

## Kubernetes Manifests

Apply the base manifests:

```bash
kubectl apply -f infrastructure/kubernetes/
```

The manifests include:

- frontend and backend Deployments
- API and frontend Services
- an nginx Ingress example
- API ServiceAccount and read-only Kubernetes discovery RBAC
- a demo `nexusops-secrets` Secret with placeholder values

Remove them:

```bash
kubectl delete -f infrastructure/kubernetes/
```

## Required Configuration

Set these values for real environments:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `OPENAI_API_KEY` or `LLM_PROVIDER=ollama`
- `QDRANT_HOST`
- `OPA_SERVER_URL`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `KUBECONFIG_PATH` or in-cluster Kubernetes service account access

For Kubernetes deployments, replace the placeholder values in `infrastructure/kubernetes/secrets.yaml` before applying to a shared or production cluster.

## Release Gate

Before publishing a demo or release:

```bash
docker compose config --quiet
docker compose exec api alembic upgrade head
docker compose exec api ruff check app tests
docker compose exec api pytest -q
cd frontend && npm run lint && npm run test && npm run build
```

## Notes

- Alembic owns application schema migrations.
- PostgreSQL init scripts are limited to database-level bootstrap hooks.
- Demo providers keep the platform usable when Kubernetes, cloud providers, or LLM keys are unavailable.
