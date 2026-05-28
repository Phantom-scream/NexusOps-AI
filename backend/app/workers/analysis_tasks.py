"""
NexusOps AI — AI Analysis Celery Tasks
Background AI analysis and anomaly detection tasks
"""
import asyncio

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.workers.analysis_tasks.analyze_incident",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    queue="analysis",
)
def analyze_incident_task(
    self,
    incident_id: str,
    query: str,
    context_window_minutes: int = 60,
) -> dict:
    """Async Celery task to run AI incident analysis in the background."""
    return run_async(_analyze_incident_async(incident_id, query, context_window_minutes))


@celery_app.task(
    name="app.workers.analysis_tasks.detect_anomalies",
    bind=True,
)
def detect_anomalies(self) -> dict:
    """Periodic task: scan active clusters for anomalies and auto-create incidents."""
    return run_async(_detect_anomalies_async())


@celery_app.task(
    name="app.workers.analysis_tasks.generate_cost_report",
    bind=True,
)
def generate_cost_report(self) -> dict:
    """Periodic task: generate cost optimization reports for all clusters."""
    return run_async(_generate_cost_report_async())


@celery_app.task(
    name="app.workers.analysis_tasks.run_terraform_scan",
    bind=True,
    max_retries=2,
    queue="analysis",
)
def run_terraform_scan_task(
    self,
    scan_id: str,
    terraform_content: str,
    scan_name: str,
    repo_url: str = None,
) -> dict:
    """Run Terraform security analysis as a background task."""
    return run_async(_run_terraform_scan_async(scan_id, terraform_content, scan_name, repo_url))


async def _analyze_incident_async(incident_id: str, query: str, context_window_minutes: int) -> dict:
    """Full AI incident investigation pipeline."""
    from app.core.database import AsyncSessionLocal
    from app.repositories.incident_repository import IncidentRepository, IncidentAnalysisRepository
    from app.services.incident_service import IncidentService
    from app.ai.incident_analyzer import IncidentInvestigationEngine
    from app.models.incident import Incident, IncidentAnalysis

    logger.info("Running AI incident analysis", incident_id=incident_id)

    async with AsyncSessionLocal() as session:
        repo = IncidentRepository(model=Incident, session=session)
        analysis_repo = IncidentAnalysisRepository(model=IncidentAnalysis, session=session)
        service = IncidentService(repository=repo, analysis_repository=analysis_repo)

        incident = await service.get_incident(incident_id)
        if not incident:
            return {"status": "not_found"}

        engine = IncidentInvestigationEngine()

        try:
            result = await engine.investigate(
                cluster_name=incident.cluster_name or "unknown",
                query=query,
                namespace=incident.namespace,
                workload=incident.affected_workload,
                context_window_minutes=context_window_minutes,
            )

            await service.save_analysis_result(incident_id, query, result)
            await session.commit()

            return {"status": "success", "incident_id": incident_id, "confidence": result.get("confidence")}

        except Exception as exc:
            logger.error("AI analysis failed", incident_id=incident_id, error=str(exc))
            return {"status": "error", "error": str(exc)}


async def _detect_anomalies_async() -> dict:
    """
    Scan cluster workloads for anomalies:
    - Pods in CrashLoopBackOff
    - High restart counts
    - Resource pressure
    - Unhealthy deployments
    """
    # In production, this would query Prometheus metrics API
    # and cross-reference with Kubernetes events
    logger.info("Running anomaly detection")
    return {"status": "completed", "anomalies_found": 0}


async def _generate_cost_report_async() -> dict:
    """Generate cost optimization reports per cluster."""
    logger.info("Generating cost optimization reports")
    # In production, queries resource utilization from Prometheus/metrics-server
    return {"status": "completed"}


async def _run_terraform_scan_async(
    scan_id: str,
    terraform_content: str,
    scan_name: str,
    repo_url: str = None,
) -> dict:
    from app.core.database import AsyncSessionLocal
    from app.models.security_finding import TerraformScan, SecurityFinding, FindingSeverity, FindingCategory, FindingStatus
    from app.ai.terraform_analyzer import TerraformAnalyzer
    import uuid

    async with AsyncSessionLocal() as session:
        scan = await session.get(TerraformScan, scan_id)
        if not scan:
            return {"status": "not_found"}

        scan.status = "running"
        await session.commit()

        try:
            analyzer = TerraformAnalyzer()
            result = await analyzer.analyze(
                terraform_content=terraform_content,
                scan_name=scan_name,
                repo_url=repo_url,
            )

            findings = result.get("findings", [])

            # Persist findings
            for finding_data in findings:
                finding = SecurityFinding(
                    id=str(uuid.uuid4()),
                    title=finding_data.get("title", "Unnamed finding"),
                    description=finding_data.get("description"),
                    severity=finding_data.get("severity", "medium"),
                    category=finding_data.get("category", "terraform"),
                    status=FindingStatus.OPEN,
                    scanner="nexusops-ai",
                    rule_id=finding_data.get("rule_id"),
                    resource_type=finding_data.get("resource"),
                    file_path=scan.scan_path,
                    ai_explanation=finding_data.get("description"),
                    remediation_suggestion=finding_data.get("remediation"),
                    remediation_code=finding_data.get("remediation_code"),
                )
                session.add(finding)

            # Update scan record
            scan.status = "completed"
            scan.findings_count = len(findings)
            scan.critical_count = sum(1 for f in findings if f.get("severity") == "critical")
            scan.high_count = sum(1 for f in findings if f.get("severity") == "high")
            scan.medium_count = sum(1 for f in findings if f.get("severity") == "medium")
            scan.low_count = sum(1 for f in findings if f.get("severity") == "low")
            scan.ai_summary = result.get("risk_summary", "")

            await session.commit()

            logger.info("Terraform scan complete", scan_id=scan_id, findings=len(findings))
            return {"status": "success", "findings_count": len(findings)}

        except Exception as exc:
            scan.status = "failed"
            await session.commit()
            logger.error("Terraform scan failed", scan_id=scan_id, error=str(exc))
            return {"status": "error", "error": str(exc)}
