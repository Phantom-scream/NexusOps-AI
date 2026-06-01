import { api } from './api'

export interface InvestigationEvidence {
  id: string
  investigation_id: string
  evidence_type: string
  severity: string
  title: string
  description: string
  resource_type?: string | null
  resource_name?: string | null
  cluster_id?: string | null
  namespace_name?: string | null
  deployment_name?: string | null
  pod_name?: string | null
  service_name?: string | null
  source_id?: string | null
  source_type?: string | null
  observed_at?: string | null
  metadata_?: Record<string, unknown>
  created_at: string
}

export interface Recommendation {
  priority?: number
  category?: string
  title: string
  description: string
  command?: string
}

export interface Investigation {
  id: string
  incident_id?: string | null
  cluster_id?: string | null
  title: string
  query: string
  status: string
  summary?: string | null
  root_cause?: string | null
  root_cause_detail?: string | null
  severity: string
  confidence_score?: number | null
  affected_resources?: Array<Record<string, unknown>>
  supporting_evidence?: Array<Record<string, unknown>>
  remediation_recommendations?: Recommendation[]
  investigation_context?: Record<string, unknown>
  context_sources?: string[]
  llm_provider?: string | null
  llm_model?: string | null
  tokens_used?: number | null
  started_at?: string | null
  completed_at?: string | null
  created_at: string
  updated_at: string
}

export interface InvestigationCreate {
  incident_id?: string
  cluster_id?: string
  title?: string
  query: string
  run_immediately?: boolean
}

export const investigationsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<{ items: Investigation[]; total: number }>('/investigations', { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Investigation>(`/investigations/${id}`).then((r) => r.data),

  create: (data: InvestigationCreate) =>
    api.post<Investigation>('/investigations', data).then((r) => r.data),

  run: (id: string) =>
    api.post<{ investigation: Investigation; evidence: InvestigationEvidence[] }>(`/investigations/${id}/run`).then((r) => r.data),

  evidence: (id: string) =>
    api.get<InvestigationEvidence[]>(`/investigations/${id}/evidence`).then((r) => r.data),

  generateDemoIncidents: () =>
    api.post('/demo/incidents/generate').then((r) => r.data),
}
