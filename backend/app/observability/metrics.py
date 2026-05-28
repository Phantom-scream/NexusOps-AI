"""
NexusOps AI — Prometheus Metrics Definitions
Custom business metrics for platform observability
"""
from prometheus_client import Counter, Gauge, Histogram

# ----------------------------------------------------------
# Incident Metrics
# ----------------------------------------------------------
incidents_total = Counter(
    "nexusops_incidents_total",
    "Total number of incidents created",
    ["severity", "source", "cluster"],
)

incidents_resolved = Counter(
    "nexusops_incidents_resolved_total",
    "Total incidents resolved",
    ["severity"],
)

active_incidents = Gauge(
    "nexusops_active_incidents",
    "Current number of open incidents",
    ["severity"],
)

# ----------------------------------------------------------
# AI Analysis Metrics
# ----------------------------------------------------------
ai_analysis_duration = Histogram(
    "nexusops_ai_analysis_duration_seconds",
    "Duration of AI incident analysis",
    ["provider", "analysis_type"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

ai_analysis_tokens = Counter(
    "nexusops_ai_tokens_total",
    "Total LLM tokens consumed",
    ["provider", "operation"],
)

ai_analysis_confidence = Histogram(
    "nexusops_ai_confidence_score",
    "AI analysis confidence score distribution",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# ----------------------------------------------------------
# Cluster Metrics
# ----------------------------------------------------------
clusters_registered = Gauge(
    "nexusops_clusters_registered_total",
    "Number of registered clusters",
    ["provider", "environment"],
)

cluster_sync_duration = Histogram(
    "nexusops_cluster_sync_duration_seconds",
    "Time to sync cluster resources from Kubernetes API",
    ["cluster_name"],
)

cluster_pod_count = Gauge(
    "nexusops_cluster_pods",
    "Pod count per cluster",
    ["cluster_name", "namespace"],
)

# ----------------------------------------------------------
# Security Metrics
# ----------------------------------------------------------
security_findings_total = Counter(
    "nexusops_security_findings_total",
    "Total security findings detected",
    ["severity", "category", "scanner"],
)

# ----------------------------------------------------------
# Cost Metrics
# ----------------------------------------------------------
cost_optimization_savings = Gauge(
    "nexusops_cost_optimization_savings_usd",
    "Estimated monthly savings from optimization recommendations",
    ["cluster_name"],
)
