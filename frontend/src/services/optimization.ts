import { api } from './api'

export interface ResourceUtilization {
  id: string
  cluster_id?: string | null
  cluster_name?: string | null
  namespace?: string | null
  resource_type: string
  resource_name: string
  workload_kind?: string | null
  cpu_request_millicores?: number | null
  memory_request_mb?: number | null
  cpu_usage_avg_percent?: number | null
  memory_usage_avg_percent?: number | null
  cpu_usage_p95_percent?: number | null
  memory_usage_p95_percent?: number | null
  request_count_avg?: number | null
  restart_count: number
  replicas_desired?: number | null
  monthly_cost_estimate_usd?: number | null
}

export interface OptimizationFinding {
  id: string
  report_id?: string | null
  cluster_id?: string | null
  cluster_name?: string | null
  namespace?: string | null
  resource_type: string
  resource_name: string
  finding_type: string
  severity: string
  title: string
  description: string
  confidence_score?: number | null
  estimated_monthly_savings_usd?: number | null
  recommendation?: string | null
  remediation?: string | null
  ai_explanation?: string | null
  status: string
  created_at: string
}

export interface CostRecommendation {
  id: string
  report_id?: string | null
  finding_id?: string | null
  cluster_id?: string | null
  cluster_name?: string | null
  namespace?: string | null
  workload_name?: string | null
  workload_kind?: string | null
  resource_type?: string | null
  resource_name?: string | null
  optimization_type: string
  status: string
  severity: string
  confidence_score?: number | null
  title: string
  description?: string | null
  recommendation?: string | null
  impact?: string | null
  current_cpu_request_millicores?: number | null
  current_memory_request_mb?: number | null
  current_cpu_usage_avg_percent?: number | null
  current_memory_usage_avg_percent?: number | null
  current_replicas?: number | null
  recommended_cpu_request_millicores?: number | null
  recommended_memory_request_mb?: number | null
  recommended_replicas?: number | null
  estimated_monthly_savings_usd?: number | null
  estimated_cpu_savings_cores?: number | null
  estimated_memory_savings_gb?: number | null
  ai_explanation?: string | null
  remediation_yaml?: string | null
  priority: number
  created_at: string
}

export interface OptimizationReport {
  id: string
  report_name: string
  cluster_id?: string | null
  cluster_name?: string | null
  status: string
  analysis_window_hours: number
  total_resources_analyzed: number
  total_findings: number
  total_recommendations: number
  estimated_monthly_savings_usd: number
  estimated_annual_savings_usd: number
  optimization_score?: number | null
  summary?: string | null
  severity_breakdown?: Record<string, number> | null
  category_breakdown?: Record<string, number> | null
  impacted_resources?: Array<Record<string, unknown>> | null
  created_at: string
}

export interface OptimizationStats {
  total_recommendations: number
  open_recommendations: number
  implemented_recommendations: number
  in_progress_recommendations: number
  total_findings: number
  critical_findings: number
  high_findings: number
  estimated_monthly_savings_usd: number
  estimated_annual_savings_usd: number
  optimization_score: number
  severity_breakdown: Record<string, number>
  type_breakdown: Record<string, number>
  top_recommendations: CostRecommendation[]
}

export interface RecommendationListResponse {
  items: CostRecommendation[]
  total: number
  page: number
  page_size: number
}

export interface FindingListResponse {
  items: OptimizationFinding[]
  total: number
  page: number
  page_size: number
}

export interface ReportListResponse {
  items: OptimizationReport[]
  total: number
  page: number
  page_size: number
}

export interface OptimizationAnalysisResponse {
  report: OptimizationReport
  findings: OptimizationFinding[]
  recommendations: CostRecommendation[]
  utilization: ResourceUtilization[]
  stats: OptimizationStats
}

interface ListParams {
  page?: number
  page_size?: number
  cluster_id?: string
  optimization_type?: string
  severity?: string
  status?: string
}

export const optimizationApi = {
  stats: () => api.get<OptimizationStats>('/optimization/stats').then((r) => r.data),

  recommendations: (params?: ListParams) =>
    api.get<RecommendationListResponse>('/optimization/recommendations', { params }).then((r) => r.data),

  recommendation: (id: string) =>
    api.get<CostRecommendation>(`/optimization/recommendations/${id}`).then((r) => r.data),

  findings: (params?: ListParams & { finding_type?: string }) =>
    api.get<FindingListResponse>('/optimization/findings', { params }).then((r) => r.data),

  reports: (params?: ListParams) =>
    api.get<ReportListResponse>('/optimization/reports', { params }).then((r) => r.data),

  analyze: (payload?: { cluster_id?: string; demo?: boolean; analysis_window_hours?: number; report_name?: string }) =>
    api.post<OptimizationAnalysisResponse>('/optimization/analyze', payload ?? { demo: true }).then((r) => r.data),
}
