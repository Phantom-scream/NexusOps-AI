# ADR-003: Provider Pattern

## Context

NexusOps AI needs to support real integrations and demo scenarios without creating separate frontend flows or separate domain models. Kubernetes discovery, telemetry ingestion, Terraform analysis, AI providers, and demo generators should feed the same service and persistence layers.

## Decision

Use provider abstractions for external and demo data sources.

Examples include infrastructure providers, telemetry providers, LLM providers, and deterministic fallback providers. Providers normalize data into shared domain models before services persist or analyze it.

## Alternatives

- **Direct integration in API routes:** fast to build, but tightly couples HTTP handlers to provider implementation details.
- **Separate demo-only models:** convenient for demos, but weakens credibility because demo behavior does not exercise production paths.
- **Plugin system:** flexible, but too complex for the current maturity level.

## Consequences

- Frontend and API consumers remain provider-agnostic.
- Demo mode is useful for development while preserving production architecture.
- Provider tests can validate conformance.
- Provider boundaries must remain small and explicit to avoid hidden framework complexity.
