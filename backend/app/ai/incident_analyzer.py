"""
NexusOps AI — AI Incident Investigation Engine
Flagship AI capability: correlates K8s events, logs, and metrics to identify root causes
"""
import json
import re
from typing import Any

import structlog

from app.ai.llm_client import llm_client
from app.ai.prompts.templates import (
    INCIDENT_INVESTIGATION_SYSTEM_PROMPT,
    INCIDENT_INVESTIGATION_USER_TEMPLATE,
)
from app.ai.rag_pipeline import RAGPipeline

logger = structlog.get_logger(__name__)


class IncidentInvestigationEngine:
    """
    Core AI engine for infrastructure incident root cause analysis.

    Pipeline:
    1. Gather telemetry context (K8s events, logs, metrics)
    2. Retrieve similar past incidents via RAG
    3. Send enriched context to LLM for analysis
    4. Parse and return structured findings
    """

    def __init__(self, rag_pipeline: RAGPipeline | None = None):
        self.rag = rag_pipeline or RAGPipeline()

    async def investigate(
        self,
        cluster_name: str,
        query: str,
        namespace: str | None = None,
        workload: str | None = None,
        context_window_minutes: int = 60,
        k8s_events: list[dict] | None = None,
        pod_logs: str | None = None,
        metrics: dict | None = None,
        recent_changes: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Run the full AI incident investigation pipeline.

        Returns structured analysis with root cause, contributing factors,
        remediation steps, and confidence score.
        """
        logger.info(
            "Starting incident investigation",
            cluster=cluster_name,
            namespace=namespace,
            workload=workload,
            query=query[:100],
        )

        # Retrieve relevant past incidents from RAG
        rag_context = ""
        try:
            rag_results = await self.rag.search_incidents(
                query=f"{cluster_name} {namespace} {workload} {query}",
                limit=3,
            )
            if rag_results:
                rag_context = "\n".join([
                    f"Past incident: {r['content'][:500]}"
                    for r in rag_results
                ])
        except Exception as exc:
            logger.warning("RAG retrieval failed, proceeding without context", error=str(exc))

        # Format context data
        events_text = self._format_k8s_events(k8s_events or [])
        logs_text = pod_logs or "No log data available."
        metrics_text = self._format_metrics(metrics or {})
        changes_text = self._format_changes(recent_changes or [])

        user_message = INCIDENT_INVESTIGATION_USER_TEMPLATE.format(
            cluster_name=cluster_name,
            namespace=namespace or "all namespaces",
            workload=workload or "multiple workloads",
            query=query,
            window=context_window_minutes,
            k8s_events=events_text,
            pod_logs=logs_text[:3000],  # Truncate to avoid token limits
            metrics=metrics_text,
            recent_changes=changes_text,
            rag_context=rag_context or "No similar past incidents found.",
        )

        # Invoke LLM
        response = await llm_client.chat(
            system_prompt=INCIDENT_INVESTIGATION_SYSTEM_PROMPT,
            user_message=user_message,
        )

        # Parse JSON response
        result = self._parse_llm_response(response["content"])
        result["tokens_used"] = response.get("tokens_used")
        result["model"] = response.get("model")
        result["context_sources"] = self._build_source_list(
            has_k8s_events=bool(k8s_events),
            has_logs=bool(pod_logs),
            has_metrics=bool(metrics),
            has_rag=bool(rag_context),
        )

        logger.info(
            "Investigation complete",
            severity=result.get("severity"),
            confidence=result.get("confidence"),
        )

        return result

    def _format_k8s_events(self, events: list[dict]) -> str:
        if not events:
            return "No Kubernetes events in the specified time window."

        lines = []
        for event in events[:20]:  # Cap at 20 events
            lines.append(
                f"[{event.get('type', 'Normal')}] {event.get('reason', '')} | "
                f"{event.get('involved_object', '')} | "
                f"{event.get('message', '')[:200]}"
            )
        return "\n".join(lines)

    def _format_metrics(self, metrics: dict) -> str:
        if not metrics:
            return "No metrics data available."

        lines = []
        for metric_name, value in metrics.items():
            lines.append(f"{metric_name}: {value}")
        return "\n".join(lines)

    def _format_changes(self, changes: list[dict]) -> str:
        if not changes:
            return "No recent infrastructure changes detected."

        lines = []
        for change in changes[:10]:
            lines.append(
                f"[{change.get('timestamp', 'unknown')}] {change.get('type', '')} | "
                f"{change.get('resource', '')} | {change.get('description', '')}"
            )
        return "\n".join(lines)

    def _parse_llm_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from LLM response, with graceful fallback."""
        try:
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r"```(?:json)?\n(.*?)\n```", content, re.DOTALL)
            if json_match:
                content = json_match.group(1)

            parsed = json.loads(content)
            return parsed

        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse LLM JSON response, using fallback", error=str(exc))
            # Graceful degradation — return a minimal valid response
            return {
                "severity": "medium",
                "root_cause": "Analysis could not be fully structured. See detail.",
                "root_cause_detail": content[:2000],
                "contributing_factors": [],
                "remediation": {
                    "immediate": "Review pod logs and events manually",
                    "short_term": "Investigate resource constraints",
                    "long_term": "Implement better observability",
                },
                "confidence": 0.3,
                "evidence": [],
            }

    def _build_source_list(self, **kwargs: bool) -> list[str]:
        sources = []
        if kwargs.get("has_k8s_events"):
            sources.append("kubernetes_events")
        if kwargs.get("has_logs"):
            sources.append("pod_logs")
        if kwargs.get("has_metrics"):
            sources.append("prometheus_metrics")
        if kwargs.get("has_rag"):
            sources.append("rag_historical_incidents")
        return sources
