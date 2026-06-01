"""Build structured investigation context from topology, telemetry, and incidents."""


from app.models.cluster import Cluster
from app.models.incident import Incident
from app.models.investigation import InvestigationEvidence
from app.repositories.cluster_repository import ClusterRepository
from app.repositories.incident_repository import IncidentRepository


class ContextBuilder:
    """Builds compact AI-ready context for an investigation."""

    def __init__(self, cluster_repo: ClusterRepository, incident_repo: IncidentRepository):
        self.cluster_repo = cluster_repo
        self.incident_repo = incident_repo

    async def build(
        self,
        *,
        incident: Incident | None,
        cluster_id: str | None,
        query: str,
        evidence: list[InvestigationEvidence],
    ) -> dict:
        cluster = await self._cluster_for(incident=incident, cluster_id=cluster_id)
        related_incidents = []
        if cluster:
            related_incidents = list(await self.incident_repo.get_by_cluster(cluster.id, limit=10))

        return {
            "query": query,
            "incident": self._incident(incident),
            "cluster": self._cluster(cluster),
            "topology": self._topology(cluster),
            "evidence": [self._evidence(item) for item in evidence[:30]],
            "related_incidents": [self._incident(item) for item in related_incidents if not incident or item.id != incident.id][:5],
        }

    async def _cluster_for(self, *, incident: Incident | None, cluster_id: str | None) -> Cluster | None:
        target_cluster_id = cluster_id or (incident.cluster_id if incident else None)
        if target_cluster_id:
            return await self.cluster_repo.get_with_topology(target_cluster_id)
        active = list(await self.cluster_repo.get_active_clusters_with_topology())
        return active[0] if active else None

    def _incident(self, incident: Incident | None) -> dict | None:
        if not incident:
            return None
        return {
            "id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity,
            "status": incident.status,
            "source": incident.source,
            "cluster_id": incident.cluster_id,
            "cluster_name": incident.cluster_name,
            "namespace": incident.namespace,
            "affected_workload": incident.affected_workload,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "root_cause": incident.root_cause,
            "ai_confidence": incident.ai_confidence,
        }

    def _cluster(self, cluster: Cluster | None) -> dict | None:
        if not cluster:
            return None
        return {
            "id": cluster.id,
            "name": cluster.name,
            "display_name": cluster.display_name,
            "provider": cluster.provider,
            "status": cluster.status,
            "environment": cluster.environment,
            "region": cluster.region,
            "node_count": cluster.node_count,
            "namespace_count": cluster.namespace_count,
            "deployment_count": cluster.deployment_count,
            "pod_count": cluster.pod_count,
            "service_count": cluster.service_count,
        }

    def _topology(self, cluster: Cluster | None) -> dict:
        if not cluster:
            return {"namespaces": [], "deployments": [], "pods": [], "services": []}
        return {
            "namespaces": [{"name": ns.name, "status": ns.status} for ns in cluster.namespaces],
            "deployments": [
                {
                    "namespace": workload.namespace_name,
                    "name": workload.name,
                    "ready": workload.replicas_ready,
                    "desired": workload.replicas_desired,
                    "healthy": workload.is_healthy,
                    "cpu": workload.cpu_usage_percent,
                    "memory": workload.memory_usage_percent,
                }
                for workload in cluster.workloads
            ],
            "pods": [
                {
                    "namespace": pod.namespace_name,
                    "name": pod.name,
                    "status": pod.status,
                    "phase": pod.phase,
                    "ready": pod.ready,
                    "restarts": pod.restart_count,
                    "node": pod.node_name,
                }
                for pod in cluster.pods
            ],
            "services": [{"namespace": svc.namespace_name, "name": svc.name, "type": svc.service_type} for svc in cluster.services],
        }

    def _evidence(self, item: InvestigationEvidence) -> dict:
        return {
            "type": item.evidence_type,
            "severity": item.severity,
            "title": item.title,
            "description": item.description,
            "resource_type": item.resource_type,
            "resource_name": item.resource_name,
            "namespace": item.namespace_name,
            "deployment": item.deployment_name,
            "pod": item.pod_name,
            "observed_at": item.observed_at.isoformat() if item.observed_at else None,
            "metadata": item.metadata_ or {},
        }
