# ADR-001: FastAPI Selection

## Context

NexusOps AI needs a backend framework that supports typed APIs, OpenAPI documentation, async request handling, dependency injection, authentication dependencies, and a clean boundary between routes, services, repositories, and schemas. The project also needs to be approachable for cloud engineering interviews and portfolio review.

## Decision

Use FastAPI as the primary HTTP API framework for the backend.

FastAPI provides first-class Pydantic integration, OpenAPI generation, async endpoint support, dependency injection, and a strong developer experience for service-oriented Python APIs.

## Alternatives

- **Django REST Framework:** mature and batteries-included, but heavier for a platform API that does not need Django's admin or ORM stack.
- **Flask:** simple and flexible, but requires more manual assembly for typed validation, OpenAPI, async behavior, and dependency injection.
- **Node.js/NestJS:** strong enterprise structure, but Python better matches the AI, infrastructure automation, and data tooling used in the project.

## Consequences

- API contracts remain explicit through Pydantic schemas.
- Auth and RBAC enforcement can be expressed as reusable dependencies.
- Async database access and external provider calls fit naturally.
- The team must keep route handlers thin so FastAPI convenience does not become business logic sprawl.
