"""
NexusOps AI — Kubernetes API Client
Async wrapper around the kubernetes Python SDK
"""
import os
from typing import Any, Dict, List, Optional

import structlog
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from app.core.config import settings

logger = structlog.get_logger(__name__)


class KubernetesClient:
    """
    Async-compatible Kubernetes API client.
    Supports both in-cluster (pod service account) and kubeconfig authentication.
    
    Used by the cluster sync task to ingest live infrastructure state.
    """

    def __init__(self, kubeconfig_path: Optional[str] = None, context: Optional[str] = None):
        self.kubeconfig_path = kubeconfig_path or settings.KUBECONFIG_PATH
        self.context = context
        self._api_client: Optional[client.ApiClient] = None

    def _initialize(self) -> None:
        """Initialize the Kubernetes API client."""
        if self._api_client:
            return

        if settings.K8S_IN_CLUSTER:
            logger.info("Loading in-cluster Kubernetes config")
            config.load_incluster_config()
        else:
            kubeconfig = os.path.expanduser(self.kubeconfig_path)
            if os.path.exists(kubeconfig):
                logger.info("Loading kubeconfig", path=kubeconfig, context=self.context)
                config.load_kube_config(config_file=kubeconfig, context=self.context)
            else:
                logger.warning("Kubeconfig not found, using default discovery")
                config.load_kube_config()

        self._api_client = client.ApiClient()

    def get_cluster_info(self) -> Dict[str, Any]:
        """Fetch cluster-level information: version, nodes, namespaces."""
        self._initialize()
        result = {
            "node_count": 0,
            "namespace_count": 0,
            "pod_count": 0,
            "kubernetes_version": None,
            "cpu_capacity": 0.0,
            "memory_capacity_gb": 0.0,
            "nodes": [],
            "namespaces": [],
        }

        # Version info
        try:
            version_api = client.VersionApi(self._api_client)
            version_info = version_api.get_code()
            result["kubernetes_version"] = f"{version_info.major}.{version_info.minor}"
        except ApiException as exc:
            logger.warning("Failed to get Kubernetes version", error=str(exc))

        # Nodes
        try:
            core_api = client.CoreV1Api(self._api_client)
            nodes = core_api.list_node()
            result["node_count"] = len(nodes.items)
            result["nodes"] = [self._parse_node(n) for n in nodes.items]

            for node in nodes.items:
                cpu_str = node.status.capacity.get("cpu", "0")
                mem_str = node.status.capacity.get("memory", "0Ki")
                result["cpu_capacity"] += self._parse_cpu(cpu_str)
                result["memory_capacity_gb"] += self._parse_memory_gb(mem_str)

        except ApiException as exc:
            logger.warning("Failed to list nodes", error=str(exc))

        # Namespaces
        try:
            core_api = client.CoreV1Api(self._api_client)
            namespaces = core_api.list_namespace()
            result["namespace_count"] = len(namespaces.items)
            result["namespaces"] = [
                {"name": ns.metadata.name, "status": ns.status.phase}
                for ns in namespaces.items
            ]
        except ApiException as exc:
            logger.warning("Failed to list namespaces", error=str(exc))

        # Pod count
        try:
            core_api = client.CoreV1Api(self._api_client)
            pods = core_api.list_pod_for_all_namespaces()
            result["pod_count"] = len(pods.items)
        except ApiException as exc:
            logger.warning("Failed to count pods", error=str(exc))

        return result

    def get_workloads(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all deployments and statefulsets."""
        self._initialize()
        workloads = []

        apps_api = client.AppsV1Api(self._api_client)

        # Deployments
        try:
            if namespace:
                deployments = apps_api.list_namespaced_deployment(namespace)
            else:
                deployments = apps_api.list_deployment_for_all_namespaces()

            for dep in deployments.items:
                workloads.append(self._parse_deployment(dep))
        except ApiException as exc:
            logger.warning("Failed to list deployments", error=str(exc))

        # StatefulSets
        try:
            if namespace:
                statefulsets = apps_api.list_namespaced_stateful_set(namespace)
            else:
                statefulsets = apps_api.list_stateful_set_for_all_namespaces()

            for ss in statefulsets.items:
                workloads.append(self._parse_statefulset(ss))
        except ApiException as exc:
            logger.warning("Failed to list statefulsets", error=str(exc))

        return workloads

    def get_events(
        self,
        namespace: Optional[str] = None,
        field_selector: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch Kubernetes events — critical for incident correlation."""
        self._initialize()
        core_api = client.CoreV1Api(self._api_client)

        try:
            if namespace:
                events = core_api.list_namespaced_event(
                    namespace,
                    field_selector=field_selector,
                )
            else:
                events = core_api.list_event_for_all_namespaces(
                    field_selector=field_selector,
                )

            return [self._parse_event(e) for e in events.items]

        except ApiException as exc:
            logger.error("Failed to fetch events", error=str(exc))
            return []

    def get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        container: Optional[str] = None,
        tail_lines: int = 100,
    ) -> str:
        """Fetch recent logs from a pod container."""
        self._initialize()
        core_api = client.CoreV1Api(self._api_client)

        try:
            return core_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
                timestamps=True,
            )
        except ApiException as exc:
            logger.warning("Failed to fetch pod logs", pod=pod_name, error=str(exc))
            return ""

    def _parse_node(self, node) -> Dict[str, Any]:
        conditions = {c.type: c.status for c in (node.status.conditions or [])}
        return {
            "name": node.metadata.name,
            "status": "Ready" if conditions.get("Ready") == "True" else "NotReady",
            "role": "control-plane" if "node-role.kubernetes.io/control-plane" in (node.metadata.labels or {}) else "worker",
            "kubernetes_version": node.status.node_info.kubelet_version if node.status.node_info else None,
            "os_image": node.status.node_info.os_image if node.status.node_info else None,
            "container_runtime": node.status.node_info.container_runtime_version if node.status.node_info else None,
            "cpu_allocatable": self._parse_cpu(node.status.allocatable.get("cpu", "0")) if node.status.allocatable else None,
            "memory_allocatable_gb": self._parse_memory_gb(node.status.allocatable.get("memory", "0Ki")) if node.status.allocatable else None,
            "conditions": conditions,
            "labels": node.metadata.labels or {},
        }

    def _parse_deployment(self, dep) -> Dict[str, Any]:
        spec = dep.spec
        containers = spec.template.spec.containers if spec.template.spec.containers else []
        first_container = containers[0] if containers else None

        cpu_req = memory_req = cpu_lim = memory_lim = None
        image = None
        if first_container:
            image = first_container.image
            if first_container.resources and first_container.resources.requests:
                cpu_req = self._parse_cpu_millicores(first_container.resources.requests.get("cpu", "0"))
                memory_req = self._parse_memory_mb(first_container.resources.requests.get("memory", "0Mi"))
            if first_container.resources and first_container.resources.limits:
                cpu_lim = self._parse_cpu_millicores(first_container.resources.limits.get("cpu", "0"))
                memory_lim = self._parse_memory_mb(first_container.resources.limits.get("memory", "0Mi"))

        return {
            "name": dep.metadata.name,
            "namespace_name": dep.metadata.namespace,
            "kind": "Deployment",
            "replicas_desired": spec.replicas or 1,
            "replicas_ready": dep.status.ready_replicas or 0 if dep.status else 0,
            "image": image,
            "cpu_request_millicores": cpu_req,
            "memory_request_mb": memory_req,
            "cpu_limit_millicores": cpu_lim,
            "memory_limit_mb": memory_lim,
            "labels": dep.metadata.labels or {},
            "annotations": dep.metadata.annotations or {},
        }

    def _parse_statefulset(self, ss) -> Dict[str, Any]:
        return {
            "name": ss.metadata.name,
            "namespace_name": ss.metadata.namespace,
            "kind": "StatefulSet",
            "replicas_desired": ss.spec.replicas or 1,
            "replicas_ready": ss.status.ready_replicas or 0 if ss.status else 0,
            "image": ss.spec.template.spec.containers[0].image if ss.spec.template.spec.containers else None,
            "labels": ss.metadata.labels or {},
            "annotations": ss.metadata.annotations or {},
        }

    def _parse_event(self, event) -> Dict[str, Any]:
        return {
            "type": event.type,
            "reason": event.reason,
            "message": event.message,
            "involved_object": f"{event.involved_object.kind}/{event.involved_object.name}" if event.involved_object else "",
            "namespace": event.metadata.namespace,
            "count": event.count or 1,
            "first_time": event.first_timestamp.isoformat() if event.first_timestamp else None,
            "last_time": event.last_timestamp.isoformat() if event.last_timestamp else None,
        }

    def _parse_cpu(self, cpu_str: str) -> float:
        """Parse CPU string (e.g., '4', '500m') to float cores."""
        if cpu_str.endswith("m"):
            return float(cpu_str[:-1]) / 1000
        return float(cpu_str)

    def _parse_cpu_millicores(self, cpu_str: str) -> int:
        """Parse CPU string to millicores."""
        if cpu_str.endswith("m"):
            return int(cpu_str[:-1])
        return int(float(cpu_str) * 1000)

    def _parse_memory_gb(self, mem_str: str) -> float:
        """Parse memory string (Ki, Mi, Gi) to GB."""
        if mem_str.endswith("Ki"):
            return float(mem_str[:-2]) / (1024 * 1024)
        elif mem_str.endswith("Mi"):
            return float(mem_str[:-2]) / 1024
        elif mem_str.endswith("Gi"):
            return float(mem_str[:-2])
        return float(mem_str) / (1024 ** 3)

    def _parse_memory_mb(self, mem_str: str) -> int:
        """Parse memory string to MB."""
        if mem_str.endswith("Ki"):
            return int(float(mem_str[:-2]) / 1024)
        elif mem_str.endswith("Mi"):
            return int(float(mem_str[:-2]))
        elif mem_str.endswith("Gi"):
            return int(float(mem_str[:-2]) * 1024)
        return int(float(mem_str) / (1024 ** 2))
