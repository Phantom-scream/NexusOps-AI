"""Terraform security, policy, and drift analysis services."""

from __future__ import annotations

import io
import json
import re
from typing import Any
from uuid import uuid4

import hcl2
import httpx
import structlog

from app.ai.llm_providers import LLMProviderFactory
from app.core.config import settings
from app.models.security_finding import TerraformScan
from app.models.terraform import (
    TerraformDrift,
    TerraformFinding,
    TerraformPolicyViolation,
    TerraformResource,
    TerraformWorkspace,
)
from app.repositories.terraform_repository import (
    TerraformDriftRepository,
    TerraformFindingRepository,
    TerraformPolicyViolationRepository,
    TerraformResourceRepository,
    TerraformScanRepository,
    TerraformWorkspaceRepository,
)
from app.schemas.terraform import (
    TerraformAnalyzeRequest,
    TerraformDashboardStats,
    TerraformUploadRequest,
)

logger = structlog.get_logger(__name__)


class TerraformAnalysisService:
    """Coordinates Terraform ingestion, security analysis, policy checks, and drift detection."""

    def __init__(
        self,
        workspace_repo: TerraformWorkspaceRepository,
        resource_repo: TerraformResourceRepository,
        finding_repo: TerraformFindingRepository,
        drift_repo: TerraformDriftRepository,
        scan_repo: TerraformScanRepository,
        policy_repo: TerraformPolicyViolationRepository,
    ):
        self.workspace_repo = workspace_repo
        self.resource_repo = resource_repo
        self.finding_repo = finding_repo
        self.drift_repo = drift_repo
        self.scan_repo = scan_repo
        self.policy_repo = policy_repo

    @classmethod
    def from_session(cls, session):
        return cls(
            workspace_repo=TerraformWorkspaceRepository(session),
            resource_repo=TerraformResourceRepository(session),
            finding_repo=TerraformFindingRepository(session),
            drift_repo=TerraformDriftRepository(session),
            scan_repo=TerraformScanRepository(session),
            policy_repo=TerraformPolicyViolationRepository(session),
        )

    async def upload(self, data: TerraformUploadRequest) -> tuple[TerraformWorkspace, list[TerraformResource]]:
        files = self._normalize_files(data.files, data.terraform_content)
        workspace = TerraformWorkspace(
            id=str(uuid4()),
            name=data.name,
            description=data.description,
            source_type=data.source_type,
            repository_url=data.repository_url,
            branch=data.branch,
            root_path=data.root_path,
            provider=data.provider or self._infer_provider(files),
            environment=data.environment,
            owner=data.owner,
            metadata_=data.metadata or {},
        )
        await self.workspace_repo.create(workspace)
        scan = await self._create_scan(workspace, data.name, data.source_type, data.repository_url, data.branch, data.root_path)
        resources = await self._persist_resources(workspace, scan, files, data.state)
        scan.status = "uploaded"
        await self.scan_repo.save(scan)
        workspace.last_scan_id = scan.id
        await self.workspace_repo.save(workspace)
        return workspace, resources

    async def analyze(
        self, data: TerraformAnalyzeRequest
    ) -> tuple[
        TerraformWorkspace,
        TerraformScan,
        list[TerraformResource],
        list[TerraformFinding],
        list[TerraformDrift],
        list[TerraformPolicyViolation],
        TerraformDashboardStats,
    ]:
        if data.demo:
            files, state = self.demo_environment()
            data.files = files
            data.state = state
            data.workspace_name = data.workspace_name or "demo-enterprise-terraform"

        files = self._normalize_files(data.files, data.terraform_content)
        if not files and not data.workspace_id:
            raise ValueError("Terraform files or workspace_id are required")

        workspace = await self._get_or_create_workspace(data, files)
        scan = await self._create_scan(
            workspace,
            data.scan_name or f"{workspace.name} analysis",
            workspace.source_type,
            workspace.repository_url,
            workspace.branch,
            workspace.root_path,
        )

        resources = await self._persist_resources(workspace, scan, files, data.state)
        if not resources:
            resources = list(await self.resource_repo.list_for_workspace(workspace.id))

        finding_payloads = self._security_findings(resources, files)
        opa_payloads = await self._opa_policy_violations(resources)
        policy_violations = await self._persist_policy_violations(workspace, scan, opa_payloads)
        finding_payloads.extend(self._findings_from_policy_violations(policy_violations))
        finding_payloads = await self._explain_findings(finding_payloads)
        findings = await self._persist_findings(workspace, scan, resources, finding_payloads)

        drift_payloads = self._detect_drift(resources)
        drift_records = await self._persist_drift(workspace, scan, resources, drift_payloads)

        self._finalize_scan(scan, findings, drift_records, policy_violations)
        await self.scan_repo.save(scan)
        workspace.last_scan_id = scan.id
        await self.workspace_repo.save(workspace)

        stats = await self.stats()
        logger.info("Terraform analysis completed", scan_id=scan.id, findings=len(findings), drift=len(drift_records))
        return workspace, scan, resources, findings, drift_records, policy_violations, stats

    async def stats(self) -> TerraformDashboardStats:
        total_workspaces = await self.workspace_repo.count()
        total_resources = await self.resource_repo.count()
        total_findings = await self.finding_repo.count_findings()
        open_findings = await self.finding_repo.count_findings(status="open")
        critical_findings = await self.finding_repo.count_findings(severity="critical")
        high_findings = await self.finding_repo.count_findings(severity="high")
        drift_count = await self.drift_repo.count_drift(status="open")
        policy_violation_count = await self.policy_repo.count()
        severity_breakdown = {
            severity: await self.finding_repo.count_findings(severity=severity)
            for severity in ("critical", "high", "medium", "low", "info")
        }
        categories = ("iam", "network", "encryption", "secrets", "kubernetes", "rbac", "compliance", "policy", "drift")
        category_breakdown = {
            category: await self.finding_repo.count_findings(category=category)
            for category in categories
        }
        return TerraformDashboardStats(
            total_workspaces=total_workspaces,
            total_resources=total_resources,
            total_findings=total_findings,
            open_findings=open_findings,
            critical_findings=critical_findings,
            high_findings=high_findings,
            drift_count=drift_count,
            policy_violation_count=policy_violation_count,
            severity_breakdown=severity_breakdown,
            category_breakdown=category_breakdown,
        )

    def demo_environment(self) -> tuple[dict[str, str], dict[str, Any]]:
        return {
            "main.tf": DEMO_TERRAFORM_MAIN,
            "kubernetes.tf": DEMO_TERRAFORM_KUBERNETES,
        }, DEMO_TERRAFORM_STATE

    async def _get_or_create_workspace(self, data: TerraformAnalyzeRequest, files: dict[str, str]) -> TerraformWorkspace:
        if data.workspace_id:
            workspace = await self.workspace_repo.get(data.workspace_id)
            if not workspace:
                raise ValueError("Terraform workspace not found")
            return workspace
        workspace = TerraformWorkspace(
            id=str(uuid4()),
            name=data.workspace_name or "terraform-upload",
            description="Terraform workspace generated from analysis request",
            source_type="demo" if data.demo else "upload",
            provider=self._infer_provider(files),
            environment="demo" if data.demo else None,
        )
        return await self.workspace_repo.create(workspace)

    async def _create_scan(
        self,
        workspace: TerraformWorkspace,
        scan_name: str,
        source_type: str,
        repository_url: str | None,
        branch: str | None,
        scan_path: str | None,
    ) -> TerraformScan:
        scan = TerraformScan(
            id=str(uuid4()),
            workspace_id=workspace.id,
            scan_name=scan_name,
            source_type=source_type,
            repository_url=repository_url,
            branch=branch,
            scan_path=scan_path,
            status="running",
        )
        return await self.scan_repo.create(scan)

    async def _persist_resources(
        self,
        workspace: TerraformWorkspace,
        scan: TerraformScan,
        files: dict[str, str],
        state: dict[str, Any] | None,
    ) -> list[TerraformResource]:
        parsed = self._parse_resources(files)
        resources = []
        for item in parsed:
            actual_state = self._actual_state_for(item["address"], state)
            resource = TerraformResource(
                id=str(uuid4()),
                workspace_id=workspace.id,
                scan_id=scan.id,
                address=item["address"],
                type=item["type"],
                name=item["name"],
                provider=item["provider"],
                module=item.get("module"),
                file_path=item.get("file_path"),
                line_number=item.get("line_number"),
                desired_config=item["config"],
                actual_state=actual_state,
                drift_status="in_sync" if actual_state else "not_ingested",
            )
            resources.append(await self.resource_repo.create(resource))
        return resources

    def _parse_resources(self, files: dict[str, str]) -> list[dict[str, Any]]:
        resources = []
        for file_path, content in files.items():
            try:
                parsed = hcl2.load(io.StringIO(content))
            except Exception as exc:
                logger.warning("Failed to parse Terraform file", file_path=file_path, error=str(exc))
                continue

            for block in parsed.get("resource", []):
                for resource_type, named_blocks in block.items():
                    for name, config in named_blocks.items():
                        address = f"{resource_type}.{name}"
                        resources.append(
                            {
                                "address": address,
                                "type": resource_type,
                                "name": name,
                                "provider": resource_type.split("_", 1)[0] if "_" in resource_type else None,
                                "file_path": file_path,
                                "line_number": self._line_number(content, resource_type, name),
                                "config": config,
                            }
                        )
        return resources

    def _security_findings(self, resources: list[TerraformResource], files: dict[str, str]) -> list[dict[str, Any]]:
        findings = []
        for resource in resources:
            config = resource.desired_config or {}
            findings.extend(self._resource_security_findings(resource, config))
        findings.extend(self._secret_findings(files))
        return findings

    def _resource_security_findings(self, resource: TerraformResource, config: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        if resource.type in {"aws_security_group_rule", "aws_security_group"} and self._has_public_ingress(config):
            findings.append(self._finding(resource, "NEXOPS-TF-NET-001", "critical", "network", "Public ingress exposure", "Resource allows inbound traffic from 0.0.0.0/0.", "Restrict ingress CIDR ranges to approved networks."))
        if resource.type in {"aws_iam_policy", "aws_iam_role_policy", "aws_iam_user_policy"} and "*" in json.dumps(config):
            findings.append(self._finding(resource, "NEXOPS-TF-IAM-001", "critical", "iam", "Wildcard IAM permission detected", "IAM policy grants wildcard actions or resources.", "Replace wildcard actions/resources with least-privilege permissions."))
        if resource.type in {"aws_s3_bucket", "aws_db_instance", "aws_ebs_volume"} and self._missing_encryption(resource.type, config):
            findings.append(self._finding(resource, "NEXOPS-TF-ENC-001", "high", "encryption", "Missing encryption at rest", "Resource does not explicitly enable encryption.", "Enable encryption and attach a customer-managed KMS key where required."))
        if resource.type == "aws_db_instance" and config.get("publicly_accessible") is True:
            findings.append(self._finding(resource, "NEXOPS-TF-NET-002", "critical", "network", "Database is publicly accessible", "RDS instance is reachable from public networks.", "Set publicly_accessible = false and route access through private subnets."))
        if resource.type in {"kubernetes_pod", "kubernetes_deployment"} and self._is_privileged(config):
            findings.append(self._finding(resource, "NEXOPS-TF-K8S-001", "high", "kubernetes", "Privileged Kubernetes workload", "Container security context enables privileged execution or root user.", "Disable privileged mode, set runAsNonRoot, and use a restricted Pod Security profile."))
        if resource.type in {"kubernetes_pod", "kubernetes_deployment"} and not self._has_resource_limits(config):
            findings.append(self._finding(resource, "NEXOPS-TF-K8S-002", "medium", "kubernetes", "Missing Kubernetes resource limits", "Workload does not define CPU and memory limits.", "Define resource requests and limits for every container."))
        if resource.type in {"kubernetes_cluster_role", "kubernetes_role"} and "*" in json.dumps(config):
            findings.append(self._finding(resource, "NEXOPS-TF-RBAC-001", "high", "rbac", "Overly permissive Kubernetes RBAC", "Role grants wildcard verbs or resources.", "Scope RBAC verbs and resources to the minimum operational need."))
        return findings

    def _finding(
        self,
        resource: TerraformResource,
        rule_id: str,
        severity: str,
        category: str,
        title: str,
        description: str,
        remediation: str,
    ) -> dict[str, Any]:
        return {
            "rule_id": rule_id,
            "severity": severity,
            "category": category,
            "title": title,
            "description": description,
            "impact": self._impact_for(severity),
            "remediation": remediation,
            "resource_address": resource.address,
            "resource_type": resource.type,
            "file_path": resource.file_path,
            "line_number": resource.line_number,
            "scanner": "nexusops-static",
            "confidence_score": 0.9,
            "raw_finding": {"desired_config": resource.desired_config},
        }

    def _secret_findings(self, files: dict[str, str]) -> list[dict[str, Any]]:
        findings = []
        pattern = re.compile(r'(?i)(password|secret|api_key|access_key)\s*=\s*"([^"$][^"]{5,})"')
        for file_path, content in files.items():
            for match in pattern.finditer(content):
                findings.append(
                    {
                        "rule_id": "NEXOPS-TF-SEC-001",
                        "severity": "critical",
                        "category": "secrets",
                        "title": "Hardcoded secret in Terraform",
                        "description": f"Terraform variable `{match.group(1)}` appears to contain a literal secret.",
                        "impact": "Secrets committed to IaC can leak through source control, CI logs, and Terraform state.",
                        "remediation": "Move secrets to Vault, cloud secret managers, or environment-backed variables.",
                        "resource_address": None,
                        "resource_type": None,
                        "file_path": file_path,
                        "line_number": content[: match.start()].count("\n") + 1,
                        "scanner": "nexusops-secret-scan",
                        "confidence_score": 0.86,
                        "raw_finding": {"match": match.group(1)},
                    }
                )
        return findings

    async def _opa_policy_violations(self, resources: list[TerraformResource]) -> list[dict[str, Any]]:
        plan = {
            "resource_changes": [
                {
                    "address": resource.address,
                    "type": resource.type,
                    "change": {"after": resource.desired_config or {}},
                }
                for resource in resources
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                response = await client.post(
                    f"{settings.OPA_SERVER_URL.rstrip('/')}/v1/data/nexusops/terraform/security",
                    json={"input": plan},
                )
                response.raise_for_status()
                result = response.json().get("result", {})
                return self._normalize_opa_result(result, plan)
        except Exception as exc:
            logger.warning("OPA evaluation unavailable; using local policy mirror", error=str(exc))
            return self._local_policy_violations(resources, plan)

    def _normalize_opa_result(self, result: dict[str, Any], input_document: dict[str, Any]) -> list[dict[str, Any]]:
        violations = []
        for bucket, default_severity in (("deny", "high"), ("warn", "medium")):
            for message in result.get(bucket, []):
                severity = self._severity_from_message(message, default_severity)
                violations.append(
                    {
                        "policy_name": "nexusops.terraform.security",
                        "rule_id": f"OPA-{bucket.upper()}",
                        "message": message,
                        "severity": severity,
                        "resource_address": self._resource_from_message(message),
                        "input_document": input_document,
                        "opa_result": result,
                    }
                )
        return violations

    def _local_policy_violations(self, resources: list[TerraformResource], input_document: dict[str, Any]) -> list[dict[str, Any]]:
        violations = []
        for resource in resources:
            config = resource.desired_config or {}
            if resource.type == "aws_security_group_rule" and self._has_public_ingress(config):
                violations.append(self._policy_violation(resource, "CRITICAL: SSH or public ingress open to the internet", "critical", input_document))
            if resource.type == "aws_db_instance" and config.get("publicly_accessible") is True:
                violations.append(self._policy_violation(resource, "CRITICAL: RDS instance is publicly accessible", "critical", input_document))
            if resource.type == "aws_db_instance" and not config.get("storage_encrypted"):
                violations.append(self._policy_violation(resource, "HIGH: RDS storage encryption is missing", "high", input_document))
        return violations

    def _policy_violation(
        self, resource: TerraformResource, message: str, severity: str, input_document: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "policy_name": "nexusops.terraform.security",
            "rule_id": "OPA-LOCAL",
            "message": f"{message} in resource {resource.address}",
            "severity": severity,
            "resource_address": resource.address,
            "input_document": input_document,
            "opa_result": {"source": "local_mirror"},
        }

    async def _persist_policy_violations(
        self, workspace: TerraformWorkspace, scan: TerraformScan, payloads: list[dict[str, Any]]
    ) -> list[TerraformPolicyViolation]:
        records = []
        for payload in payloads:
            records.append(
                await self.policy_repo.create(
                    TerraformPolicyViolation(
                        id=str(uuid4()),
                        workspace_id=workspace.id,
                        scan_id=scan.id,
                        policy_name=payload["policy_name"],
                        rule_id=payload.get("rule_id"),
                        message=payload["message"],
                        severity=payload["severity"],
                        resource_address=payload.get("resource_address"),
                        input_document=payload.get("input_document"),
                        opa_result=payload.get("opa_result"),
                    )
                )
            )
        return records

    def _findings_from_policy_violations(self, violations: list[TerraformPolicyViolation]) -> list[dict[str, Any]]:
        return [
            {
                "rule_id": violation.rule_id,
                "severity": violation.severity,
                "category": "policy",
                "title": "OPA policy violation",
                "description": violation.message,
                "impact": self._impact_for(violation.severity),
                "remediation": "Update Terraform configuration to satisfy OPA policy requirements.",
                "resource_address": violation.resource_address,
                "resource_type": None,
                "file_path": None,
                "line_number": None,
                "scanner": "opa",
                "confidence_score": 0.94,
                "raw_finding": {"policy_name": violation.policy_name},
            }
            for violation in violations
        ]

    async def _explain_findings(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for payload in payloads:
            payload["ai_explanation"] = self._deterministic_explanation(payload)
        if not payloads or (settings.LLM_PROVIDER == "openai" and not self._has_openai_key()):
            return payloads
        try:
            provider = LLMProviderFactory.create()
            prompt = json.dumps(payloads[:8], default=str)
            response = await provider.analyze(
                system_prompt="Explain Terraform security findings as concise JSON keyed by rule_id.",
                user_message=f"Return JSON array with rule_id, explanation, remediation, confidence:\n{prompt}",
            )
            enriched = self._parse_explanations(response.get("content", ""))
            by_rule = {item.get("rule_id"): item for item in enriched}
            for payload in payloads:
                if payload.get("rule_id") in by_rule:
                    item = by_rule[payload["rule_id"]]
                    payload["ai_explanation"] = item.get("explanation") or payload["ai_explanation"]
                    payload["remediation"] = item.get("remediation") or payload.get("remediation")
                    payload["confidence_score"] = item.get("confidence") or payload.get("confidence_score")
        except Exception as exc:
            logger.warning("Terraform AI explanation failed; deterministic explanations retained", error=str(exc))
        return payloads

    async def _persist_findings(
        self,
        workspace: TerraformWorkspace,
        scan: TerraformScan,
        resources: list[TerraformResource],
        payloads: list[dict[str, Any]],
    ) -> list[TerraformFinding]:
        by_address = {resource.address: resource for resource in resources}
        records = []
        seen = set()
        for payload in payloads:
            key = (payload.get("rule_id"), payload.get("resource_address"), payload.get("file_path"), payload.get("line_number"))
            if key in seen:
                continue
            seen.add(key)
            resource = by_address.get(payload.get("resource_address"))
            records.append(
                await self.finding_repo.create(
                    TerraformFinding(
                        id=str(uuid4()),
                        workspace_id=workspace.id,
                        scan_id=scan.id,
                        resource_id=resource.id if resource else None,
                        title=payload["title"],
                        description=payload["description"],
                        impact=payload.get("impact"),
                        severity=payload["severity"],
                        category=payload["category"],
                        scanner=payload.get("scanner", "nexusops"),
                        rule_id=payload.get("rule_id"),
                        resource_address=payload.get("resource_address"),
                        resource_type=payload.get("resource_type") or (resource.type if resource else None),
                        file_path=payload.get("file_path") or (resource.file_path if resource else None),
                        line_number=payload.get("line_number") or (resource.line_number if resource else None),
                        remediation=payload.get("remediation"),
                        ai_explanation=payload.get("ai_explanation"),
                        confidence_score=payload.get("confidence_score"),
                        raw_finding=payload.get("raw_finding"),
                    )
                )
            )
        return records

    def _detect_drift(self, resources: list[TerraformResource]) -> list[dict[str, Any]]:
        drift = []
        important_keys = {
            "replicas",
            "instance_type",
            "publicly_accessible",
            "storage_encrypted",
            "encrypted",
            "acl",
            "cidr_blocks",
            "from_port",
            "to_port",
        }
        for resource in resources:
            desired = resource.desired_config or {}
            actual = resource.actual_state or {}
            if not actual:
                continue
            flat_desired = self._flatten(desired)
            flat_actual = self._flatten(actual)
            for key, desired_value in flat_desired.items():
                if key.split(".")[-1] not in important_keys or key not in flat_actual:
                    continue
                actual_value = flat_actual[key]
                if desired_value != actual_value:
                    drift.append(
                        {
                            "resource_address": resource.address,
                            "resource_type": resource.type,
                            "attribute_path": key,
                            "desired_value": desired_value,
                            "actual_value": actual_value,
                            "drift_type": "changed",
                            "severity": self._drift_severity(key, desired_value, actual_value),
                            "description": f"{resource.address} drifted: `{key}` is {actual_value!r}, desired {desired_value!r}.",
                            "remediation": "Reconcile live infrastructure with Terraform desired state or update Terraform after approval.",
                            "confidence_score": 0.88,
                        }
                    )
            resource.drift_status = "drifted" if any(item["resource_address"] == resource.address for item in drift) else "in_sync"
        return drift

    async def _persist_drift(
        self,
        workspace: TerraformWorkspace,
        scan: TerraformScan,
        resources: list[TerraformResource],
        payloads: list[dict[str, Any]],
    ) -> list[TerraformDrift]:
        by_address = {resource.address: resource for resource in resources}
        records = []
        for payload in payloads:
            resource = by_address.get(payload["resource_address"])
            records.append(
                await self.drift_repo.create(
                    TerraformDrift(
                        id=str(uuid4()),
                        workspace_id=workspace.id,
                        scan_id=scan.id,
                        resource_id=resource.id if resource else None,
                        **payload,
                    )
                )
            )
        return records

    def _finalize_scan(
        self,
        scan: TerraformScan,
        findings: list[TerraformFinding],
        drift: list[TerraformDrift],
        policy_violations: list[TerraformPolicyViolation],
    ) -> None:
        scan.status = "completed"
        scan.findings_count = len(findings)
        scan.critical_count = sum(1 for item in findings if item.severity == "critical")
        scan.high_count = sum(1 for item in findings if item.severity == "high")
        scan.medium_count = sum(1 for item in findings if item.severity == "medium")
        scan.low_count = sum(1 for item in findings if item.severity == "low")
        scan.policy_violation_count = len(policy_violations)
        scan.drift_count = len(drift)
        scan.drift_detected = bool(drift)
        scan.drift_details = {"drift": [item.description for item in drift[:20]]}
        scan.ai_summary = (
            f"Terraform analysis found {len(findings)} security findings, "
            f"{len(policy_violations)} policy violations, and {len(drift)} drift records."
        )

    def _normalize_files(self, files: dict[str, str] | None, terraform_content: str | None) -> dict[str, str]:
        normalized = dict(files or {})
        if terraform_content:
            normalized.setdefault("main.tf", terraform_content)
        return {path: content for path, content in normalized.items() if path.endswith(".tf")}

    def _actual_state_for(self, address: str, state: dict[str, Any] | None) -> dict[str, Any] | None:
        if not state:
            return None
        if address in state and isinstance(state[address], dict):
            return state[address]
        for resource in state.get("resources", []):
            candidate = f"{resource.get('type')}.{resource.get('name')}"
            if candidate == address:
                instances = resource.get("instances") or []
                if instances:
                    return instances[0].get("attributes", {})
        for change in state.get("resource_changes", []):
            if change.get("address") == address:
                return change.get("change", {}).get("after", {})
        return None

    def _has_public_ingress(self, config: dict[str, Any]) -> bool:
        serialized = json.dumps(config)
        return "0.0.0.0/0" in serialized

    def _missing_encryption(self, resource_type: str, config: dict[str, Any]) -> bool:
        if resource_type == "aws_db_instance":
            return config.get("storage_encrypted") is not True
        if resource_type == "aws_ebs_volume":
            return config.get("encrypted") is not True
        if resource_type == "aws_s3_bucket":
            return "server_side_encryption" not in json.dumps(config)
        return False

    def _is_privileged(self, config: dict[str, Any]) -> bool:
        serialized = json.dumps(config).lower()
        return '"privileged": true' in serialized or '"run_as_user": 0' in serialized

    def _has_resource_limits(self, config: dict[str, Any]) -> bool:
        serialized = json.dumps(config).lower()
        return "limits" in serialized and "cpu" in serialized and "memory" in serialized

    def _flatten(self, value: Any, prefix: str = "") -> dict[str, Any]:
        if isinstance(value, dict):
            items = {}
            for key, child in value.items():
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                items.update(self._flatten(child, child_prefix))
            return items
        if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
            return self._flatten(value[0], prefix)
        return {prefix: value}

    def _drift_severity(self, key: str, desired: Any, actual: Any) -> str:
        if key.endswith(("publicly_accessible", "cidr_blocks")):
            return "critical"
        if key.endswith(("storage_encrypted", "encrypted")) and actual is False:
            return "high"
        if key.endswith("replicas") and isinstance(desired, int) and isinstance(actual, int) and abs(actual - desired) >= 2:
            return "high"
        return "medium"

    def _line_number(self, content: str, resource_type: str, name: str) -> int | None:
        pattern = re.compile(rf'resource\s+"{re.escape(resource_type)}"\s+"{re.escape(name)}"')
        match = pattern.search(content)
        return content[: match.start()].count("\n") + 1 if match else None

    def _severity_from_message(self, message: str, default: str) -> str:
        prefix = message.split(":", 1)[0].lower()
        return prefix if prefix in {"critical", "high", "medium", "low", "info"} else default

    def _resource_from_message(self, message: str) -> str | None:
        match = re.search(r"resource ([\w.\-\[\]\"]+)", message)
        return match.group(1) if match else None

    def _impact_for(self, severity: str) -> str:
        impacts = {
            "critical": "Could allow direct compromise, data exposure, or broad privilege escalation.",
            "high": "Material risk to production security or compliance posture.",
            "medium": "Operational or compliance risk that should be remediated in normal sprint flow.",
            "low": "Low-risk hardening opportunity.",
        }
        return impacts.get(severity, "Informational infrastructure security signal.")

    def _deterministic_explanation(self, payload: dict[str, Any]) -> str:
        return (
            f"{payload['title']} affects {payload.get('resource_address') or payload.get('file_path') or 'the Terraform project'}. "
            f"Impact: {payload.get('impact')}. Recommended action: {payload.get('remediation')}"
        )

    def _parse_explanations(self, content: str) -> list[dict[str, Any]]:
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`").removeprefix("json").strip()
        parsed = json.loads(content)
        return parsed if isinstance(parsed, list) else []

    def _has_openai_key(self) -> bool:
        key = settings.OPENAI_API_KEY.strip()
        return bool(key and not key.startswith("sk-your-"))

    def _infer_provider(self, files: dict[str, str]) -> str | None:
        joined = "\n".join(files.values())
        if "aws_" in joined:
            return "aws"
        if "azurerm_" in joined:
            return "azure"
        if "google_" in joined:
            return "gcp"
        if "kubernetes_" in joined:
            return "kubernetes"
        return None


DEMO_TERRAFORM_MAIN = """
resource "aws_security_group_rule" "ssh_world" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}

resource "aws_db_instance" "orders" {
  identifier            = "orders-prod"
  instance_type         = "db.t3.medium"
  publicly_accessible   = true
  storage_encrypted     = false
  skip_final_snapshot   = true
  password              = "super-secret-password"
}

resource "aws_iam_policy" "platform_admin" {
  name   = "platform-admin"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

resource "aws_s3_bucket" "logs" {
  bucket = "nexusops-prod-logs"
  acl    = "public-read"
}
"""


DEMO_TERRAFORM_KUBERNETES = """
resource "kubernetes_deployment" "checkout" {
  metadata {
    name = "checkout-api"
  }

  spec {
    replicas = 3
    template {
      spec {
        container {
          name  = "checkout"
          image = "checkout:latest"
          security_context {
            privileged  = true
            run_as_user = 0
          }
        }
      }
    }
  }
}

resource "kubernetes_cluster_role" "wildcard_operator" {
  metadata {
    name = "wildcard-operator"
  }

  rule {
    api_groups = ["*"]
    resources  = ["*"]
    verbs      = ["*"]
  }
}
"""


DEMO_TERRAFORM_STATE = {
    "aws_db_instance.orders": {
        "identifier": "orders-prod",
        "instance_type": "db.t3.large",
        "publicly_accessible": True,
        "storage_encrypted": False,
        "skip_final_snapshot": True,
    },
    "kubernetes_deployment.checkout": {
        "metadata": [{"name": "checkout-api"}],
        "spec": [{"replicas": 5}],
    },
    "aws_security_group_rule.ssh_world": {
        "type": "ingress",
        "from_port": 22,
        "to_port": 22,
        "protocol": "tcp",
        "cidr_blocks": ["0.0.0.0/0"],
    },
}
