"""
NexusOps AI — Terraform Security Analysis Engine
AI-powered analysis of Terraform configurations for security risks and drift
"""
import json
import re
from typing import Any, Dict, List, Optional

import structlog

from app.ai.llm_client import llm_client
from app.ai.prompts.templates import (
    TERRAFORM_SECURITY_SYSTEM_PROMPT,
    TERRAFORM_SECURITY_USER_TEMPLATE,
)

logger = structlog.get_logger(__name__)


class TerraformAnalyzer:
    """
    Analyzes Terraform HCL configurations for:
    - Security misconfigurations (IAM, network, encryption)
    - RBAC risks in Kubernetes manifests
    - Secrets exposure
    - Compliance gaps
    - Infrastructure drift patterns
    """

    async def analyze(
        self,
        terraform_content: str,
        scan_name: str,
        repo_url: Optional[str] = None,
        opa_violations: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Run AI security analysis on Terraform configuration.
        Returns structured findings with severity, category, and remediation.
        """
        logger.info("Starting Terraform security analysis", scan_name=scan_name)

        # Pre-scan for common patterns (fast heuristic checks)
        heuristic_findings = self._heuristic_scan(terraform_content)

        opa_text = self._format_opa_violations(opa_violations or [])

        user_message = TERRAFORM_SECURITY_USER_TEMPLATE.format(
            scan_name=scan_name,
            repo_url=repo_url or "local upload",
            terraform_content=terraform_content[:8000],  # Token limit
            opa_violations=opa_text,
        )

        response = await llm_client.chat(
            system_prompt=TERRAFORM_SECURITY_SYSTEM_PROMPT,
            user_message=user_message,
        )

        result = self._parse_llm_response(response["content"])

        # Merge heuristic findings with LLM findings
        all_findings = result.get("findings", []) + heuristic_findings
        result["findings"] = all_findings
        result["tokens_used"] = response.get("tokens_used")

        logger.info(
            "Terraform analysis complete",
            scan_name=scan_name,
            total_findings=len(all_findings),
        )

        return result

    def _heuristic_scan(self, content: str) -> List[Dict]:
        """
        Fast regex-based heuristic scan for obvious security issues.
        These run before the AI analysis and are always reported.
        """
        findings = []

        patterns = [
            {
                "pattern": r'cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\]',
                "severity": "high",
                "category": "network",
                "rule_id": "NEXOPS-TF-001",
                "title": "Security group allows unrestricted inbound access (0.0.0.0/0)",
                "description": "Opening all inbound traffic exposes resources to the internet.",
                "remediation": "Restrict cidr_blocks to specific IP ranges required by the application.",
            },
            {
                "pattern": r'(password|secret|api_key|access_key)\s*=\s*"[^"]{4,}"',
                "severity": "critical",
                "category": "secrets",
                "rule_id": "NEXOPS-TF-002",
                "title": "Hardcoded credential or secret detected in Terraform configuration",
                "description": "Secrets embedded in Terraform code are exposed in version control and state files.",
                "remediation": "Use AWS Secrets Manager, HashiCorp Vault, or environment variables via var.* references.",
            },
            {
                "pattern": r'encrypted\s*=\s*false',
                "severity": "high",
                "category": "encryption",
                "rule_id": "NEXOPS-TF-003",
                "title": "Storage resource explicitly disables encryption",
                "description": "Unencrypted storage violates data protection requirements.",
                "remediation": "Set encrypted = true and specify a KMS key.",
            },
            {
                "pattern": r'publicly_accessible\s*=\s*true',
                "severity": "critical",
                "category": "network",
                "rule_id": "NEXOPS-TF-004",
                "title": "Database or storage resource is publicly accessible",
                "description": "Publicly accessible databases are directly exposed to internet threats.",
                "remediation": "Set publicly_accessible = false and use VPC-only access.",
            },
            {
                "pattern": r'skip_final_snapshot\s*=\s*true',
                "severity": "medium",
                "category": "compliance",
                "rule_id": "NEXOPS-TF-005",
                "title": "RDS instance configured to skip final snapshot on deletion",
                "description": "Data loss risk if database is accidentally deleted without a final backup.",
                "remediation": "Set skip_final_snapshot = false and define final_snapshot_identifier.",
            },
        ]

        for check in patterns:
            if re.search(check["pattern"], content, re.IGNORECASE):
                findings.append({
                    "severity": check["severity"],
                    "category": check["category"],
                    "rule_id": check["rule_id"],
                    "title": check["title"],
                    "description": check["description"],
                    "resource": "detected via pattern matching",
                    "remediation": check["remediation"],
                    "source": "heuristic",
                })

        return findings

    def _format_opa_violations(self, violations: List[Dict]) -> str:
        if not violations:
            return "No OPA policy violations reported."
        return "\n".join([
            f"- {v.get('policy')}: {v.get('message', '')}"
            for v in violations
        ])

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r"```(?:json)?\n(.*?)\n```", content, re.DOTALL)
            if json_match:
                content = json_match.group(1)

            return json.loads(content)

        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse Terraform analysis JSON response")
            return {
                "findings": [],
                "risk_summary": content[:1000],
                "compliance_gaps": [],
                "overall_risk_score": 5.0,
            }
