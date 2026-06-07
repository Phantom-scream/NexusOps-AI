# Developer Onboarding

## Local Requirements

- Docker 24+
- Docker Compose v2
- Node.js 20+
- Python 3.12+

## First Run

```bash
git clone https://github.com/Phantom-scream/NexusOps-AI.git
cd NexusOps-AI
cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head
```

## Backend Workflow

```bash
docker compose exec api ruff check app tests
docker compose exec api pytest -q
docker compose exec api alembic upgrade head
```

Backend layers:

- `api/v1`: FastAPI route handlers
- `schemas`: Pydantic request/response contracts
- `services`: business workflows
- `repositories`: SQLAlchemy persistence access
- `models`: SQLAlchemy domain models
- `infrastructure`, `observability`, `ai`: provider-specific integrations

## Frontend Workflow

```bash
cd frontend
npm install
npm run lint
npm run test
npm run build
```

Frontend layers:

- `pages`: route-level product screens
- `services`: API clients
- `components`: reusable UI elements
- `components/charts`: chart primitives
- `store`: persisted auth state

## Development Principles

- Keep provider-specific logic behind provider abstractions.
- Keep frontend pages API-backed; avoid adding new static mocks for implemented domains.
- Use deterministic fallbacks for demos where external credentials are unavailable.
- Add tests for new rules, services, and API flows.
- Update docs when workflows or demo behavior changes.
