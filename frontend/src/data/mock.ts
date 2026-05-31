// ─────────────────────────────────────────────
// NexusOps AI — Realistic Mock Data
// ─────────────────────────────────────────────
import type {
  Cluster,
  Incident,
  SecurityFinding,
  CostRecommendation,
  ServiceHealth,
  MetricPoint,
} from '@/types'

// ── Helpers ──────────────────────────────────
const daysAgo = (n: number) => new Date(Date.now() - n * 86400000).toISOString()
const hoursAgo = (n: number) => new Date(Date.now() - n * 3600000).toISOString()
const minsAgo = (n: number) => new Date(Date.now() - n * 60000).toISOString()

function sparkline(base: number, variance: number, len = 24): number[] {
  let v = base
  return Array.from({ length: len }, () => {
    v = Math.max(0, Math.min(100, v + (Math.random() - 0.5) * variance))
    return Math.round(v)
  })
}

// ── Clusters ─────────────────────────────────
export const mockClusters: Cluster[] = [
  {
    id: 'cls-prod-us-east',
    name: 'prod-us-east-1',
    status: 'healthy',
    provider: 'aws',
    region: 'us-east-1',
    nodeCount: 24,
    healthyNodes: 24,
    k8sVersion: '1.29.3',
    cpuUsage: 67,
    memoryUsage: 72,
    podCount: 312,
    totalPods: 400,
    namespaceCount: 18,
    createdAt: daysAgo(185),
    lastSync: minsAgo(2),
    tags: ['production', 'tier-1', 'us'],
    metrics: { cpu: sparkline(67, 8), memory: sparkline(72, 5), pods: sparkline(78, 6) },
  },
  {
    id: 'cls-prod-eu-west',
    name: 'prod-eu-west-1',
    status: 'healthy',
    provider: 'aws',
    region: 'eu-west-1',
    nodeCount: 18,
    healthyNodes: 18,
    k8sVersion: '1.29.3',
    cpuUsage: 54,
    memoryUsage: 61,
    podCount: 228,
    totalPods: 300,
    namespaceCount: 14,
    createdAt: daysAgo(142),
    lastSync: minsAgo(1),
    tags: ['production', 'tier-1', 'eu'],
    metrics: { cpu: sparkline(54, 7), memory: sparkline(61, 5), pods: sparkline(76, 4) },
  },
  {
    id: 'cls-prod-ap',
    name: 'prod-ap-southeast-1',
    status: 'degraded',
    provider: 'gcp',
    region: 'asia-southeast1',
    nodeCount: 12,
    healthyNodes: 10,
    k8sVersion: '1.28.7',
    cpuUsage: 88,
    memoryUsage: 91,
    podCount: 156,
    totalPods: 180,
    namespaceCount: 9,
    createdAt: daysAgo(98),
    lastSync: minsAgo(3),
    tags: ['production', 'tier-1', 'apac'],
    metrics: { cpu: sparkline(88, 6), memory: sparkline(91, 4), pods: sparkline(87, 3) },
  },
  {
    id: 'cls-staging',
    name: 'staging-central',
    status: 'healthy',
    provider: 'azure',
    region: 'eastus',
    nodeCount: 8,
    healthyNodes: 8,
    k8sVersion: '1.29.1',
    cpuUsage: 38,
    memoryUsage: 45,
    podCount: 87,
    totalPods: 150,
    namespaceCount: 11,
    createdAt: daysAgo(211),
    lastSync: minsAgo(4),
    tags: ['staging', 'tier-2'],
    metrics: { cpu: sparkline(38, 12), memory: sparkline(45, 10), pods: sparkline(58, 8) },
  },
  {
    id: 'cls-dev-us',
    name: 'dev-us-west-2',
    status: 'healthy',
    provider: 'aws',
    region: 'us-west-2',
    nodeCount: 5,
    healthyNodes: 5,
    k8sVersion: '1.29.3',
    cpuUsage: 22,
    memoryUsage: 31,
    podCount: 44,
    totalPods: 100,
    namespaceCount: 7,
    createdAt: daysAgo(67),
    lastSync: minsAgo(5),
    tags: ['development', 'tier-3'],
    metrics: { cpu: sparkline(22, 15), memory: sparkline(31, 12), pods: sparkline(44, 10) },
  },
  {
    id: 'cls-edge-cdn',
    name: 'edge-cdn-global',
    status: 'healthy',
    provider: 'hybrid',
    region: 'multi-region',
    nodeCount: 32,
    healthyNodes: 31,
    k8sVersion: '1.28.9',
    cpuUsage: 43,
    memoryUsage: 38,
    podCount: 189,
    totalPods: 250,
    namespaceCount: 5,
    createdAt: daysAgo(300),
    lastSync: minsAgo(1),
    tags: ['production', 'cdn', 'edge'],
    metrics: { cpu: sparkline(43, 9), memory: sparkline(38, 7), pods: sparkline(76, 5) },
  },
  {
    id: 'cls-ml-training',
    name: 'ml-training-gpu',
    status: 'maintenance',
    provider: 'gcp',
    region: 'us-central1',
    nodeCount: 6,
    healthyNodes: 4,
    k8sVersion: '1.28.7',
    cpuUsage: 95,
    memoryUsage: 87,
    podCount: 18,
    totalPods: 30,
    namespaceCount: 3,
    createdAt: daysAgo(45),
    lastSync: minsAgo(8),
    tags: ['ml', 'gpu', 'batch'],
    metrics: { cpu: sparkline(95, 4), memory: sparkline(87, 6), pods: sparkline(60, 5) },
  },
  {
    id: 'cls-dr-backup',
    name: 'dr-backup-us',
    status: 'healthy',
    provider: 'azure',
    region: 'westus2',
    nodeCount: 6,
    healthyNodes: 6,
    k8sVersion: '1.29.1',
    cpuUsage: 15,
    memoryUsage: 22,
    podCount: 24,
    totalPods: 80,
    namespaceCount: 6,
    createdAt: daysAgo(155),
    lastSync: minsAgo(10),
    tags: ['dr', 'backup', 'cold-standby'],
    metrics: { cpu: sparkline(15, 8), memory: sparkline(22, 6), pods: sparkline(30, 5) },
  },
]

