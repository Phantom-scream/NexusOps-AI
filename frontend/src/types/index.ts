// ─────────────────────────────────────────────
// NexusOps AI — Core Type Definitions
// ─────────────────────────────────────────────

// ── Shared ──────────────────────────────────
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type HealthStatus = 'healthy' | 'degraded' | 'critical' | 'unknown' | 'maintenance'
export type CloudProvider = 'aws' | 'gcp' | 'azure' | 'on-premise' | 'hybrid'

// ── Clusters ────────────────────────────────
export interface ClusterNode {
  name: string
  role: 'control-plane' | 'worker'
  status: 'ready' | 'notready' | 'unknown'
  cpu: number
  memory: number
  age: string
}

export interface Cluster {
  id: string
  name: string
  status: HealthStatus
  provider: CloudProvider
  region: string
  nodeCount: number
  healthyNodes: number
  k8sVersion: string
  cpuUsage: number
  memoryUsage: number
  podCount: number
  totalPods: number
  namespaceCount: number
  createdAt: string
  lastSync: string
  tags: string[]
  metrics: {
    cpu: number[]
    memory: number[]
    pods: number[]
  }
}

// ── Incidents ───────────────────────────────
export type IncidentStatus = 'open' | 'acknowledged' | 'investigating' | 'in_progress' | 'resolved'

export interface Incident {
  id: string
  title: string
  description: string
  severity: Severity
  status: IncidentStatus
  affectedService: string
  affectedCluster: string
  namespace?: string
  assignee?: string
  createdAt: string
  updatedAt: string
  resolvedAt?: string
  detectedBy: 'ai' | 'alert' | 'user' | 'integration'
  tags: string[]
  errorRate?: number
  latencyP99?: number
  rootCause?: string
  resolution?: string
}

// ── Security ────────────────────────────────
export type FindingStatus = 'open' | 'in_progress' | 'resolved' | 'suppressed'
export type FindingCategory = 'vulnerability' | 'misconfig' | 'policy' | 'secret' | 'network'

export interface SecurityFinding {
  id: string
  title: string
  description: string
  severity: Severity
  status: FindingStatus
  category: FindingCategory
  resource: string
  cluster: string
  cveId?: string
  cvssScore?: number
  createdAt: string
  remediationAvailable: boolean
}

// ── Cost ────────────────────────────────────
export type CostCategory = 'rightsizing' | 'reserved' | 'idle' | 'storage' | 'network'
export type RecommendationStatus = 'pending' | 'implementing' | 'implemented' | 'dismissed'

export interface CostRecommendation {
  id: string
  title: string
  description: string
  category: CostCategory
  impact: 'high' | 'medium' | 'low'
  monthlySavings: number
  effort: 'low' | 'medium' | 'high'
  cluster: string
  resource: string
  status: RecommendationStatus
  currentCost: number
  optimizedCost: number
}

// ── Observability ───────────────────────────
export interface ServiceHealth {
  name: string
  type: 'api' | 'database' | 'cache' | 'queue' | 'gateway' | 'worker'
  status: 'healthy' | 'degraded' | 'down'
  uptime: number
  responseTime: number
  errorRate: number
  requestsPerSec: number
}

export interface MetricPoint {
  time: string
  value?: number
  [key: string]: string | number | undefined
}

// ── AI Investigation ────────────────────────
export interface AIMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: string[]
  confidence?: number
}
