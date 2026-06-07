# NexusOps AI Demo Scenarios

These scenarios are reusable demonstrations for recruiters, interviewers, and engineering reviews. They work with local Docker Compose and do not require a live Kubernetes cluster or cloud credentials.

## Setup

```bash
docker compose up -d
docker compose exec api alembic upgrade head
```

Create a demo user through the UI or API:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@nexusops.ai","username":"demo","password":"Password1"}'

TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@nexusops.ai","password":"Password1"}' | jq -r .access_token)
```

## Scenario 1: CrashLoopBackOff Investigation

Trigger:

```bash
curl -H "Authorization: Bearer $TOKEN" -X POST http://localhost:8000/api/v1/demo/generate
curl -H "Authorization: Bearer $TOKEN" -X POST http://localhost:8000/api/v1/demo/telemetry/generate
curl -H "Authorization: Bearer $TOKEN" -X POST http://localhost:8000/api/v1/demo/incidents/generate
```

Expected outcome:

- Infrastructure view shows degraded pods and a staged topology.
- Incidents page shows a high-severity Kubernetes workload incident.
- AI Investigation produces a deterministic RCA if no LLM provider is configured.
- Evidence includes pod restarts, Kubernetes events, and error logs.

## Scenario 2: Database Outage

Trigger:

- Generate demo incidents.
- Select the incident related to database or dependency failure.
- Run an investigation from the AI Investigation page.

Expected outcome:

- RCA points to dependency failure or database saturation.
- Remediation recommends rollback, connection pool review, and dependency health validation.

## Scenario 3: High Latency Service

Trigger:

- Generate demo telemetry.
- Open Dashboard, Incidents, and AI Investigation.

Expected outcome:

- Telemetry panels show elevated latency/error trends.
- Trace evidence highlights slow spans across frontend, API, auth, and database paths.

## Scenario 4: Terraform Security and Drift

Trigger:

```bash
curl -X POST http://localhost:8000/api/v1/terraform/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"demo": true, "scan_name": "Demo Terraform security scan"}'
```

Expected outcome:

- Security page shows critical findings for public ingress, public database exposure, wildcard IAM, hardcoded secrets, and policy violations.
- Drift records identify differences such as desired replicas versus actual replicas.
- Findings include remediation guidance and AI-style explanations.

## Scenario 5: Cost Waste Detection

Trigger:

```bash
curl -X POST http://localhost:8000/api/v1/optimization/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"demo": true, "report_name": "Demo cost optimization analysis"}'
```

Expected outcome:

- Cost Optimization page shows estimated monthly and annual savings.
- Recommendations identify oversized CPU/memory requests, excessive replicas, idle services, restart waste, and autoscaling opportunities.
- Each recommendation includes confidence, severity, impacted resource, estimated savings, and a Kubernetes patch sketch.

## Presentation Path

1. Start at Dashboard for executive platform posture.
2. Open Infrastructure to show topology and Kubernetes discovery.
3. Open Incidents and run AI Investigation for the RCA workflow.
4. Open Security to show Terraform drift and policy analysis.
5. Open Cost Optimization to show resource intelligence and savings.
