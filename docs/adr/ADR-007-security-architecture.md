# ADR-007: Security Architecture

## Context

NexusOps AI exposes sensitive platform workflows: infrastructure discovery, Terraform analysis, incident investigation, AI prompts, demo generation, and administrative audit data. A credible cloud platform must document authentication, authorization, auditability, secret handling, and policy evaluation tradeoffs.

## Decision

Use layered security controls:

- JWT authentication with issuer, audience, expiry, token type, and unique token IDs.
- Role-based authorization for Viewer, Operator, Security Analyst, and Administrator workflows.
- Audit trail for authentication, demo generation, investigations, security scans, Terraform analysis, and cost analysis.
- OPA-backed policy evaluation for infrastructure-as-code security checks.
- Environment-based configuration with production guardrails for secrets and CORS.

## Alternatives

- **Single admin token:** simple, but not enterprise credible.
- **No RBAC during portfolio phase:** faster, but weakens security architecture and interview value.
- **Full OAuth/OIDC implementation:** production-realistic, but too complex for the current project scope.

## Consequences

- Write operations have explicit authorization boundaries.
- Audit records provide accountability for sensitive workflows.
- The current JWT design remains stateless and should evolve to persisted sessions and refresh-token revocation for production SaaS use.
- Security documentation must clearly distinguish implemented controls from recommended future controls.
