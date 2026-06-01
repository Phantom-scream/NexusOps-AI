"""Rule-assisted remediation recommendations for investigation results."""

from app.models.investigation import InvestigationEvidence


class RemediationEngine:
    """Builds actionable recommendations from evidence patterns."""

    def recommend(self, evidence: list[InvestigationEvidence], root_cause: str | None = None) -> list[dict]:
        text = " ".join([root_cause or ""] + [item.title + " " + item.description for item in evidence]).lower()
        recommendations: list[dict] = []

        if "crashloop" in text or "restart" in text or "back-off" in text:
            recommendations.append(
                {
                    "priority": 1,
                    "category": "kubernetes",
                    "title": "Stabilize restarting pods",
                    "description": "Inspect the failing pod logs, confirm the failing container, and roll back the deployment if the crash began after a release.",
                    "command": "kubectl logs deploy/<deployment> -n <namespace> --previous && kubectl rollout undo deploy/<deployment> -n <namespace>",
                }
            )

        if "memory" in text or "oom" in text:
            recommendations.append(
                {
                    "priority": 2,
                    "category": "resources",
                    "title": "Mitigate memory pressure",
                    "description": "Raise memory limits only as a short-term mitigation; follow up by profiling the workload for leaks or unbounded caches.",
                    "command": "kubectl top pod -n <namespace> && kubectl describe pod <pod> -n <namespace>",
                }
            )

        if "latency" in text or "duration" in text or "error rate" in text:
            recommendations.append(
                {
                    "priority": 3,
                    "category": "performance",
                    "title": "Reduce request path latency",
                    "description": "Correlate slow trace spans with recent deployments and downstream dependencies before scaling.",
                    "command": "kubectl rollout history deploy/<deployment> -n <namespace>",
                }
            )

        if "replicas" in text or "degraded" in text:
            recommendations.append(
                {
                    "priority": 4,
                    "category": "availability",
                    "title": "Restore desired replica count",
                    "description": "Inspect scheduling, image pull, readiness probe, and resource quota failures for the degraded deployment.",
                    "command": "kubectl describe deploy/<deployment> -n <namespace>",
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "priority": 5,
                    "category": "triage",
                    "title": "Gather deeper telemetry",
                    "description": "Collect pod describe output, recent deployment history, and dependency health to improve confidence.",
                    "command": "kubectl get events -A --sort-by=.lastTimestamp",
                }
            )

        return recommendations