// ── Incidents ────────────────────────────────
export const mockIncidents: Incident[] = [
  {
    id: 'inc-001',
    title: 'High CPU utilization on APAC production nodes',
    description: 'CPU usage exceeding 88% on 8 of 12 nodes in prod-ap-southeast-1 cluster, causing pod scheduling failures.',
    severity: 'critical',
    status: 'investigating',
    affectedService: 'core-api',
    affectedCluster: 'prod-ap-southeast-1',
    assignee: 'Sarah Chen',
    createdAt: minsAgo(45),
    updatedAt: minsAgo(12),
    detectedBy: 'ai',
    tags: ['cpu', 'performance', 'production'],
    errorRate: 12.4,
    latencyP99: 4200,
  },
  {
    id: 'inc-002',
    title: 'Database connection pool exhaustion',
    description: 'PostgreSQL connection pool reaching maximum capacity in US-East-1. Queries queuing with 1800ms average wait.',
    severity: 'high',
    status: 'acknowledged',
    affectedService: 'user-service',
    affectedCluster: 'prod-us-east-1',
    assignee: 'Marcus Webb',
    createdAt: hoursAgo(2),
    updatedAt: minsAgo(30),
    detectedBy: 'alert',
    tags: ['database', 'postgres', 'connections'],
    errorRate: 3.8,
    latencyP99: 1800,
  },
  {
    id: 'inc-003',
    title: 'Elevated 5xx error rate on payment service',
    description: 'Payment service returning 5xx errors at 2.3% rate for the past 25 minutes. Potential impact on revenue.',
    severity: 'high',
    status: 'open',
    affectedService: 'payment-service',
    affectedCluster: 'prod-us-east-1',
    createdAt: minsAgo(25),
    updatedAt: minsAgo(25),
    detectedBy: 'alert',
    tags: ['payments', 'revenue', '5xx'],
    errorRate: 2.3,
    latencyP99: 890,
  },
  {
    id: 'inc-004',
    title: 'ML training job OOM crashes',
    description: 'GPU training jobs exceeding memory limits and crashing. Training pipeline blocked.',
    severity: 'medium',
    status: 'open',
    affectedService: 'ml-trainer',
    affectedCluster: 'ml-training-gpu',
    createdAt: hoursAgo(4),
    updatedAt: hoursAgo(1),
    detectedBy: 'ai',
    tags: ['ml', 'oom', 'gpu'],
    errorRate: 45.0,
    latencyP99: 0,
  },
  {
    id: 'inc-005',
    title: 'Redis cache hit rate degradation',
    description: 'Cache hit rate dropped from 94% to 67% following deploy of content-service v3.2.1.',
    severity: 'medium',
    status: 'open',
    affectedService: 'content-service',
    affectedCluster: 'prod-eu-west-1',
    createdAt: hoursAgo(6),
    updatedAt: hoursAgo(2),
    detectedBy: 'ai',
    tags: ['cache', 'redis', 'performance'],
    errorRate: 0.4,
    latencyP99: 340,
  },
  {
    id: 'inc-006',
    title: 'Certificate expiry warning — auth.nexusops.ai',
    description: 'TLS certificate for auth.nexusops.ai expires in 7 days. Automatic renewal failed 3 times.',
    severity: 'medium',
    status: 'acknowledged',
    affectedService: 'auth-service',
    affectedCluster: 'prod-us-east-1',
    assignee: 'System',
    createdAt: daysAgo(2),
    updatedAt: hoursAgo(12),
    detectedBy: 'integration',
    tags: ['tls', 'cert', 'security'],
  },
  {
    id: 'inc-007',
    title: 'Staging deployment rollback triggered',
    description: 'Canary analysis failed for v4.1.0 — error budget exceeded. Rollback to v4.0.9 completed.',
    severity: 'low',
    status: 'resolved',
    affectedService: 'api-gateway',
    affectedCluster: 'staging-central',
    assignee: 'CI/CD System',
    createdAt: daysAgo(1),
    updatedAt: hoursAgo(20),
    resolvedAt: hoursAgo(20),
    detectedBy: 'integration',
    tags: ['deployment', 'rollback', 'canary'],
    errorRate: 8.1,
  },
  {
    id: 'inc-008',
    title: 'Network packet loss detected on edge nodes',
    description: '3-5% packet loss on edge-cdn-global cluster nodes in EMEA PoP. BGP route flapping suspected.',
    severity: 'high',
    status: 'investigating',
    affectedService: 'cdn-edge',
    affectedCluster: 'edge-cdn-global',
    assignee: 'Network Team',
    createdAt: hoursAgo(1),
    updatedAt: minsAgo(15),
    detectedBy: 'alert',
    tags: ['network', 'bgp', 'edge', 'packet-loss'],
    errorRate: 3.8,
    latencyP99: 2100,
  },
]

