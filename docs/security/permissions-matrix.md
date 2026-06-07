# Permissions Matrix

NexusOps AI uses four enterprise roles. The current implementation focuses on portfolio-grade role enforcement for sensitive workflows while keeping the read path easy to demonstrate.

## Roles

| Role | Purpose |
|---|---|
| Viewer | Read-only access to dashboards, infrastructure, telemetry, incidents, findings, and reports. |
| Operator | Operational workflows such as demo generation, incident updates, investigations, telemetry generation, and cost analysis. |
| Security Analyst | Security-focused workflows such as Terraform upload and Terraform analysis. Operators and administrators also inherit these capabilities. |
| Administrator | Administrative access, including audit event review and privileged platform operations. |

## API Permission Matrix

| Workflow | Viewer | Operator | Security Analyst | Administrator |
|---|---:|---:|---:|---:|
| Read dashboards and infrastructure | Yes | Yes | Yes | Yes |
| Read telemetry, incidents, findings, reports | Yes | Yes | Yes | Yes |
| Register, update, or sync clusters | No | Yes | No | Yes |
| Delete clusters | No | No | No | Yes |
| Generate demo infrastructure | No | Yes | No | Yes |
| Generate demo telemetry | No | Yes | No | Yes |
| Generate demo incidents | No | Yes | No | Yes |
| Create or update incidents | No | Yes | No | Yes |
| Run investigations | No | Yes | No | Yes |
| Run AI investigation endpoint | No | Yes | No | Yes |
| Upload Terraform content | No | Yes | Yes | Yes |
| Run Terraform analysis | No | Yes | Yes | Yes |
| Queue legacy Terraform security scan | No | Yes | Yes | Yes |
| Run cost optimization analysis | No | Yes | No | Yes |
| View audit events | No | No | No | Yes |

## Enforcement Notes

- Read endpoints require authentication unless intentionally public health checks are used.
- Write and analysis endpoints use FastAPI dependencies such as `require_operator`, `require_security_analyst`, and `require_admin`.
- Super administrators are treated as administrators for authorization checks.
- Tests cover viewer denial for write analysis endpoints and administrator-only audit event access.

## Future Production Enhancements

- Persist sessions and support forced logout.
- Add tenant-aware permissions if multi-tenancy is introduced.
- Add object-level authorization for resource ownership or cluster ownership.
- Add policy-based authorization for fine-grained enterprise controls.
