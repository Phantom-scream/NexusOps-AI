# Threat Model

This threat model documents the major risks for NexusOps AI as a platform engineering portfolio project. It distinguishes implemented mitigations from recommended mitigations that would be required before operating as a production SaaS.

## Scope

In scope:

- FastAPI APIs and authentication.
- React frontend and API client behavior.
- Kubernetes discovery and demo providers.
- Telemetry, incident, Terraform, cost, AI, and audit workflows.
- Docker Compose, CI/CD, and local deployment assets.

Out of scope:

- Full multi-tenant SaaS isolation.
- Cloud account billing integration.
- Enterprise SSO and external identity provider configuration.

## Threats

| Threat | Risk | Impact | Existing mitigations | Recommended mitigations |
|---|---|---|---|---|
| JWT abuse | A stolen or forged token could access protected APIs. | Unauthorized reads, analysis execution, or administrative access. | JWT issuer, audience, expiry, token type, unique token ID, strong secret production guardrails, RBAC dependencies. | Persist session records, track token families, support server-side revocation, rotate signing keys, integrate OIDC. |
| Token theft | Browser storage, logs, or compromised clients could expose bearer tokens. | Account takeover until token expiry. | Short-lived access tokens, refresh endpoint validates active user, audit events for login and refresh. | Move browser auth to secure HttpOnly cookies with SameSite controls, add refresh-token rotation persistence, add suspicious-session detection. |
| XSS | Malicious scripts could execute in the frontend and access user context. | Token theft, data exposure, unauthorized actions. | React escapes content by default, no intentional raw HTML rendering in core pages. | Add CSP headers, sanitize any markdown/AI output, avoid localStorage token storage, add frontend security tests. |
| CSRF | Cookie-based auth could allow forged state-changing requests. | Unauthorized write operations if cookies are introduced without CSRF protection. | Current bearer-token approach is not automatically attached by the browser. | If moving to cookies, add SameSite=strict/lax, CSRF tokens for unsafe methods, and origin checks. |
| Prompt injection | Logs, incidents, or user prompts could instruct the AI to ignore policy or leak data. | Misleading RCA, unsafe remediation, exposure of hidden context. | Deterministic fallbacks, structured investigation outputs, evidence-oriented context builder. | Add prompt-injection filters, source attribution, output validation, model policy prompts, and allowlist-based tool execution. |
| Supply-chain attacks | Compromised dependencies or container images could introduce vulnerabilities. | Build compromise, runtime compromise, credential theft. | CI lint/test/build gates, production image builds, pinned base major versions. | Add SBOM generation, Trivy scans, dependency vulnerability scans, signed artifacts, Dependabot or Renovate. |
| Secret leakage | Environment files, logs, screenshots, or manifests could expose secrets. | Credential compromise and unauthorized platform access. | `.env.example` uses placeholders, production secret validation, Kubernetes secrets documented as placeholders. | Use secret managers, sealed secrets, pre-commit secret scanning, log redaction, environment-specific secret rotation. |
| Kubernetes privilege escalation | Discovery credentials could be over-privileged. | Cluster data exposure or workload modification. | Kubernetes manifests include read-oriented service account and RBAC examples. | Enforce least-privilege ClusterRoles, namespace scoping where possible, audit Kubernetes API calls, avoid mounting broad kubeconfigs in production. |
| API abuse | Attackers could spam demo generation, analysis, or expensive AI workflows. | Resource exhaustion, high costs, noisy audit records. | RBAC protects write and analysis operations, audit events record sensitive actions. | Add per-user and per-IP rate limits, request quotas, queue limits, and cost controls for LLM calls. |
| Denial of service | Large telemetry, Terraform uploads, or repeated syncs could overload API, DB, or workers. | Slow platform, failed syncs, unavailable dashboards. | Async service architecture, Celery workers, Redis queues, bounded demo data. | Add payload limits, backpressure, queue partitioning, worker autoscaling, telemetry retention, and circuit breakers. |
| Multi-tenant risks | Shared resources could leak data between organizations if SaaS tenancy is added. | Cross-tenant data exposure or privilege escalation. | Current project is single-tenant by design. | Add tenant IDs to all domain models, tenant-aware indexes, tenant-scoped RBAC, row-level security, and tenant isolation tests. |

## Authentication and Token Lifecycle

The current implementation uses stateless JWT access and refresh tokens. Refresh requests validate token type and ensure the user still exists and is active before issuing new tokens. Authentication events are audited.

For production SaaS usage, refresh tokens should be stored as hashed token families with rotation validation, reuse detection, absolute expiry, per-device sessions, and administrative revocation.

## Frontend Token Storage Tradeoff

The current bearer-token strategy is simple for local development and API exploration. It also avoids CSRF because tokens are not automatically attached by the browser. The downside is that browser-accessible token storage is more exposed to XSS.

The recommended production design is an HttpOnly secure cookie strategy with SameSite controls, CSRF protection for unsafe methods, and short-lived access tokens.

## AI Safety Notes

AI investigation output must be treated as advisory. Production use should require source attribution, deterministic validation of remediation commands, restricted tool access, and explicit human approval before applying operational changes.