// ── Security Findings ────────────────────────
export const mockFindings: SecurityFinding[] = [
  {
    id: 'sec-001',
    title: 'Critical: Privilege escalation vulnerability in containerd',
    description: 'CVE-2024-21626 allows container escape via runc process.cwd. All affected nodes must be patched.',
    severity: 'critical',
    status: 'in_progress',
    category: 'vulnerability',
    resource: 'containerd/runc',
    cluster: 'prod-us-east-1',
    cveId: 'CVE-2024-21626',
    cvssScore: 9.8,
    createdAt: daysAgo(5),
    remediationAvailable: true,
  },
  {
    id: 'sec-002',
    title: 'Secret exposed in Kubernetes ConfigMap',
    description: 'AWS API key found in plaintext within namespace "payments" ConfigMap. Immediate rotation required.',
    severity: 'critical',
    status: 'open',
    category: 'secret',
    resource: 'configmap/payments-config',
    cluster: 'prod-us-east-1',
    createdAt: daysAgo(1),
    remediationAvailable: true,
  },
  {
    id: 'sec-003',
    title: 'Container running as root',
    description: 'payment-service containers running with UID 0. Violates security policy and increases blast radius.',
    severity: 'high',
    status: 'open',
    category: 'misconfig',
    resource: 'deployment/payment-service',
    cluster: 'prod-eu-west-1',
    createdAt: daysAgo(8),
    remediationAvailable: true,
  },
  {
    id: 'sec-004',
    title: 'Network policy missing on namespace "analytics"',
    description: 'Namespace has no NetworkPolicy. All pods accept unrestricted ingress/egress traffic.',
    severity: 'high',
    status: 'open',
    category: 'network',
    resource: 'namespace/analytics',
    cluster: 'prod-us-east-1',
    createdAt: daysAgo(12),
    remediationAvailable: true,
  },
  {
    id: 'sec-005',
    title: 'RBAC: Wildcard permissions on ClusterRole',
    description: '"ops-role" ClusterRole has wildcard verb/resource permissions. Violates least privilege.',
    severity: 'high',
    status: 'open',
    category: 'policy',
    resource: 'clusterrole/ops-role',
    cluster: 'staging-central',
    createdAt: daysAgo(15),
    remediationAvailable: true,
  },
  {
    id: 'sec-006',
    title: 'Deprecated Kubernetes API version in use',
    description: 'Ingress objects using networking.k8s.io/v1beta1 (removed in k8s 1.22). Upgrade required.',
    severity: 'medium',
    status: 'in_progress',
    category: 'misconfig',
    resource: 'ingress/api-ingress',
    cluster: 'prod-ap-southeast-1',
    createdAt: daysAgo(20),
    remediationAvailable: true,
  },
  {
    id: 'sec-007',
    title: 'Image pull from public registry without digest pinning',
    description: '12 deployments pulling images from Docker Hub without digest pins. Supply chain risk.',
    severity: 'medium',
    status: 'open',
    category: 'policy',
    resource: 'multiple deployments',
    cluster: 'prod-us-east-1',
    createdAt: daysAgo(3),
    remediationAvailable: true,
  },
  {
    id: 'sec-008',
    title: 'Istio mTLS disabled on service mesh',
    description: 'PERMISSIVE mode allows plaintext traffic. Enable STRICT mode to enforce mTLS between services.',
    severity: 'medium',
    status: 'open',
    category: 'network',
    resource: 'peerauthentication/default',
    cluster: 'prod-eu-west-1',
    createdAt: daysAgo(7),
    remediationAvailable: true,
  },
]

