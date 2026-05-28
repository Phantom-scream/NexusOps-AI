import { api } from './api'

export interface Cluster {
  id: string
  name: string
  display_name: string
  provider: string
  status: string
  region?: string
  kubernetes_version?: string
  node_count: number
  pod_count: number
  namespace_count: number
  created_at: string
  last_sync_at?: string
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
}
