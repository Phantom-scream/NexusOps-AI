.PHONY: help dev prod down build test lint format migrate seed clean

DOCKER_COMPOSE := docker compose
BACKEND_DIR := backend
FRONTEND_DIR := frontend

# ============================================================
# Help
# ============================================================
help:
	@echo ""
	@echo "  NexusOps AI — Development Commands"
	@echo "  ====================================="
	@echo ""
	@echo "  make dev          Start full stack in development mode"
	@echo "  make prod         Start full stack in production mode"
	@echo "  make down         Stop all containers"
	@echo "  make build        Build all Docker images"
	@echo "  make test         Run all tests"
	@echo "  make lint         Run linters"
	@echo "  make format       Format code"
	@echo "  make migrate      Run database migrations"
	@echo "  make seed         Seed database with sample data"
	@echo "  make clean        Remove all containers and volumes"
	@echo "  make logs         Tail all container logs"
	@echo "  make shell-api    Open shell in API container"
	@echo ""

# ============================================================
# Docker Lifecycle
# ============================================================
dev:
	@echo "Starting NexusOps AI in development mode..."
	cp -n .env.example .env 2>/dev/null || true
	$(DOCKER_COMPOSE) up -d --build
	@echo ""
	@echo "  Services:"
	@echo "    Frontend:   http://localhost:3000"
	@echo "    Backend:    http://localhost:8000"
	@echo "    API Docs:   http://localhost:8000/docs"
	@echo "    Grafana:    http://localhost:3001"
	@echo "    Prometheus: http://localhost:9090"
	@echo "    Qdrant:     http://localhost:6333/dashboard"
	@echo ""

prod:
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build

logs:
	$(DOCKER_COMPOSE) logs -f

shell-api:
	$(DOCKER_COMPOSE) exec api bash

shell-worker:
	$(DOCKER_COMPOSE) exec worker bash

clean:
	@echo "WARNING: This will remove all containers and volumes."
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f

# ============================================================
# Backend
# ============================================================
migrate:
	cd $(BACKEND_DIR) && alembic upgrade head

migrate-down:
	cd $(BACKEND_DIR) && alembic downgrade -1

migrate-new:
	@read -p "Migration message: " msg && \
	cd $(BACKEND_DIR) && alembic revision --autogenerate -m "$$msg"

seed:
	cd $(BACKEND_DIR) && python -m scripts.seed

test-backend:
	cd $(BACKEND_DIR) && pytest tests/ -v --cov=app --cov-report=term-missing

lint-backend:
	cd $(BACKEND_DIR) && ruff check app/ && mypy app/

format-backend:
	cd $(BACKEND_DIR) && ruff format app/ && isort app/

# ============================================================
# Frontend
# ============================================================
install-frontend:
	cd $(FRONTEND_DIR) && npm install

test-frontend:
	cd $(FRONTEND_DIR) && npm run test

lint-frontend:
	cd $(FRONTEND_DIR) && npm run lint

build-frontend:
	cd $(FRONTEND_DIR) && npm run build

# ============================================================
# Combined
# ============================================================
test: test-backend test-frontend

lint: lint-backend lint-frontend

format: format-backend

# ============================================================
# Kubernetes
# ============================================================
k8s-deploy:
	kubectl apply -f infrastructure/kubernetes/

k8s-teardown:
	kubectl delete -f infrastructure/kubernetes/

helm-install:
	helm install nexusops infrastructure/helm/nexusops/ --values infrastructure/helm/nexusops/values.yaml

helm-upgrade:
	helm upgrade nexusops infrastructure/helm/nexusops/ --values infrastructure/helm/nexusops/values.yaml
