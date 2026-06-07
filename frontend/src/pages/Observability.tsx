import { useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format, formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'
import {
  Activity,
  AlertCircle,
  FileText,
  GitBranch,
  LineChart,
  RadioTower,
  RefreshCw,
} from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import MetricsAreaChart from '@/components/charts/MetricsAreaChart'
import { ChartSkeleton } from '@/components/ui/Skeleton'
import { telemetryApi, type Metric } from '@/services/telemetry'
import type { MetricPoint } from '@/types'

function chartRows(metrics: Metric[], names: string[]): MetricPoint[] {
  const buckets = new Map<string, Record<string, string | number>>()
  metrics
    .filter((metric) => names.includes(metric.metric_name))
    .slice()
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .forEach((metric) => {
      const time = format(new Date(metric.timestamp), 'HH:mm')
      const row = buckets.get(time) ?? { time }
      row[metric.metric_name] = Number(metric.value.toFixed(2))
      buckets.set(time, row)
    })
  return Array.from(buckets.values()) as MetricPoint[]
}

export default function Observability() {
  const queryClient = useQueryClient()
  const metricsQuery = useQuery({ queryKey: ['observability', 'metrics'], queryFn: () => telemetryApi.metrics({ limit: 1800 }) })
  const logsQuery = useQuery({ queryKey: ['observability', 'logs'], queryFn: () => telemetryApi.logs({ limit: 12 }) })
  const eventsQuery = useQuery({ queryKey: ['observability', 'events'], queryFn: () => telemetryApi.events({ limit: 12 }) })
  const tracesQuery = useQuery({ queryKey: ['observability', 'traces'], queryFn: () => telemetryApi.traces({ limit: 80 }) })
  const summaryQuery = useQuery({ queryKey: ['observability', 'summary'], queryFn: telemetryApi.summary })

  const generateDemo = useMutation({
    mutationFn: telemetryApi.generateDemo,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['observability'] }),
  })

  const metrics = metricsQuery.data ?? []
  const logs = logsQuery.data ?? []
  const events = eventsQuery.data ?? []
  const traces = tracesQuery.data ?? []
  const saturation = useMemo(() => chartRows(metrics, ['cpu_usage_percent', 'memory_usage_percent']), [metrics])
  const reliability = useMemo(() => chartRows(metrics, ['error_rate_percent', 'pod_restarts']), [metrics])
  const requestVolume = useMemo(() => chartRows(metrics, ['request_count']), [metrics])

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Observability Suite"
        subtitle="Unified metrics, logs, events, and traces for infrastructure-aware operations"
        breadcrumb={['Home', 'Observability']}
        statusChips={
          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
            <span className="text-cyan-300 font-medium">{summaryQuery.data?.sources ?? 0} telemetry sources</span>
            <span>·</span>
            <span>
              {summaryQuery.data?.latest_timestamp
                ? `Updated ${formatDistanceToNow(new Date(summaryQuery.data.latest_timestamp), { addSuffix: true })}`
                : 'Awaiting data'}
            </span>
          </div>
        }
        actions={
          <button
            onClick={() => generateDemo.mutate()}
            disabled={generateDemo.isPending}
            className="btn-primary text-xs py-2 px-4"
          >
            <RefreshCw className={clsx('w-3.5 h-3.5', generateDemo.isPending && 'animate-spin')} />
            {generateDemo.isPending ? 'Generating' : 'Refresh Demo'}
          </button>
        }
      />

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <SignalCard icon={LineChart} label="Metrics" value={summaryQuery.data?.metrics ?? 0} tone="text-cyan-300" />
        <SignalCard icon={FileText} label="Logs" value={summaryQuery.data?.logs ?? 0} tone="text-sky-300" />
        <SignalCard icon={AlertCircle} label="Events" value={summaryQuery.data?.events ?? 0} tone="text-amber-300" />
        <SignalCard icon={GitBranch} label="Trace Spans" value={summaryQuery.data?.traces ?? 0} tone="text-violet-300" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card>
          <CardHeader title="Saturation" subtitle="CPU and memory pressure" icon={<Activity className="w-3.5 h-3.5" />} />
          <div className="p-4 pt-2">
            {metricsQuery.isLoading ? <ChartSkeleton height={240} /> : (
              <MetricsAreaChart
                data={saturation}
                height={240}
                series={[
                  { key: 'cpu_usage_percent', label: 'CPU', color: '#22d3ee', gradient: 'obs-cpu' },
                  { key: 'memory_usage_percent', label: 'Memory', color: '#8b5cf6', gradient: 'obs-mem' },
                ]}
              />
            )}
          </div>
        </Card>
        <Card>
          <CardHeader title="Reliability" subtitle="Errors and restart churn" icon={<RadioTower className="w-3.5 h-3.5" />} />
          <div className="p-4 pt-2">
            {metricsQuery.isLoading ? <ChartSkeleton height={240} /> : (
              <MetricsAreaChart
                data={reliability}
                height={240}
                series={[
                  { key: 'error_rate_percent', label: 'Error Rate', color: '#f43f5e', gradient: 'obs-err' },
                  { key: 'pod_restarts', label: 'Restarts', color: '#f59e0b', gradient: 'obs-rst' },
                ]}
              />
            )}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Request Volume" subtitle="Application throughput signals" icon={<LineChart className="w-3.5 h-3.5" />} />
        <div className="p-4 pt-2">
          {metricsQuery.isLoading ? <ChartSkeleton height={180} /> : (
            <MetricsAreaChart
              data={requestVolume}
              height={180}
              series={[{ key: 'request_count', label: 'Requests', color: '#10b981', gradient: 'obs-req' }]}
            />
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Feed title="Recent Logs" items={logs.map((log) => ({
          id: log.id,
          badge: log.severity,
          title: log.message,
          meta: `${log.namespace_name ?? 'global'} / ${log.pod_name ?? log.deployment_name ?? log.source}`,
        }))} />
        <Feed title="Infrastructure Events" items={events.map((event) => ({
          id: event.id,
          badge: event.severity,
          title: event.message,
          meta: `${event.reason} · ${event.resource_type}:${event.resource_name}`,
        }))} />
        <Feed title="Trace Summaries" items={traces.slice(0, 12).map((trace) => ({
          id: trace.id,
          badge: trace.status,
          title: `${trace.operation_name} · ${trace.duration_ms}ms`,
          meta: `${trace.service_name} / ${trace.trace_id.slice(0, 10)}`,
        }))} />
      </div>
    </div>
  )
}

function SignalCard({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: React.ElementType
  label: string
  value: number
  tone: string
}) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="w-9 h-9 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center">
          <Icon className={clsx('w-4 h-4', tone)} />
        </div>
        <span className="text-[10px] uppercase tracking-[0.2em] text-gray-600">signal</span>
      </div>
      <p className={clsx('text-3xl font-bold tabular-nums', tone)}>{value.toLocaleString()}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </Card>
  )
}

function Feed({
  title,
  items,
}: {
  title: string
  items: Array<{ id: string; badge: string; title: string; meta: string }>
}) {
  return (
    <Card>
      <CardHeader title={title} />
      <div className="divide-y divide-white/[0.05]">
        {items.length ? items.map((item) => (
          <div key={item.id} className="px-5 py-3">
            <Badge value={item.badge} size="xs" />
            <p className="text-xs text-gray-200 mt-2 line-clamp-2">{item.title}</p>
            <p className="text-[10px] text-gray-600 mt-1 font-mono">{item.meta}</p>
          </div>
        )) : (
          <div className="p-6 text-sm text-gray-500">No signals available.</div>
        )}
      </div>
    </Card>
  )
}
