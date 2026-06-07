"""Demo infrastructure API."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, require_operator
from app.models.audit import AuditEvent
from app.models.cluster import Cluster
from app.models.incident import Incident
from app.models.telemetry import TelemetrySource
from app.repositories.audit_repository import AuditRepository
from app.repositories.cluster_repository import ClusterRepository
from app.repositories.incident_repository import IncidentAnalysisRepository, IncidentRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.cluster import ClusterOut
from app.schemas.incident import IncidentCreate, IncidentOut
from app.services.audit_service import AuditService
from app.services.incident_service import IncidentService
from app.services.infrastructure_discovery_service import InfrastructureDiscoveryService
from app.services.telemetry_service import TelemetryService

router = APIRouter()


def get_discovery_service(db: AsyncSession = Depends(get_db)) -> InfrastructureDiscoveryService:
    return InfrastructureDiscoveryService(repository=ClusterRepository(model=Cluster, session=db))


def get_incident_service(db: AsyncSession = Depends(get_db)) -> IncidentService:
    from app.models.incident import IncidentAnalysis

    return IncidentService(
        repository=IncidentRepository(model=Incident, session=db),
        analysis_repository=IncidentAnalysisRepository(model=IncidentAnalysis, session=db),
    )


def get_telemetry_service(db: AsyncSession = Depends(get_db)) -> TelemetryService:
    return TelemetryService(
        telemetry_repo=TelemetryRepository(model=TelemetrySource, session=db),
        cluster_repo=ClusterRepository(model=Cluster, session=db),
    )


@router.post("/generate", response_model=list[ClusterOut])
async def generate_demo_infrastructure(
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: InfrastructureDiscoveryService = Depends(get_discovery_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """
    Generate a realistic demo infrastructure topology using the same persistence
    model and APIs as Kubernetes discovery.
    """
    clusters = await service.generate_demo_environment()
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="demo.infrastructure_generate",
        actor=current_user,
        request=request,
        resource_type="demo_environment",
        metadata={"clusters": len(clusters)},
    )
    return [ClusterOut.model_validate(cluster) for cluster in clusters]


@router.post("/incidents/generate", response_model=list[IncidentOut])
async def generate_demo_incidents(
    request: Request,
    db: AsyncSession = Depends(get_db),
    discovery_service: InfrastructureDiscoveryService = Depends(get_discovery_service),
    incident_service: IncidentService = Depends(get_incident_service),
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Generate realistic incident scenarios connected to demo topology and telemetry."""
    clusters = await discovery_service.repo.get_active_clusters_with_topology()
    if not clusters:
        clusters = await discovery_service.generate_demo_environment()
        clusters = await discovery_service.repo.get_active_clusters_with_topology()

    await telemetry_service.generate_demo_telemetry()

    incidents = []
    scenarios = [
        ("CrashLoopBackOff detected in payments worker", "critical", "payments", "Repeated container restarts and back-off logs indicate a crashing payments workload."),
        ("Failed deployment rollout in checkout API", "high", "checkout-api", "Deployment has fewer ready replicas than desired after rollout."),
        ("Memory leak suspected in API gateway", "high", "api-gateway", "Memory utilization is trending above safe thresholds and correlates with elevated errors."),
        ("High latency across customer frontend", "medium", "frontend", "Trace spans show elevated request duration between frontend and API gateway."),
        ("Database dependency outage impacting orders", "critical", "orders", "Application logs and traces indicate downstream PostgreSQL dependency failures."),
        ("Network dependency errors in auth path", "medium", "auth", "Intermittent request failures point to a dependency or network path issue."),
    ]

    cluster_list = list(clusters)
    for index, (title, severity, workload_hint, description) in enumerate(scenarios):
        cluster = cluster_list[index % len(cluster_list)]
        workload = next(
            (item for item in cluster.workloads if workload_hint in item.name),
            cluster.workloads[index % len(cluster.workloads)] if cluster.workloads else None,
        )
        incident = await incident_service.create_incident(
            IncidentCreate(
                title=title,
                description=description,
                severity=severity,
                source="ai_detected",
                cluster_id=cluster.id,
                cluster_name=cluster.name,
                namespace=workload.namespace_name if workload else None,
                affected_workload=workload.name if workload else None,
                tags=["demo", "phase-6", workload_hint],
            )
        )
        incidents.append(incident)

    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="demo.incidents_generate",
        actor=current_user,
        request=request,
        resource_type="incident",
        metadata={"incidents": len(incidents)},
    )
    return [IncidentOut.model_validate(incident) for incident in incidents]
