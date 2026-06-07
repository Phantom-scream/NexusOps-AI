# Terraform Security & Drift Analysis

NexusOps AI Phase 7 adds Infrastructure-as-Code posture management for Terraform.

## Stabilization Fixes

Before Phase 7 implementation, two Docker Compose services were unstable.

### OPA Restart Loop

Root cause:

- `infrastructure/policies/terraform_security.rego` used older partial-set syntax such as `deny[msg]`.
- The current `openpolicyagent/opa:latest` image expects Rego v1 syntax with `contains` and `if`.

Fix:

- Updated rules to `deny contains msg if { ... }` and `warn contains msg if { ... }`.
- Added an OPA healthcheck in `docker-compose.yml`.

### OpenTelemetry Collector Restart Loop

Root cause:

- The collector config used the deprecated `logging` exporter.
- The current `otel/opentelemetry-collector-contrib:latest` image no longer includes the `loki` exporter type used in the old config.

Fix:

- Replaced `logging` with the supported `debug` exporter.
- Removed the unsupported `loki` exporter from the collector pipeline.
- Added the official `health_check` extension and exposed port `13133`.
- Added an OTel collector healthcheck in `docker-compose.yml`.

## Domain Model

Phase 7 introduces:

- `TerraformWorkspace`
- `TerraformResource`
- `TerraformFinding`
- `TerraformDrift`
- `TerraformPolicyViolation`

The existing `TerraformScan` model is retained and extended with workspace, policy, and drift metadata.

## Analysis Pipeline

1. Upload Terraform files or request a demo environment.
2. Parse HCL using `python-hcl2`.
3. Persist resources as Terraform desired state.
4. Ingest optional actual state.
5. Run deterministic security checks.
6. Evaluate OPA policies when OPA is reachable.
7. Fall back to a local policy mirror when OPA is unavailable.
8. Compare desired and actual state for drift.
9. Generate deterministic AI-style explanations, with OpenAI/Ollama enrichment when configured.
10. Persist findings, drift records, policy violations, and scan summary.

## API Surface

- `POST /api/v1/terraform/upload`
- `POST /api/v1/terraform/analyze`
- `GET /api/v1/terraform/workspaces`
- `GET /api/v1/terraform/findings`
- `GET /api/v1/terraform/findings/{id}`
- `GET /api/v1/terraform/drift`
- `GET /api/v1/terraform/scans`
- `GET /api/v1/terraform/stats`

## Demo Environment

Sample Terraform lives in:

- `terraform/demo/insecure-platform/main.tf`
- `terraform/demo/insecure-platform/kubernetes.tf`
- `terraform/demo/insecure-platform/state.json`

The demo intentionally includes:

- Public SSH ingress
- Public RDS
- Missing encryption
- Hardcoded secret
- Wildcard IAM
- Privileged Kubernetes workload
- Missing resource limits
- Overly permissive RBAC
- Drifted database instance type
- Drifted Kubernetes replica count

## Frontend

The Security page now uses React Query and backend Terraform APIs. It includes:

- Findings dashboard
- Drift dashboard
- Severity breakdown
- Category breakdown
- Security findings table
- Finding detail panel
- Demo analysis action
