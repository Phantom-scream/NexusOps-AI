# AI Incident Investigation Engine

NexusOps AI Phase 6 adds a persistent investigation workflow that turns topology and telemetry into structured root cause analysis.

## Workflow

1. Select or create an incident.
2. Collect related infrastructure topology.
3. Collect correlated metrics, logs, events, and traces.
4. Build an investigation context.
5. Generate analysis through the configured LLM provider.
6. Fall back to deterministic RCA when the LLM provider is unavailable.
7. Persist the investigation, evidence, remediation, and incident updates.

## Architecture

Phase 6 introduces:

- `InvestigationService`: orchestrates the full workflow.
- `EvidenceCollector`: normalizes telemetry signals into evidence records.
- `ContextBuilder`: builds compact AI-ready context from incidents, topology, and telemetry.
- `RemediationEngine`: adds rule-assisted remediation recommendations.
- `LLMProvider` abstraction: supports OpenAI and Ollama through provider classes.
- RAG indexing: completed investigations are indexed through the existing Qdrant-backed incident collection when embeddings are available.

## Persistent Data

New tables:

- `investigations`
- `investigation_evidence`

Each investigation stores:

- Summary
- Probable root cause
- Technical detail
- Supporting evidence
- Affected resources
- Severity
- Confidence score
- Remediation recommendations
- LLM provider/model metadata
- Full investigation context

## API Surface

- `POST /api/v1/investigations`
- `GET /api/v1/investigations`
- `GET /api/v1/investigations/{id}`
- `POST /api/v1/investigations/{id}/run`
- `GET /api/v1/investigations/{id}/evidence`

Demo support:

- `POST /api/v1/demo/incidents/generate`

The demo endpoint creates realistic incident scenarios and ensures demo telemetry exists.

## Demo Scenarios

Generated scenarios include:

- CrashLoopBackOff
- Failed deployment
- Memory leak
- High latency
- Database dependency outage
- Network dependency issue

## Frontend

The AI Investigation page now uses backend APIs. It displays:

- Incident queue
- Investigation history
- Root cause analysis
- Confidence score
- Evidence panels
- Affected resources
- Remediation recommendations

If no incidents exist, use **Generate Demo Incidents** from the AI Investigation page.
