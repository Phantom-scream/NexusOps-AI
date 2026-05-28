import { api } from './api'

export interface AIInvestigateRequest {
  cluster_id: string
  query: string
  namespace?: string
  workload?: string
  context_window_minutes?: number
}

export interface AIInvestigateResponse {
  severity: string
  root_cause: string
  contributing_factors: string[]
  remediation: Record<string, string>
  confidence: number
  analysis_detail: string
  tokens_used?: number
}

export const aiApi = {
  investigate: (data: AIInvestigateRequest) =>
    api.post<AIInvestigateResponse>('/ai/investigate', data).then((r) => r.data),

  query: (query: string) =>
    api.post<{ answer: string; sources: string[] }>('/ai/query', null, { params: { query } }).then((r) => r.data),
}
