"""Cost optimization and resource intelligence engine."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from statistics import mean
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import select

from app.ai.llm_providers import LLMProviderFactory
from app.core.config import settings
from app.models.cluster import Cluster, KubernetesPod, KubernetesWorkload
from app.models.cost_recommendation import (
    CostRecommendation,
    OptimizationFinding,
    OptimizationReport,
    OptimizationRule,
    ResourceUtilization,
)
from app.models.telemetry import TelemetrySource
from app.repositories.cluster_repository import ClusterRepository
from app.repositories.optimization_repository import (
    CostRecommendationRepository,
    OptimizationFindingRepository,
    OptimizationReportRepository,
    OptimizationRuleRepository,
    ResourceUtilizationRepository,
)
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.optimization import OptimizationAnalyzeRequest, OptimizationDashboardStats
from app.services.infrastructure_discovery_service import InfrastructureDiscoveryService
from app.services.telemetry_service import TelemetryService

logger = structlog.get_logger(__name__)


class OptimizationService:
    """Analyze infrastructure and telemetry to generate cost recommendations."""

    CPU_CORE_MONTHLY_USD = 35.0
    MEMORY_GB_MONTHLY_USD = 4.0

    def __init__(
        self,
        utilization_repo: ResourceUtilizationRepository,
        rule_repo: OptimizationRuleRepository,
        finding_repo: OptimizationFindingRepository,
        recommendation_repo: CostRecommendationRepository,
        report_repo: OptimizationReportRepository,
        cluster_repo: ClusterRepository,
        telemetry_repo: TelemetryRepository,
    ):
        self.utilization_repo = utilization_repo
        self.rule_repo = rule_repo
        self.finding_repo = finding_repo
        self.recommendation_repo = recommendation_repo
        self.report_repo = report_repo
        self.cluster_repo = cluster_repo
        self.telemetry_repo = telemetry_repo

    @classmethod
    def from_session(cls, session):
        return cls(
            utilization_repo=ResourceUtilizationRepository(session),
            rule_repo=OptimizationRuleRepository(session),
            finding_repo=OptimizationFindingRepository(session),
            recommendation_repo=CostRecommendationRepository(session),
            report_repo=OptimizationReportRepository(session),
            cluster_repo=ClusterRepository(model=Cluster, session=session),
            telemetry_repo=TelemetryRepository(model=TelemetrySource, session=session),
        )

    async def analyze(
        self, request: OptimizationAnalyzeRequest
    ) -> tuple[OptimizationReport, list[OptimizationFinding], list[CostRecommendation], list[ResourceUtilization], OptimizationDashboardStats]:
        clusters = await self._clusters_for_analysis(request)
        await self._seed_rules()
        report = await self._create_report(request, clusters)

        utilization = []
        for cluster in clusters:
            for workload in cluster.workloads:
                utilization.append(await self._snapshot_workload(cluster, workload, request.analysis_window_hours))

        findings = []
        for snapshot in utilization:
            findings.extend(await self._apply_rules(report, snapshot))

        recommendations = await self._recommend(report, findings)
        await self._enhance_recommendations(recommendations)
        self._finalize_report(report, utilization, findings, recommendations)
        await self.report_repo.save(report)

        stats = await self.stats()
        logger.info("Optimization analysis completed", report_id=report.id, findings=len(findings), recommendations=len(recommendations))
        return report, findings, recommendations, utilization, stats

    async def stats(self) -> OptimizationDashboardStats:
        total_recommendations = await self.recommendation_repo.count_recommendations()
        open_recommendations = await self.recommendation_repo.count_recommendations(status="open")
        implemented_recommendations = await self.recommendation_repo.count_recommendations(status="implemented")
        in_progress_recommendations = await self.recommendation_repo.count_recommendations(status="in_progress")
        total_findings = await self.finding_repo.count_findings()
        critical_findings = await self.finding_repo.count_findings(severity="critical")
        high_findings = await self.finding_repo.count_findings(severity="high")
        top = list(await self.recommendation_repo.list_recommendations(limit=5, status="open"))
        all_open = list(await self.recommendation_repo.list_recommendations(limit=1000, status="open"))
        monthly = round(sum(item.estimated_monthly_savings_usd or 0 for item in all_open), 2)
        severity_breakdown = {
            severity: await self.finding_repo.count_findings(severity=severity)
            for severity in ("critical", "high", "medium", "low", "info")
        }
        type_breakdown = {
            item: await self.finding_repo.count_findings(finding_type=item)
            for item in (
                "cpu_oversizing",
                "memory_oversizing",
                "excessive_replicas",
                "idle_service",
                "missing_autoscaling",
                "restart_waste",
            )
        }
        score = self._optimization_score(total_findings, monthly)
        return OptimizationDashboardStats(
            total_recommendations=total_recommendations,
            open_recommendations=open_recommendations,
            implemented_recommendations=implemented_recommendations,
            in_progress_recommendations=in_progress_recommendations,
            total_findings=total_findings,
            critical_findings=critical_findings,
            high_findings=high_findings,
            estimated_monthly_savings_usd=monthly,
            estimated_annual_savings_usd=round(monthly * 12, 2),
            optimization_score=score,
            severity_breakdown=severity_breakdown,
            type_breakdown=type_breakdown,
            top_recommendations=top,
        )

    async def _clusters_for_analysis(self, request: OptimizationAnalyzeRequest) -> list[Cluster]:
        clusters = list(await self.cluster_repo.get_active_clusters_with_topology())
        if not clusters or request.demo:
            discovery = InfrastructureDiscoveryService(repository=self.cluster_repo)
            await discovery.generate_demo_environment()
            clusters = list(await self.cluster_repo.get_active_clusters_with_topology())
            await TelemetryService(self.telemetry_repo, self.cluster_repo).generate_demo_telemetry()
            await self._shape_demo_cost_scenarios(clusters)
        if request.cluster_id:
            clusters = [cluster for cluster in clusters if cluster.id == request.cluster_id]
        if not clusters:
            raise ValueError("No clusters available for optimization analysis")
        return clusters

    async def _shape_demo_cost_scenarios(self, clusters: list[Cluster]) -> None:
        scenarios = {
            "api-gateway": {"cpu_request": 2200, "memory_request": 4096, "cpu_usage": 12.0, "memory_usage": 18.0, "replicas": 6},
            "cdn-controller": {"cpu_request": 900, "memory_request": 2048, "cpu_usage": 2.0, "memory_usage": 4.0, "replicas": 3},
            "ledger-worker": {"cpu_request": 1600, "memory_request": 3072, "cpu_usage": 18.0, "memory_usage": 29.0, "replicas": 4},
            "otel-collector": {"cpu_request": 1200, "memory_request": 2048, "cpu_usage": 22.0, "memory_usage": 24.0, "replicas": 5},
            "prometheus": {"cpu_request": 1800, "memory_request": 8192, "cpu_usage": 41.0, "memory_usage": 27.0, "replicas": 3},
        }
        for cluster in clusters:
            for workload in cluster.workloads:
                scenario = scenarios.get(workload.name)
                if not scenario:
                    continue
                workload.cpu_request_millicores = scenario["cpu_request"]
                workload.memory_request_mb = scenario["memory_request"]
                workload.cpu_limit_millicores = scenario["cpu_request"] * 2
                workload.memory_limit_mb = scenario["memory_request"] * 2
                workload.cpu_usage_percent = scenario["cpu_usage"]
                workload.memory_usage_percent = scenario["memory_usage"]
                workload.replicas_desired = scenario["replicas"]
                workload.replicas_ready = scenario["replicas"]
                workload.is_healthy = True
        await self.cluster_repo.session.flush()

    async def _create_report(self, request: OptimizationAnalyzeRequest, clusters: list[Cluster]) -> OptimizationReport:
        now = datetime.now(UTC)
        cluster_name = clusters[0].name if len(clusters) == 1 else None
        report = OptimizationReport(
            id=str(uuid4()),
            report_name=request.report_name or f"Optimization analysis {now:%Y-%m-%d %H:%M}",
            cluster_id=request.cluster_id,
            cluster_name=cluster_name,
            status="running",
            analysis_window_hours=request.analysis_window_hours,
            started_at=now,
        )
        return await self.report_repo.create(report)

    async def _snapshot_workload(
        self, cluster: Cluster, workload: KubernetesWorkload, window_hours: int
    ) -> ResourceUtilization:
        cpu_values = await self._metric_values(cluster.id, workload.namespace_name, workload.name, "cpu_usage_percent")
        memory_values = await self._metric_values(cluster.id, workload.namespace_name, workload.name, "memory_usage_percent")
        error_values = await self._metric_values(cluster.id, workload.namespace_name, workload.name, "error_rate_percent")
        requests = await self._metric_values(cluster.id, workload.namespace_name, workload.name, "request_count")

        cpu_avg = self._avg(cpu_values, workload.cpu_usage_percent)
        memory_avg = self._avg(memory_values, workload.memory_usage_percent)
        replicas = workload.replicas_desired or 1
        monthly_cost = self._monthly_cost(
            workload.cpu_request_millicores or 0,
            workload.memory_request_mb or 0,
            replicas,
        )
        snapshot = ResourceUtilization(
            id=str(uuid4()),
            cluster_id=cluster.id,
            cluster_name=cluster.name,
            namespace=workload.namespace_name,
            resource_type="workload",
            resource_name=workload.name,
            workload_kind=workload.kind,
            cpu_request_millicores=workload.cpu_request_millicores,
            memory_request_mb=workload.memory_request_mb,
            cpu_limit_millicores=workload.cpu_limit_millicores,
            memory_limit_mb=workload.memory_limit_mb,
            cpu_usage_avg_percent=cpu_avg,
            memory_usage_avg_percent=memory_avg,
            cpu_usage_p95_percent=self._p95(cpu_values, cpu_avg),
            memory_usage_p95_percent=self._p95(memory_values, memory_avg),
            request_count_avg=self._avg(requests, 0.0),
            error_rate_avg_percent=self._avg(error_values, 0.0),
            restart_count=await self._restart_count(workload),
            replicas_desired=workload.replicas_desired,
            replicas_ready=workload.replicas_ready,
            sample_count=max(len(cpu_values), len(memory_values)),
            observation_window_hours=window_hours,
            monthly_cost_estimate_usd=monthly_cost,
            metadata_={"image": workload.image, "healthy": workload.is_healthy},
        )
        return await self.utilization_repo.create(snapshot)

    async def _metric_values(self, cluster_id: str, namespace: str, workload: str, metric_name: str) -> list[float]:
        metrics = await self.telemetry_repo.list_metrics(
            cluster_id=cluster_id,
            namespace_name=namespace,
            deployment_name=workload,
            metric_name=metric_name,
            limit=200,
        )
        return [metric.value for metric in metrics]

    async def _restart_count(self, workload: KubernetesWorkload) -> int:
        result = await self.cluster_repo.session.execute(
            select(KubernetesPod).where(KubernetesPod.workload_id == workload.id)
        )
        return sum(pod.restart_count for pod in result.scalars().all())

    async def _seed_rules(self) -> None:
        rules = [
            ("cpu_oversizing", "right_sizing", "CPU request is materially higher than observed CPU usage.", "high", {"usage_threshold": 25}),
            ("memory_oversizing", "right_sizing", "Memory request is materially higher than observed memory usage.", "high", {"usage_threshold": 35}),
            ("excessive_replicas", "replica_optimization", "Replica count is high relative to demand.", "medium", {"replica_threshold": 4}),
            ("idle_service", "idle_removal", "Workload appears idle and may be scaled down or retired.", "critical", {"cpu_threshold": 5, "memory_threshold": 10}),
            ("missing_autoscaling", "autoscaling", "Workload has steady replicas and should use HPA/VPA guardrails.", "medium", {"replica_threshold": 3}),
            ("restart_waste", "reliability_waste", "Repeated restarts waste capacity and hide noisy failure loops.", "medium", {"restart_threshold": 5}),
        ]
        for name, rule_type, description, severity, parameters in rules:
            rule = await self.rule_repo.get_by_name(name)
            if not rule:
                await self.rule_repo.create(
                    OptimizationRule(
                        id=str(uuid4()),
                        name=name,
                        rule_type=rule_type,
                        description=description,
                        severity=severity,
                        parameters=parameters,
                        is_enabled=True,
                    )
                )

    async def _apply_rules(self, report: OptimizationReport, snapshot: ResourceUtilization) -> list[OptimizationFinding]:
        payloads = []
        cpu = snapshot.cpu_usage_avg_percent or 0
        memory = snapshot.memory_usage_avg_percent or 0
        request_count = snapshot.request_count_avg or 0
        replicas = snapshot.replicas_desired or 1
        if cpu < 25 and (snapshot.cpu_request_millicores or 0) >= 500:
            payloads.append(self._finding_payload(snapshot, "cpu_oversizing", "high", "CPU Oversizing", "CPU requests exceed observed usage.", "Right-size CPU requests based on p95 utilization plus headroom."))
        if memory < 35 and (snapshot.memory_request_mb or 0) >= 768:
            payloads.append(self._finding_payload(snapshot, "memory_oversizing", "high", "Memory Oversizing", "Memory requests exceed observed usage.", "Right-size memory requests based on p95 utilization plus headroom."))
        if replicas >= 4 and cpu < 45 and memory < 55:
            payloads.append(self._finding_payload(snapshot, "excessive_replicas", "medium", "Excessive Replicas", "Replica count appears higher than demand requires.", "Reduce baseline replicas and use autoscaling for bursts."))
        if cpu < 5 and memory < 10 and request_count < 20:
            payloads.append(self._finding_payload(snapshot, "idle_service", "critical", "Idle Service", "Workload appears idle across CPU, memory, and request signals.", "Scale to zero, suspend, or retire the service after owner validation."))
        if replicas >= 3 and cpu < 65 and "hpa" not in json.dumps(snapshot.metadata_ or {}).lower():
            payloads.append(self._finding_payload(snapshot, "missing_autoscaling", "medium", "Missing Autoscaling", "Static replica count may waste capacity during low demand.", "Add HPA or VPA recommendations with conservative minimum replicas."))
        if snapshot.restart_count >= 5:
            payloads.append(self._finding_payload(snapshot, "restart_waste", "medium", "Restart Waste", "Restart loops consume capacity without useful work.", "Fix the crash loop and reduce wasted restart churn."))

        findings = []
        for payload in payloads:
            rule = await self.rule_repo.get_by_name(payload["finding_type"])
            findings.append(
                await self.finding_repo.create(
                    OptimizationFinding(
                        id=str(uuid4()),
                        report_id=report.id,
                        rule_id=rule.id if rule else None,
                        utilization_id=snapshot.id,
                        cluster_id=snapshot.cluster_id,
                        cluster_name=snapshot.cluster_name,
                        namespace=snapshot.namespace,
                        resource_type=snapshot.resource_type,
                        resource_name=snapshot.resource_name,
                        **payload,
                    )
                )
            )
        return findings

    def _finding_payload(
        self,
        snapshot: ResourceUtilization,
        finding_type: str,
        severity: str,
        title: str,
        description: str,
        recommendation: str,
    ) -> dict[str, Any]:
        return {
            "finding_type": finding_type,
            "severity": severity,
            "title": title,
            "description": f"{description} Resource: {snapshot.namespace}/{snapshot.resource_name}.",
            "evidence": {
                "cpu_usage_avg_percent": snapshot.cpu_usage_avg_percent,
                "memory_usage_avg_percent": snapshot.memory_usage_avg_percent,
                "replicas": snapshot.replicas_desired,
                "request_count_avg": snapshot.request_count_avg,
                "monthly_cost_estimate_usd": snapshot.monthly_cost_estimate_usd,
            },
            "confidence_score": self._confidence(snapshot, finding_type),
            "estimated_monthly_savings_usd": self._estimated_savings(snapshot, finding_type),
            "recommendation": recommendation,
            "remediation": self._remediation(snapshot, finding_type),
            "ai_explanation": self._explanation(snapshot, title, recommendation),
        }

    async def _recommend(
        self, report: OptimizationReport, findings: list[OptimizationFinding]
    ) -> list[CostRecommendation]:
        recommendations = []
        for finding in findings:
            utilization = await self.utilization_repo.get(finding.utilization_id) if finding.utilization_id else None
            rec_cpu, rec_mem, rec_replicas = self._recommended_state(utilization, finding.finding_type)
            recommendation = CostRecommendation(
                id=str(uuid4()),
                report_id=report.id,
                finding_id=finding.id,
                cluster_id=finding.cluster_id,
                cluster_name=finding.cluster_name,
                namespace=finding.namespace,
                workload_name=finding.resource_name,
                workload_kind=utilization.workload_kind if utilization else None,
                resource_type=finding.resource_type,
                resource_name=finding.resource_name,
                optimization_type=self._optimization_type(finding.finding_type),
                status="open",
                severity=finding.severity,
                confidence_score=finding.confidence_score,
                title=finding.title,
                description=finding.description,
                recommendation=finding.recommendation,
                impact=self._impact(finding),
                current_cpu_request_millicores=utilization.cpu_request_millicores if utilization else None,
                current_memory_request_mb=utilization.memory_request_mb if utilization else None,
                current_cpu_usage_avg_percent=utilization.cpu_usage_avg_percent if utilization else None,
                current_memory_usage_avg_percent=utilization.memory_usage_avg_percent if utilization else None,
                current_replicas=utilization.replicas_desired if utilization else None,
                recommended_cpu_request_millicores=rec_cpu,
                recommended_memory_request_mb=rec_mem,
                recommended_replicas=rec_replicas,
                estimated_monthly_savings_usd=finding.estimated_monthly_savings_usd,
                estimated_cpu_savings_cores=self._cpu_savings(utilization, rec_cpu, rec_replicas),
                estimated_memory_savings_gb=self._memory_savings(utilization, rec_mem, rec_replicas),
                ai_explanation=finding.ai_explanation,
                remediation_yaml=self._remediation_yaml(utilization, rec_cpu, rec_mem, rec_replicas),
                evidence=finding.evidence,
                priority=self._priority(finding.severity, finding.estimated_monthly_savings_usd or 0),
            )
            recommendations.append(await self.recommendation_repo.create(recommendation))
        return recommendations

    async def _enhance_recommendations(self, recommendations: list[CostRecommendation]) -> None:
        for item in recommendations:
            item.ai_explanation = item.ai_explanation or self._deterministic_recommendation_explanation(item)
        if not recommendations or (settings.LLM_PROVIDER == "openai" and not self._has_openai_key()):
            return
        try:
            provider = LLMProviderFactory.create()
            payload = [
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "recommendation": item.recommendation,
                    "savings": item.estimated_monthly_savings_usd,
                    "evidence": item.evidence,
                }
                for item in recommendations[:8]
            ]
            response = await provider.analyze(
                system_prompt="Explain Kubernetes cost optimization recommendations as concise JSON keyed by id.",
                user_message=f"Return JSON array with id, explanation, impact, remediation:\n{json.dumps(payload, default=str)}",
            )
            parsed = self._parse_llm_json(response.get("content", ""))
            by_id = {item.get("id"): item for item in parsed}
            for item in recommendations:
                if item.id in by_id:
                    item.ai_explanation = by_id[item.id].get("explanation") or item.ai_explanation
                    item.impact = by_id[item.id].get("impact") or item.impact
                    item.recommendation = by_id[item.id].get("remediation") or item.recommendation
        except Exception as exc:
            logger.warning("Cost optimization AI enhancement failed; deterministic explanations retained", error=str(exc))

    def _finalize_report(
        self,
        report: OptimizationReport,
        utilization: list[ResourceUtilization],
        findings: list[OptimizationFinding],
        recommendations: list[CostRecommendation],
    ) -> None:
        monthly = round(sum(item.estimated_monthly_savings_usd or 0 for item in recommendations), 2)
        report.status = "completed"
        report.total_resources_analyzed = len(utilization)
        report.total_findings = len(findings)
        report.total_recommendations = len(recommendations)
        report.estimated_monthly_savings_usd = monthly
        report.estimated_annual_savings_usd = round(monthly * 12, 2)
        report.optimization_score = self._optimization_score(len(findings), monthly)
        report.severity_breakdown = self._count_by(findings, "severity")
        report.category_breakdown = self._count_by(findings, "finding_type")
        report.impacted_resources = [
            {"cluster": item.cluster_name, "namespace": item.namespace, "name": item.resource_name}
            for item in findings[:20]
        ]
        report.summary = (
            f"Analyzed {len(utilization)} resources and found {len(recommendations)} optimization "
            f"opportunities worth an estimated ${monthly:,.2f}/month."
        )
        report.completed_at = datetime.now(UTC)

    def _recommended_state(
        self, utilization: ResourceUtilization | None, finding_type: str
    ) -> tuple[int | None, int | None, int | None]:
        if not utilization:
            return None, None, None
        cpu = utilization.cpu_request_millicores
        memory = utilization.memory_request_mb
        replicas = utilization.replicas_desired
        if finding_type in {"cpu_oversizing", "idle_service"} and cpu:
            cpu = max(100, int(cpu * max(0.25, (utilization.cpu_usage_p95_percent or 20) / 70)))
        if finding_type in {"memory_oversizing", "idle_service"} and memory:
            memory = max(256, int(memory * max(0.35, (utilization.memory_usage_p95_percent or 30) / 75)))
        if finding_type in {"excessive_replicas", "idle_service", "missing_autoscaling"} and replicas:
            replicas = 0 if finding_type == "idle_service" else max(2, math.ceil(replicas * 0.6))
        return cpu, memory, replicas

    def _estimated_savings(self, snapshot: ResourceUtilization, finding_type: str) -> float:
        rec_cpu, rec_mem, rec_replicas = self._recommended_state(snapshot, finding_type)
        current = snapshot.monthly_cost_estimate_usd or 0
        optimized = self._monthly_cost(
            rec_cpu if rec_cpu is not None else snapshot.cpu_request_millicores or 0,
            rec_mem if rec_mem is not None else snapshot.memory_request_mb or 0,
            rec_replicas if rec_replicas is not None else snapshot.replicas_desired or 1,
        )
        return round(max(0, current - optimized), 2)

    def _monthly_cost(self, cpu_millicores: int, memory_mb: int, replicas: int) -> float:
        cpu_cost = (cpu_millicores / 1000) * self.CPU_CORE_MONTHLY_USD
        mem_cost = (memory_mb / 1024) * self.MEMORY_GB_MONTHLY_USD
        return round((cpu_cost + mem_cost) * max(replicas, 0), 2)

    def _cpu_savings(self, utilization: ResourceUtilization | None, rec_cpu: int | None, rec_replicas: int | None) -> float | None:
        if not utilization or rec_cpu is None:
            return None
        current = (utilization.cpu_request_millicores or 0) * (utilization.replicas_desired or 1)
        recommended = rec_cpu * (rec_replicas if rec_replicas is not None else utilization.replicas_desired or 1)
        return round(max(0, current - recommended) / 1000, 2)

    def _memory_savings(self, utilization: ResourceUtilization | None, rec_mem: int | None, rec_replicas: int | None) -> float | None:
        if not utilization or rec_mem is None:
            return None
        current = (utilization.memory_request_mb or 0) * (utilization.replicas_desired or 1)
        recommended = rec_mem * (rec_replicas if rec_replicas is not None else utilization.replicas_desired or 1)
        return round(max(0, current - recommended) / 1024, 2)

    def _optimization_type(self, finding_type: str) -> str:
        mapping = {
            "cpu_oversizing": "right_sizing",
            "memory_oversizing": "right_sizing",
            "excessive_replicas": "right_sizing",
            "idle_service": "idle_removal",
            "missing_autoscaling": "autoscaling",
            "restart_waste": "right_sizing",
        }
        return mapping.get(finding_type, "right_sizing")

    def _remediation(self, snapshot: ResourceUtilization, finding_type: str) -> str:
        if finding_type == "idle_service":
            return f"Validate ownership for {snapshot.namespace}/{snapshot.resource_name}, then scale down or remove the deployment."
        if finding_type == "missing_autoscaling":
            return f"Create an HPA for {snapshot.namespace}/{snapshot.resource_name} with conservative min replicas."
        return f"Patch {snapshot.namespace}/{snapshot.resource_name} resource requests and replica baseline after canary validation."

    def _remediation_yaml(
        self, utilization: ResourceUtilization | None, cpu: int | None, memory: int | None, replicas: int | None
    ) -> str | None:
        if not utilization:
            return None
        patch = {
            "spec": {
                "replicas": replicas,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": utilization.resource_name,
                                "resources": {
                                    "requests": {
                                        "cpu": f"{cpu}m" if cpu is not None else None,
                                        "memory": f"{memory}Mi" if memory is not None else None,
                                    }
                                },
                            }
                        ]
                    }
                },
            }
        }
        return json.dumps(patch, indent=2)

    def _impact(self, finding: OptimizationFinding) -> str:
        savings = finding.estimated_monthly_savings_usd or 0
        return f"Expected monthly savings of ${savings:,.2f} and lower scheduling pressure for {finding.resource_name}."

    def _priority(self, severity: str, savings: float) -> int:
        base = {"critical": 1, "high": 2, "medium": 4, "low": 6}.get(severity, 7)
        if savings > 500:
            return max(1, base - 1)
        return base

    def _confidence(self, snapshot: ResourceUtilization, finding_type: str) -> float:
        samples = snapshot.sample_count or 0
        base = 0.72 + min(samples, 24) * 0.006
        if finding_type == "idle_service":
            base += 0.08
        return round(min(0.95, base), 2)

    def _explanation(self, snapshot: ResourceUtilization, title: str, recommendation: str) -> str:
        return (
            f"{title} is based on {snapshot.observation_window_hours}h of utilization for "
            f"{snapshot.namespace}/{snapshot.resource_name}. {recommendation}"
        )

    def _deterministic_recommendation_explanation(self, item: CostRecommendation) -> str:
        return (
            f"{item.title}: observed CPU {item.current_cpu_usage_avg_percent}% and memory "
            f"{item.current_memory_usage_avg_percent}% against requested capacity. "
            f"Estimated savings are ${item.estimated_monthly_savings_usd or 0:,.2f}/month."
        )

    def _avg(self, values: list[float], fallback: float | None) -> float:
        if values:
            return round(mean(values), 2)
        return round(fallback or 0.0, 2)

    def _p95(self, values: list[float], fallback: float) -> float:
        if not values:
            return round(fallback, 2)
        ordered = sorted(values)
        index = min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1)
        return round(ordered[index], 2)

    def _count_by(self, rows: list[Any], attr: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            value = getattr(row, attr)
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _optimization_score(self, findings: int, monthly_savings: float) -> float:
        return round(max(0, min(100, 100 - findings * 3 - monthly_savings / 250)), 1)

    def _parse_llm_json(self, content: str) -> list[dict[str, Any]]:
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`").removeprefix("json").strip()
        parsed = json.loads(content)
        return parsed if isinstance(parsed, list) else []

    def _has_openai_key(self) -> bool:
        key = settings.OPENAI_API_KEY.strip()
        return bool(key and not key.startswith("sk-your-"))