// ── Cost Recommendations ──────────────────────
export const mockCostRecs: CostRecommendation[] = [
  {
    id: 'cost-001',
    title: 'Right-size oversized ML training nodes',
    description: 'GPU nodes average 12% utilization over 30 days. Downgrade from p3.8xlarge to p3.2xlarge.',
    category: 'rightsizing',
    impact: 'high',
    monthlySavings: 4820,
    effort: 'low',
    cluster: 'ml-training-gpu',
    resource: 'nodegroup/gpu-workers',
    status: 'pending',
    currentCost: 7200,
    optimizedCost: 2380,
  },
  {
    id: 'cost-002',
    title: 'Convert on-demand EC2 to Reserved Instances',
    description: '18 production nodes have stable baseline usage. 1-year RIs save 40% vs on-demand.',
    category: 'reserved',
    impact: 'high',
    monthlySavings: 3240,
    effort: 'medium',
    cluster: 'prod-us-east-1',
    resource: 'nodegroup/workers',
    status: 'implementing',
    currentCost: 8100,
    optimizedCost: 4860,
  },
  {
    id: 'cost-003',
    title: 'Remove idle staging namespaces',
    description: '4 staging namespaces have had zero traffic for 14+ days. Safe to deprovision.',
    category: 'idle',
    impact: 'medium',
    monthlySavings: 890,
    effort: 'low',
    cluster: 'staging-central',
    resource: 'namespace/test-*',
    status: 'pending',
    currentCost: 890,
    optimizedCost: 0,
  },
  {
    id: 'cost-004',
    title: 'Delete orphaned EBS volumes',
    description: '23 detached EBS volumes not bound to any PVC. All are older than 30 days.',
    category: 'storage',
    impact: 'medium',
    monthlySavings: 456,
    effort: 'low',
    cluster: 'prod-us-east-1',
    resource: 'pvc/orphaned-*',
    status: 'pending',
    currentCost: 456,
    optimizedCost: 0,
  },
  {
    id: 'cost-005',
    title: 'Enable VPC endpoint for S3 traffic',
    description: '1.8 TB/month S3 traffic routing through NAT gateway. VPC endpoints eliminate data transfer fees.',
    category: 'network',
    impact: 'medium',
    monthlySavings: 324,
    effort: 'low',
    cluster: 'prod-us-east-1',
    resource: 'vpc/prod-vpc',
    status: 'pending',
    currentCost: 324,
    optimizedCost: 0,
  },
  {
    id: 'cost-006',
    title: 'Scale down DR cluster to cold standby',
    description: 'DR cluster running hot standby 24/7. Switch to cold standby with 15-min RTO.',
    category: 'rightsizing',
    impact: 'high',
    monthlySavings: 2100,
    effort: 'medium',
    cluster: 'dr-backup-us',
    resource: 'nodegroup/dr-nodes',
    status: 'pending',
    currentCost: 2800,
    optimizedCost: 700,
  },
]

