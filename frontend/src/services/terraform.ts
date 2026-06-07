import { api } from './api'

export interface TerraformWorkspace {
  id: string
  name: string
  description?: string | null
  source_type: string
  repository_url?: string | null
  branch?: string | null
  root_path?: string | null
  provider?: string | null
  environment?: string | null
  owner?: string | null
  last_scan_id?: string | null
  created_at: string
  updated_at: string
}

export interface TerraformFinding {
  id: string
  workspace_id: string
  scan_id?: string | null
  resource_id?: string | null
  title: string
  description: string
  impact?: string | null
  severity: string
  category: string
  status: string
  scanner: string
  rule_id?: string | null
  resource_address?: string | null
  resource_type?: string | null
  file_path?: string | null
  line_number?: number | null
  remediation?: string | null
  ai_explanation?: string | null
  confidence_score?: number | null
  created_at: string
}

export interface TerraformDrift {
  id: string
  workspace_id: string
  scan_id?: string | null
  resource_id?: string | null
  resource_address: string
  resource_type?: string | null
  attribute_path: string
  desired_value?: unknown
  actual_value?: unknown
  drift_type: string
  severity: string
  status: string
  description: string
  remediation?: string | null
  confidence_score?: number | null
  created_at: string
}

export interface TerraformScan {
  id: string
  workspace_id?: string | null
  scan_name: string
  source_type: string
  repository_url?: string | null
  branch?: string | null
  scan_path?: string | null
  status: string
  findings_count: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  policy_violation_count: number
  drift_count: number
  drift_detected: boolean
  ai_summary?: string | null
  created_at: string
}

export interface TerraformStats {
  total_workspaces: number
  total_resources: number
  total_findings: number
  open_findings: number
  critical_findings: number
  high_findings: number
  drift_count: number
  policy_violation_count: number
  severity_breakdown: Record<string, number>
  category_breakdown: Record<string, number>
}

export interface TerraformFindingListResponse {
  items: TerraformFinding[]
  total: number
  page: number
  page_size: number
}

export interface TerraformDriftListResponse {
  items: TerraformDrift[]
  total: number
  page: number
  page_size: number
}

export interface TerraformAnalysisResponse {
  workspace: TerraformWorkspace
  scan: TerraformScan
  findings: TerraformFinding[]
  drift: TerraformDrift[]
  stats: TerraformStats
}

export interface TerraformAnalyzeRequest {
  workspace_id?: string
  workspace_name?: string
  files?: Record<string, string>
  terraform_content?: string
  state?: Record<string, unknown>
  demo?: boolean
  scan_name?: string
}

interface TerraformListParams {
  page?: number
  page_size?: number
  workspace_id?: string
  severity?: string
  category?: string
  status?: string
}

export const terraformApi = {
  stats: () => api.get<TerraformStats>('/terraform/stats').then((r) => r.data),

  workspaces: () => api.get<TerraformWorkspace[]>('/terraform/workspaces').then((r) => r.data),

  scans: () => api.get<TerraformScan[]>('/terraform/scans').then((r) => r.data),

  findings: (params?: TerraformListParams) =>
    api.get<TerraformFindingListResponse>('/terraform/findings', { params }).then((r) => r.data),

  finding: (id: string) => api.get<TerraformFinding>(`/terraform/findings/${id}`).then((r) => r.data),

  drift: (params?: TerraformListParams) =>
    api.get<TerraformDriftListResponse>('/terraform/drift', { params }).then((r) => r.data),

  analyze: (payload: TerraformAnalyzeRequest) =>
    api.post<TerraformAnalysisResponse>('/terraform/analyze', payload).then((r) => r.data),
}
