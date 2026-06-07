# Cost Optimization & Resource Intelligence

NexusOps AI Phase 8 adds a persistent cost optimization engine that analyzes Kubernetes topology and telemetry to identify waste and generate savings recommendations.

## Domain Model

Phase 8 introduces:

- `ResourceUtilization`
- `OptimizationRule`
- `OptimizationFinding`
- `OptimizationReport`

The existing `CostRecommendation` model is extended with report/finding links, severity, confidence, impact, evidence, recommendation text, and richer resource metadata.

## Analysis Pipeline

1. Load Kubernetes clusters and topology.
2. Generate demo topology and telemetry when demo mode is requested or no clusters exist.
3. Build utilization snapshots from workload requests, limits, replicas, telemetry, and restart data.
4. Apply deterministic optimization rules.
5. Persist findings.
6. Convert findings into recommendations with estimated savings.
7. Add deterministic AI-style explanations, with OpenAI/Ollama enrichment when configured.
8. Persist optimization reports and dashboard statistics.

## Optimization Rules

Implemented rules include:

- CPU oversizing
- Memory oversizing
- Excessive replicas
- Idle services
- Missing autoscaling recommendations
- Restart waste

Each finding includes:

- Severity
- Confidence
- Evidence
- Estimated savings
- Recommendation
- Remediation guidance

## API Surface

- `POST /api/v1/optimization/analyze`
- `GET /api/v1/optimization/findings`
- `GET /api/v1/optimization/reports`
- `GET /api/v1/optimization/recommendations`
- `GET /api/v1/optimization/recommendations/{id}`
- `GET /api/v1/optimization/stats`

## Frontend

The Cost Optimization page now uses React Query and backend APIs. It displays:

- Estimated monthly and annual savings
- Open recommendations
- Priority findings
- Optimization score
- Savings opportunity chart
- Finding type breakdown
- Report history
- Recommendation detail panel with remediation patch guidance

## Demo Mode

`POST /api/v1/optimization/analyze` with `{"demo": true}` creates realistic demo waste scenarios:

- Oversized deployment
- Idle service
- Overprovisioned resources
- Inefficient static scaling
- Missing autoscaling
- Wasteful workloads

Demo mode requires no cloud provider credentials.
