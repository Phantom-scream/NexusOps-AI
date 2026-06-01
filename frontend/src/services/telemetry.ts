import { api } from './api'

export interface TelemetrySource {
  id: string
  name: string
  source_type: string
  endpoint_url?: string | null
  cluster_id?: string | null
  is_active: boolean
  config?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface Metric {
  id: string
  timestamp: string
  metric_name: string
  value: number
  unit: string
  resource_type: string
  resource_name?: string | null
  source_id?: string | null
  cluster_id?: string | null
  namespace_name?: string | null
  deployment_name?: string | null
  pod_name?: string | null
  service_name?: string | null
  incident_id?: string | null
  labels?: Record<string, unknown>
}

export interface LogEntry {
  id: string
  timestamp: string
  severity: string
  source: string
  message: string
  source_id?: string | null
  cluster_id?: string | null
  namespace_name?: string | null
  deployment_name?: string | null
  pod_name?: string | null
  service_name?: string | null
  incident_id?: string | null
  trace_id?: string | null
  span_id?: string | null
  attributes?: Record<string, unknown>
}

export interface InfrastructureEvent {
  id: string
  timestamp: string
  event_type: string
  reason: string
  severity: string
  message: string
  resource_type: string
  resource_name: string
  source_id?: string | null
  cluster_id?: string | null
  namespace_name?: string | null
  deployment_name?: string | null
  pod_name?: string | null
  service_name?: string | null
  incident_id?: string | null
  attributes?: Record<string, unknown>
}

export interface TraceSpan {
  id: string
  trace_id: string
  span_id: string
  parent_span_id?: string | null
  operation_name: string
  service_name: string
  status: string
  start_time: string
  end_time: string
  duration_ms: number
  source_id?: string | null
  cluster_id?: string | null
  namespace_name?: string | null
  deployment_name?: string | null
  pod_name?: string | null
  incident_id?: string | null
  attributes?: Record<string, unknown>
}

export interface TelemetrySummary {
  metrics: number
  logs: number
  events: number
  traces: number
  sources: number
  latest_timestamp?: string | null
}

export interface DemoTelemetryResponse {
  status: string
  clusters: number
  metrics: number
  logs: number
  events: number
  traces: number
  source: TelemetrySource
}

interface TelemetryParams {
  cluster_id?: string
  metric_name?: string
  severity?: string
  resource_type?: string
  namespace_name?: string
  deployment_name?: string
  pod_name?: string
  service_name?: string
  incident_id?: string
  limit?: number
}

export const telemetryApi = {
  sources: () =>
    api.get<TelemetrySource[]>('/telemetry/sources').then((r) => r.data),

  summary: () =>
    api.get<TelemetrySummary>('/telemetry/summary').then((r) => r.data),

  metrics: (params?: TelemetryParams) =>
    api.get<Metric[]>('/metrics', { params }).then((r) => r.data),

  logs: (params?: TelemetryParams) =>
    api.get<LogEntry[]>('/logs', { params }).then((r) => r.data),

  events: (params?: TelemetryParams) =>
    api.get<InfrastructureEvent[]>('/events', { params }).then((r) => r.data),

  traces: (params?: TelemetryParams) =>
    api.get<TraceSpan[]>('/traces', { params }).then((r) => r.data),

  clusterMetrics: (clusterId: string, params?: TelemetryParams) =>
    api.get<Metric[]>(`/clusters/${clusterId}/metrics`, { params }).then((r) => r.data),

  clusterLogs: (clusterId: string, params?: TelemetryParams) =>
    api.get<LogEntry[]>(`/clusters/${clusterId}/logs`, { params }).then((r) => r.data),

  clusterEvents: (clusterId: string, params?: TelemetryParams) =>
    api.get<InfrastructureEvent[]>(`/clusters/${clusterId}/events`, { params }).then((r) => r.data),

  clusterTraces: (clusterId: string, params?: TelemetryParams) =>
    api.get<TraceSpan[]>(`/clusters/${clusterId}/traces`, { params }).then((r) => r.data),

  generateDemo: () =>
    api.post<DemoTelemetryResponse>('/demo/telemetry/generate').then((r) => r.data),
}
