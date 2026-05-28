import { api } from './api'

export interface Incident {
  id: string
  title: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  status: 'open' | 'investigating' | 'resolved' | 'closed'
  source: string
  cluster_id: string
  namespace?: string
  workload?: string
  root_cause?: string
  ai_confidence?: number
  created_at: string
  resolved_at?: string
}

export interface IncidentStats {
  total_open: number
  critical: number
  high: number
  medium: number
  low: number
  resolved_today: number
  avg_resolution_hours: number
}

export const incidentsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<{ items: Incident[]; total: number }>('/incidents', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Incident>(`/incidents/${id}`).then((r) => r.data),

  create: (data: Partial<Incident>) =>
    api.post<Incident>('/incidents', data).then((r) => r.data),

  update: (id: string, data: Partial<Incident>) =>
    api.patch<Incident>(`/incidents/${id}`, data).then((r) => r.data),

  resolve: (id: string) =>
    api.post<Incident>(`/incidents/${id}/resolve`).then((r) => r.data),

  stats: () =>
    api.get<IncidentStats>('/incidents/stats').then((r) => r.data),

  investigate: (id: string, query: string) =>
    api.post(`/incidents/${id}/investigate`, null, { params: { query } }).then((r) => r.data),
}
