# API Reference

Interactive OpenAPI documentation is available at `http://localhost:8000/docs` when the backend is running.

## Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

Most platform APIs require a bearer token.

## Infrastructure

- `GET /api/v1/clusters`
- `GET /api/v1/clusters/{id}`
- `GET /api/v1/clusters/{id}/namespaces`
- `GET /api/v1/clusters/{id}/deployments`
- `GET /api/v1/clusters/{id}/pods`
- `GET /api/v1/clusters/{id}/services`
- `GET /api/v1/clusters/{id}/topology`
- `POST /api/v1/clusters/{id}/sync`
- `POST /api/v1/demo/generate`

## Telemetry

- `GET /api/v1/metrics`
- `GET /api/v1/logs`
- `GET /api/v1/events`
- `GET /api/v1/traces`
- `GET /api/v1/clusters/{id}/metrics`
- `GET /api/v1/clusters/{id}/logs`
- `GET /api/v1/clusters/{id}/events`
- `GET /api/v1/clusters/{id}/traces`
- `POST /api/v1/demo/telemetry/generate`

## Incidents and Investigations

- `GET /api/v1/incidents`
- `POST /api/v1/demo/incidents/generate`
- `POST /api/v1/investigations`
- `GET /api/v1/investigations`
- `GET /api/v1/investigations/{id}`
- `POST /api/v1/investigations/{id}/run`
- `GET /api/v1/investigations/{id}/evidence`

## Terraform Security and Drift

- `POST /api/v1/terraform/upload`
- `POST /api/v1/terraform/analyze`
- `GET /api/v1/terraform/workspaces`
- `GET /api/v1/terraform/findings`
- `GET /api/v1/terraform/findings/{id}`
- `GET /api/v1/terraform/drift`
- `GET /api/v1/terraform/stats`

## Cost Optimization

- `POST /api/v1/optimization/analyze`
- `GET /api/v1/optimization/stats`
- `GET /api/v1/optimization/findings`
- `GET /api/v1/optimization/recommendations`
- `GET /api/v1/optimization/recommendations/{id}`
- `GET /api/v1/optimization/reports`

## Smoke Test Sequence

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@nexusops.ai","password":"Password1"}' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" -X POST http://localhost:8000/api/v1/demo/generate
curl -H "Authorization: Bearer $TOKEN" -X POST http://localhost:8000/api/v1/demo/telemetry/generate
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/v1/terraform/analyze -d '{"demo":true}'
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/v1/optimization/analyze -d '{"demo":true}'
```
