"""Phase 9 hardening coverage for core platform engines."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.ai.evidence_collector import EvidenceCollector
from app.infrastructure.providers.demo import DemoProvider
from app.models.cost_recommendation import OptimizationFinding, ResourceUtilization
from app.models.investigation import InvestigationEvidence
from app.models.telemetry import InfrastructureEvent, LogEntry, Metric, Trace
from app.models.terraform import TerraformResource
from app.services.investigation_service import InvestigationService
from app.services.optimization_service import OptimizationService
from app.services.terraform_service import TerraformAnalysisService


def _optimization_service() -> OptimizationService:
    return OptimizationService(None, None, None, None, None, None, None)


def _terraform_service() -> TerraformAnalysisService:
    return TerraformAnalysisService(None, None, None, None, None, None)


def test_demo_provider_generates_reconstructable_enterprise_topology():
    snapshots = DemoProvider().discover_all()

    assert len(snapshots) == 3
    assert {snapshot.cluster["environment"] for snapshot in snapshots} == {
        "production",
        "staging",
        "shared-services",
    }
    assert any(pod["phase"] == "CrashLoopBackOff" for snapshot in snapshots for pod in snapshot.pods)
    assert all(snapshot.deployments for snapshot in snapshots)
    assert all(snapshot.nodes for snapshot in snapshots)
    assert all(snapshot.services for snapshot in snapshots)


def test_evidence_collector_promotes_high_signal_metrics():
    now = datetime.now(UTC)
    metrics = [
        Metric(
            id=f"metric-{index}",
            timestamp=now - timedelta(minutes=index),
            metric_name="memory_usage_percent",
            value=value,
            unit="percent",
            resource_type="deployment",
            resource_name="checkout-api",
            cluster_id="cluster-1",
            namespace_name="payments",
            deployment_name="checkout-api",
        )
        for index, value in enumerate([91, 95, 87, 83])
    ]

    evidence = EvidenceCollector(None)._metric_evidence(metrics)

    assert len(evidence) == 1
    assert evidence[0].severity == "critical"
    assert "Memory pressure" in evidence[0].title
    assert evidence[0].metadata_["peak"] == 95


def test_evidence_collector_filters_noise_logs_and_keeps_errors():
    now = datetime.now(UTC)
    logs = [
        LogEntry(
            id="log-info",
            timestamp=now,
            severity="info",
            source="app",
            message="request completed",
            deployment_name="checkout-api",
        ),
        LogEntry(
            id="log-error",
            timestamp=now,
            severity="error",
            source="app",
            message="database connection pool exhausted",
            deployment_name="checkout-api",
            pod_name="checkout-api-1",
        ),
    ]

    evidence = EvidenceCollector(None)._log_evidence(logs)

    assert len(evidence) == 1
    assert evidence[0].severity == "critical"
    assert evidence[0].resource_name == "checkout-api-1"


def test_evidence_collector_converts_warning_events_and_failed_traces():
    now = datetime.now(UTC)
    collector = EvidenceCollector(None)
    events = [
        InfrastructureEvent(
            id="event-1",
            timestamp=now,
            event_type="kubernetes",
            reason="ReplicaSetDegraded",
            severity="warning",
            message="ReplicaSet has fewer ready pods than desired.",
            resource_type="deployment",
            resource_name="checkout-api",
            namespace_name="payments",
        )
    ]
    traces = [
        Trace(
            id="trace-1",
            trace_id="trace-1",
            span_id="span-1",
            operation_name="POST /checkout",
            service_name="checkout-api",
            status="error",
            start_time=now,
            end_time=now + timedelta(milliseconds=940),
            duration_ms=940,
            namespace_name="payments",
            deployment_name="checkout-api",
        )
    ]

    event_evidence = collector._event_evidence(events)
    trace_evidence = collector._trace_evidence(traces)

    assert event_evidence[0].severity == "high"
    assert "ReplicaSetDegraded" in event_evidence[0].title
    assert trace_evidence[0].severity == "critical"
    assert trace_evidence[0].metadata_["trace_id"] == "trace-1"


def test_investigation_fallback_prioritizes_metric_evidence():
    evidence = [
        InvestigationEvidence(
            id="evidence-1",
            investigation_id="investigation-1",
            evidence_type="metric",
            severity="high",
            title="CPU pressure peaked at 94.0%",
            description="cpu_usage_percent averaged 91.1 with peak 94.0.",
            resource_type="deployment",
            resource_name="checkout-api",
            namespace_name="payments",
            observed_at=datetime.now(UTC),
        )
    ]
    service = InvestigationService(None, None, None, None, None)

    analysis = service._fallback_analysis(
        context={"incident": {"title": "Checkout latency", "severity": "high"}},
        evidence=evidence,
        provider_name="openai:not_configured",
    )

    assert analysis["severity"] == "high"
    assert analysis["confidence"] > 0.5
    assert "strongest correlated signal" in analysis["root_cause"]
    assert analysis["affected_resources"][0]["name"] == "checkout-api"


def test_investigation_json_parser_normalizes_remediation_dict():
    service = InvestigationService(None, None, None, None, None)

    parsed = service._parse_json(
        """```json
        {
          "summary": "checkout-api is degraded",
          "root_cause": "Database saturation",
          "severity": "critical",
          "confidence": 0.86,
          "remediation": {
            "immediate": "Roll back checkout-api",
            "long_term": "Increase database pool limits"
          }
        }
        ```"""
    )

    assert parsed["severity"] == "critical"
    assert parsed["confidence"] == 0.86
    assert parsed["remediation_recommendations"][0]["title"] == "Immediate"


def test_terraform_parser_detects_multiple_resource_types():
    service = _terraform_service()
    files, _ = service.demo_environment()

    resources = service._parse_resources(files)
    addresses = {item["address"] for item in resources}

    assert "aws_db_instance.orders" in addresses
    assert "aws_iam_policy.platform_admin" in addresses
    assert "kubernetes_deployment.checkout" in addresses
    assert service._infer_provider(files) == "aws"


def test_terraform_security_helpers_detect_core_risks():
    service = _terraform_service()
    resource = TerraformResource(
        id="resource-1",
        workspace_id="workspace-1",
        address="aws_db_instance.orders",
        type="aws_db_instance",
        name="orders",
        desired_config={"publicly_accessible": True, "storage_encrypted": False},
        file_path="main.tf",
        line_number=1,
    )

    findings = service._resource_security_findings(resource, resource.desired_config)
    titles = {finding["title"] for finding in findings}

    assert "Database is publicly accessible" in titles
    assert "Missing encryption at rest" in titles
    assert service._impact_for("critical").startswith("Could allow")


def test_terraform_secret_and_drift_detection():
    service = _terraform_service()
    secret_findings = service._secret_findings({"main.tf": 'variable "db" { password = "supersecret" }'})
    resource = TerraformResource(
        id="resource-1",
        workspace_id="workspace-1",
        address="kubernetes_deployment.checkout",
        type="kubernetes_deployment",
        name="checkout",
        desired_config={"spec": [{"replicas": 3}]},
        actual_state={"spec": [{"replicas": 6}]},
    )

    drift = service._detect_drift([resource])

    assert secret_findings[0]["category"] == "secrets"
    assert drift[0]["attribute_path"] == "spec.replicas"
    assert drift[0]["severity"] == "high"


def test_optimization_cost_math_and_recommended_state():
    service = _optimization_service()
    snapshot = ResourceUtilization(
        id="util-1",
        cluster_id="cluster-1",
        cluster_name="prod",
        namespace="payments",
        resource_type="workload",
        resource_name="checkout-api",
        workload_kind="Deployment",
        cpu_request_millicores=2000,
        memory_request_mb=4096,
        cpu_usage_avg_percent=10,
        memory_usage_avg_percent=20,
        cpu_usage_p95_percent=18,
        memory_usage_p95_percent=25,
        request_count_avg=10,
        replicas_desired=5,
        sample_count=24,
        observation_window_hours=24,
        monthly_cost_estimate_usd=430,
    )

    rec_cpu, rec_mem, rec_replicas = service._recommended_state(snapshot, "idle_service")

    assert service._monthly_cost(1000, 1024, 2) == 78.0
    assert rec_cpu == 514
    assert rec_mem == 1433
    assert rec_replicas == 0
    assert service._estimated_savings(snapshot, "idle_service") == 430


def test_optimization_report_summary_and_priority():
    service = _optimization_service()
    report = SimpleNamespace(status="running")
    finding = OptimizationFinding(
        id="finding-1",
        resource_type="workload",
        resource_name="checkout-api",
        finding_type="cpu_oversizing",
        severity="high",
        title="CPU Oversizing",
        description="CPU requests exceed observed usage.",
        estimated_monthly_savings_usd=650,
        cluster_name="prod",
        namespace="payments",
    )

    service._finalize_report(report, [], [finding], [])

    assert service._priority("high", 650) == 1
    assert report.status == "completed"
    assert report.total_findings == 1
    assert report.estimated_monthly_savings_usd == 0
    assert report.severity_breakdown == {"high": 1}
    assert report.impacted_resources[0]["name"] == "checkout-api"
