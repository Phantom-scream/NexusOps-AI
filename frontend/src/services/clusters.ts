import { api } from './api'

export interface Cluster {
  id: string
  name: string
  display_name: string
  provider: string
  status: string
  region?: string
  environment: string
  kubernetes_version?: string
  node_count: number
  pod_count: number
  namespace_count: number
  service_count: number
  deployment_count: number
  cpu_capacity?: number
  memory_capacity_gb?: number
  created_at: string
  last_sync_at?: string
  tags?: Record<string, string>
}

export interface ClusterSummary {
  id: string
  name: string
  status: string
  node_count: number
  pod_count: number
  namespace_count: number
  health_score: number
  recent_incidents: number
}

export interface ClusterNode {
  id: string
  name: string
  status: string
  role: string
  kubernetes_version?: string
  os_image?: string
  cpu_allocatable?: number
  memory_allocatable_gb?: number
  cpu_usage_percent?: number
  memory_usage_percent?: number
}

export interface Namespace {
  id: string
  cluster_id: string
  name: string
  status: string
  labels?: Record<string, string>
}

export interface Deployment {
  id: string
  cluster_id: string
  namespace_name: string
  name: string
  kind: string
  replicas_desired: number
  replicas_ready: number
  image?: string
  cpu_usage_percent?: number
  memory_usage_percent?: number
  is_healthy: boolean
  labels?: Record<string, string>
}

export interface Pod {
  id: string
  cluster_id: string
  namespace_name: string
  name: string
  phase: string
  status: string
  node_name?: string
  pod_ip?: string
  restart_count: number
  ready: boolean
  owner_kind?: string
  owner_name?: string
}

export interface KubernetesService {
  id: string
  cluster_id: string
  namespace_name: string
  name: string
  service_type: string
  cluster_ip?: string
  external_ip?: string
  ports?: Array<Record<string, unknown>>
  selector?: Record<string, string>
}

export interface TopologyNode {
  id: string
  name: string
  type: string
  status?: string
  metadata: Record<string, unknown>
  children: TopologyNode[]
}

export interface ClusterTopology {
  cluster_id: string
  generated_at: string
  root: TopologyNode
}

export const clustersApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<{ items: Cluster[]; total: number }>('/clusters', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Cluster>(`/clusters/${id}`).then((r) => r.data),

  create: (data: Partial<Cluster>) =>
    api.post<Cluster>('/clusters', data).then((r) => r.data),

  update: (id: string, data: Partial<Cluster>) =>
    api.patch<Cluster>(`/clusters/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/clusters/${id}`),

  sync: (id: string) =>
    api.post<{ task_id: string }>(`/clusters/${id}/sync`).then((r) => r.data),

  summary: (id: string) =>
    api.get<ClusterSummary>(`/clusters/${id}/summary`).then((r) => r.data),

  nodes: (id: string) =>
    api.get<ClusterNode[]>(`/clusters/${id}/nodes`).then((r) => r.data),

  namespaces: (id: string) =>
    api.get<Namespace[]>(`/clusters/${id}/namespaces`).then((r) => r.data),

  deployments: (id: string) =>
    api.get<Deployment[]>(`/clusters/${id}/deployments`).then((r) => r.data),

  pods: (id: string) =>
    api.get<Pod[]>(`/clusters/${id}/pods`).then((r) => r.data),

  services: (id: string) =>
    api.get<KubernetesService[]>(`/clusters/${id}/services`).then((r) => r.data),

  topology: (id: string) =>
    api.get<ClusterTopology>(`/clusters/${id}/topology`).then((r) => r.data),
}

export const demoApi = {
  generate: () =>
    api.post<Cluster[]>('/demo/generate').then((r) => r.data),
}