// ── Service Health ────────────────────────────
export const mockServiceHealth: ServiceHealth[] = [
  { name: 'API Gateway',     type: 'gateway',  status: 'healthy',  uptime: 99.97, responseTime: 42,   errorRate: 0.03, requestsPerSec: 12400 },
  { name: 'Auth Service',    type: 'api',      status: 'healthy',  uptime: 99.99, responseTime: 38,   errorRate: 0.01, requestsPerSec: 4820  },
  { name: 'User Service',    type: 'api',      status: 'degraded', uptime: 99.81, responseTime: 280,  errorRate: 1.20, requestsPerSec: 3180  },
  { name: 'Payment Service', type: 'api',      status: 'degraded', uptime: 99.72, responseTime: 890,  errorRate: 2.30, requestsPerSec: 620   },
  { name: 'Content Service', type: 'api',      status: 'healthy',  uptime: 99.95, responseTime: 65,   errorRate: 0.08, requestsPerSec: 8920  },
  { name: 'PostgreSQL',      type: 'database', status: 'degraded', uptime: 99.89, responseTime: 1800, errorRate: 0.40, requestsPerSec: 2840  },
  { name: 'Redis Cache',     type: 'cache',    status: 'healthy',  uptime: 99.99, responseTime: 2,    errorRate: 0.00, requestsPerSec: 45200 },
  { name: 'Kafka',           type: 'queue',    status: 'healthy',  uptime: 99.94, responseTime: 12,   errorRate: 0.02, requestsPerSec: 18600 },
  { name: 'ML Pipeline',     type: 'worker',   status: 'down',     uptime: 94.20, responseTime: 0,    errorRate: 100,  requestsPerSec: 0     },
  { name: 'CDN Edge',        type: 'gateway',  status: 'degraded', uptime: 99.88, responseTime: 28,   errorRate: 3.80, requestsPerSec: 98400 },
]

// ── Metrics time series ───────────────────────
export function generateMetricSeries(
  base: number,
  variance: number,
  hours = 24,
  key = 'value',
): MetricPoint[] {
  let v = base
  return Array.from({ length: hours }, (_, i) => {
    v = Math.max(0, Math.min(100, v + (Math.random() - 0.5) * variance))
    const h = (new Date().getHours() - hours + i + 24) % 24
    return { time: `${h.toString().padStart(2, '0')}:00`, [key]: Math.round(v) }
  })
}

export function generateMultiSeries(hours = 24): MetricPoint[] {
  let cpu = 58, mem = 65, req = 70
  return Array.from({ length: hours }, (_, i) => {
    cpu = Math.max(0, Math.min(100, cpu + (Math.random() - 0.48) * 8))
    mem = Math.max(0, Math.min(100, mem + (Math.random() - 0.49) * 5))
    req = Math.max(0, Math.min(100, req + (Math.random() - 0.5) * 12))
    const h = (new Date().getHours() - hours + i + 24) % 24
    return {
      time: `${h.toString().padStart(2, '0')}:00`,
      cpu: Math.round(cpu),
      memory: Math.round(mem),
      requests: Math.round(req),
    }
  })
}

export function generateIncidentTrend(hours = 24): MetricPoint[] {
  let incidents = 3, alerts = 8
  return Array.from({ length: hours }, (_, i) => {
    incidents = Math.max(0, Math.min(20, incidents + Math.round((Math.random() - 0.5) * 2)))
    alerts = Math.max(0, Math.min(40, alerts + Math.round((Math.random() - 0.5) * 4)))
    const h = (new Date().getHours() - hours + i + 24) % 24
    return { time: `${h.toString().padStart(2, '0')}:00`, incidents, alerts }
  })
}

export function generateCostTrend(months = 6): MetricPoint[] {
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const now = new Date()
  return Array.from({ length: months }, (_, i) => {
    const month = new Date(now.getFullYear(), now.getMonth() - months + i + 1, 1)
    return {
      time: monthNames[month.getMonth()],
      actual: Math.round(28000 + Math.random() * 8000),
      optimized: Math.round(18000 + Math.random() * 4000),
    }
  })
}

// ── Summary stats ─────────────────────────────
export const mockSummary = {
  totalClusters: mockClusters.length,
  healthyClusters: mockClusters.filter(c => c.status === 'healthy').length,
  totalNodes: mockClusters.reduce((s, c) => s + c.nodeCount, 0),
  openIncidents: mockIncidents.filter(i => i.status !== 'resolved').length,
  criticalIncidents: mockIncidents.filter(i => i.severity === 'critical' && i.status !== 'resolved').length,
  securityFindings: mockFindings.filter(f => f.status === 'open' || f.status === 'in_progress').length,
  criticalFindings: mockFindings.filter(f => f.severity === 'critical').length,
  totalSavings: mockCostRecs.filter(r => r.status !== 'dismissed').reduce((s, r) => s + r.monthlySavings, 0),
  healthyServices: mockServiceHealth.filter(s => s.status === 'healthy').length,
  totalServices: mockServiceHealth.length,
}
