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

Local service endpoints:

| Service | URL |
|---|---|
| Frontend dashboard | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| API documentation | `http://localhost:8000/docs` |
| Grafana | `http://localhost:3001` |
| Prometheus | `http://localhost:9090` |
| Qdrant UI | `http://localhost:6333/dashboard` |

## Demo Data Workflow

After registering and logging in, use the UI demo actions or call the demo APIs with an access token:

```bash
TOKEN="<access-token-from-login>"

curl -H "Authorization: Bearer $TOKEN" -X POST http://localhost:8000/api/v1/demo/generate
curl -H "Authorization: Bearer $TOKEN" -X POST http://localhost:8000/api/v1/demo/telemetry/generate
curl -H "Authorization: Bearer $TOKEN" -X POST http://localhost:8000/api/v1/demo/incidents/generate
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/v1/terraform/analyze -d '{"demo":true}'
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/v1/optimization/analyze -d '{"demo":true}'
```

Development registrations receive the configured development role so local demos can run protected workflows. Production registrations default to Viewer unless explicitly configured otherwise.

## Production Image Validation

```bash
docker build --target production -t nexusops-api:local ./backend
docker build --target production -t nexusops-frontend:local ./frontend
```

## Production Hardening Notes

- Replace local fallback passwords with environment-specific secrets.
- Use a secret manager or Kubernetes Secrets managed by your deployment pipeline.
- Pin third-party service images to tested version tags or immutable digests before production use.
- Avoid mounting broad kubeconfigs into containers; prefer least-privilege service accounts.
- Keep OpenTelemetry, OPA, Grafana, Prometheus, Loki, Qdrant, and Redpanda versions upgraded through a controlled validation process.

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
