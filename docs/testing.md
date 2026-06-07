# Testing Strategy

NexusOps AI uses tests as an architecture signal. The goal is not only to increase line coverage, but to verify the important platform boundaries: authentication, authorization, provider behavior, service workflows, persistence, and API contracts.

## Test Layers

| Layer | Purpose | Examples |
|---|---|---|
| Unit tests | Validate deterministic logic in isolation. | Optimization rules, Terraform security rules, context building. |
| Service tests | Validate business workflows with repositories and providers. | Demo generation, telemetry generation, investigation pipeline. |
| Repository tests | Validate persistence behavior and query filters. | Audit event filtering, topology reconstruction, report retrieval. |
| API tests | Validate HTTP contracts, schemas, auth, and RBAC. | `/auth`, `/demo`, `/investigations`, `/terraform`, `/optimization`. |
| Smoke tests | Validate the critical demo path. | Register, login, generate demo data, run analysis workflows. |
| Build tests | Validate deployable artifacts. | Backend image, frontend image, frontend build. |

## Current Quality Gate

The CI pipeline validates:

- Ruff linting.
- Backend compile checks.
- Alembic migrations.
- Backend tests with coverage output.
- Focused API smoke tests.
- Frontend TypeScript checks.
- Frontend linting, tests, and build.
- Docker Compose config validation.
- Production container image builds.

## Security-Oriented Tests

Required coverage areas:

- Authorization boundaries for Viewer, Operator, Security Analyst, and Administrator.
- Audit event creation for sensitive workflows.
- Token refresh behavior for active and inactive users.
- Security middleware and production configuration guardrails.
- Provider fallback behavior when Kubernetes, telemetry, or LLM providers are unavailable.
- Failure scenarios for invalid payloads, missing resources, and provider errors.

## Recent Coverage Additions

- Viewer denial for protected optimization analysis.
- Administrator-only audit event listing.
- Refresh token role preservation using the configured default role.

## Future Test Improvements

- Add property-based tests for Terraform rule inputs.
- Add provider contract tests shared across Kubernetes and demo providers.
- Add integration tests for audit records emitted by each sensitive endpoint.
- Add frontend tests for unauthorized and error states.
- Add migration rollback validation in a disposable database.

## Local Validation

Use the deployment guide for local service startup. The core validation commands are:

```bash
docker compose config --quiet
docker compose exec api alembic upgrade head
docker compose exec api ruff check app tests
docker compose exec api pytest -q
cd frontend && npm run lint && npm run test && npm run build
```
