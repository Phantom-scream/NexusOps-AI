import { useMemo, type ComponentProps, type ElementType, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  DollarSign,
  FileText,
  GitBranch,
  MemoryStick,
  RotateCcw,
  Server,
  Shield,
  Zap,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { format, formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import StatusDot from '@/components/ui/StatusDot'
import ProgressBar from '@/components/ui/ProgressBar'
import MetricsAreaChart from '@/components/charts/MetricsAreaChart'
import MiniSparkline from '@/components/charts/MiniSparkline'
import { clustersApi, type Cluster } from '@/services/clusters'
import { telemetryApi, type InfrastructureEvent, type LogEntry, type Metric, type TraceSpan } from '@/services/telemetry'
import { mockSummary } from '@/data/mock'
import type { MetricPoint } from '@/types'

const stagger = {
  container: { animate: { transition: { staggerChildren: 0.04 } } },
  item: {
    initial: { opacity: 0, y: 8 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.25 } },
  },
}

interface StatCardProps {
  label: string
  value: string | number
  subtext?: string
  icon: ElementType
  iconColor: string
  sparkline?: number[]
  sparkColor?: string
  onClick?: () => void
}

function StatCard({ label, value, subtext, icon: Icon, iconColor, sparkline, sparkColor, onClick }: StatCardProps) {
  return (
    <motion.div variants={stagger.item}>
      <Card hover={!!onClick} className="p-5 group" onClick={onClick}>
        <div className="flex items-start justify-between mb-3">
          <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center', iconColor)}>
            <Icon className="w-4 h-4" />
          </div>
          {sparkline && (
            <div className="opacity-70">
              <MiniSparkline data={sparkline} color={sparkColor ?? '#6366f1'} height={32} width={70} />
            </div>
          )}
        </div>
        <p className="text-2xl font-bold text-gray-50 tabular-nums">{value}</p>
        <p className="text-xs text-gray-500 font-medium">{label}</p>
        {subtext && <p className="text-xs text-gray-600 mt-2">{subtext}</p>}
      </Card>
    </motion.div>
  )
}

function buildMetricChart(metrics: Metric[], names: string[]): MetricPoint[] {
  const clusterMetrics = metrics.filter((metric) => metric.resource_type === 'cluster' && names.includes(metric.metric_name))
  const buckets = new Map<string, Record<string, number | string>>()

  clusterMetrics
    .slice()
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .forEach((metric) => {
      const bucket = format(new Date(metric.timestamp), 'HH:mm')
      const row = buckets.get(bucket) ?? { time: bucket }
      row[metric.metric_name] = Number(metric.value.toFixed(2))
      buckets.set(bucket, row)
    })

  return Array.from(buckets.values()) as MetricPoint[]
}

function latestAverage(metrics: Metric[], name: string) {
  const rows = metrics.filter((metric) => metric.metric_name === name && metric.resource_type === 'cluster')
  if (!rows.length) return 0
  const latest = rows.slice().sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(0, 4)
  return latest.reduce((sum, metric) => sum + metric.value, 0) / latest.length
}

function severityVariant(value: string): ComponentProps<typeof Badge>['variant'] {
  if (value === 'error' || value === 'critical') return 'critical'
  if (value === 'warn' || value === 'warning') return 'medium'
  if (value === 'normal') return 'healthy'
  return 'info'
}

function clusterStatus(status: string) {
  if (status === 'connected') return 'healthy'
  if (status === 'degraded') return 'degraded'
  if (status === 'disconnected') return 'down'
  return 'unknown'
}

function EmptyTelemetry({ onGenerate, loading }: { onGenerate: () => void; loading: boolean }) {
  return (
    <Card className="p-8 text-center">
      <Database className="w-10 h-10 mx-auto text-brand-400/60 mb-3" />
      <h3 className="text-lg font-semibold text-gray-100">No telemetry has been ingested yet</h3>
      <p className="text-sm text-gray-500 mt-1 max-w-xl mx-auto">
        Generate demo telemetry to populate metrics, logs, events, and traces from the same infrastructure topology APIs used by Kubernetes discovery.
      </p>
      <button
        onClick={onGenerate}
        disabled={loading}
        className="mt-5 inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-400 disabled:opacity-60"
      >
        <RotateCcw className={clsx('w-4 h-4', loading && 'animate-spin')} />
        {loading ? 'Generating telemetry' : 'Generate demo telemetry'}
      </button>
    </Card>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const clustersQuery = useQuery({
    queryKey: ['dashboard-clusters'],
    queryFn: () => clustersApi.list({ page_size: 50 }),
  })
  const telemetryQuery = useQuery({
    queryKey: ['dashboard-telemetry-metrics'],
    queryFn: () => telemetryApi.metrics({ limit: 1600 }),
  })
  const logsQuery = useQuery({
    queryKey: ['dashboard-telemetry-logs'],
    queryFn: () => telemetryApi.logs({ limit: 12 }),
  })
  const eventsQuery = useQuery({
    queryKey: ['dashboard-telemetry-events'],
    queryFn: () => telemetryApi.events({ limit: 12 }),
  })
  const tracesQuery = useQuery({
    queryKey: ['dashboard-telemetry-traces'],
    queryFn: () => telemetryApi.traces({ limit: 30 }),
  })
  const summaryQuery = useQuery({
    queryKey: ['dashboard-telemetry-summary'],
    queryFn: telemetryApi.summary,
  })

  const generateTelemetry = useMutation({
    mutationFn: telemetryApi.generateDemo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-telemetry-metrics'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-telemetry-logs'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-telemetry-events'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-telemetry-traces'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-telemetry-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-clusters'] })
    },
  })

  const clusters = clustersQuery.data?.items ?? []
  const metrics = telemetryQuery.data ?? []
  const logs = logsQuery.data ?? []
  const events = eventsQuery.data ?? []
  const traces = tracesQuery.data ?? []
  const hasTelemetry = metrics.length > 0 || logs.length > 0 || events.length > 0 || traces.length > 0

  const cpuMemoryChart = useMemo(() => buildMetricChart(metrics, ['cpu_usage_percent', 'memory_usage_percent']), [metrics])
  const reliabilityChart = useMemo(() => buildMetricChart(metrics, ['error_rate_percent', 'pod_restarts']), [metrics])
  const cpuSpark = cpuMemoryChart.map((row) => Number(row.cpu_usage_percent ?? 0)).slice(-12)
  const memorySpark = cpuMemoryChart.map((row) => Number(row.memory_usage_percent ?? 0)).slice(-12)
  const restartSpark = reliabilityChart.map((row) => Number(row.pod_restarts ?? 0)).slice(-12)
  const errorSpark = reliabilityChart.map((row) => Number(row.error_rate_percent ?? 0)).slice(-12)

  const healthyClusters = clusters.filter((cluster) => cluster.status === 'connected').length
  const degradedClusters = clusters.filter((cluster) => cluster.status !== 'connected').length
  const latestCpu = latestAverage(metrics, 'cpu_usage_percent')
  const latestMemory = latestAverage(metrics, 'memory_usage_percent')
  const latestErrorRate = latestAverage(metrics, 'error_rate_percent')
  const recentRestarts = metrics
    .filter((metric) => metric.metric_name === 'pod_restarts' && metric.resource_type === 'cluster')
    .slice(0, 8)
    .reduce((sum, metric) => sum + metric.value, 0)

  const traceGroups = Object.values(
    traces.reduce<Record<string, TraceSpan[]>>((acc, span) => {
      acc[span.trace_id] = [...(acc[span.trace_id] ?? []), span]
      return acc
    }, {}),
  )

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Operations Center"
        subtitle="Infrastructure telemetry, events, logs, and traces from provider-neutral observability APIs"
        breadcrumb={['Home', 'Dashboard']}
        statusChips={
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs">
              <StatusDot status={degradedClusters ? 'degraded' : 'healthy'} size="xs" />
              <span className="text-emerald-400 font-medium">{healthyClusters}/{clusters.length || 0} clusters connected</span>
            </div>
            <div className="w-px h-3.5 bg-gray-700" />
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              <span>
                {summaryQuery.data?.latest_timestamp
                  ? `Updated ${formatDistanceToNow(new Date(summaryQuery.data.latest_timestamp), { addSuffix: true })}`
                  : 'Awaiting telemetry'}
              </span>
            </div>
          </div>
        }
      />

      {!hasTelemetry && !telemetryQuery.isLoading && (
        <EmptyTelemetry onGenerate={() => generateTelemetry.mutate()} loading={generateTelemetry.isPending} />
      )}

      <motion.div
        variants={stagger.container}
        initial="initial"
        animate="animate"
        className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4"
      >
        <StatCard
          label="Clusters"
          value={clusters.length}
          icon={Server}
          iconColor="bg-brand-500/15 text-brand-400"
          subtext={`${clusters.reduce((sum, cluster) => sum + cluster.node_count, 0)} nodes`}
          onClick={() => navigate('/clusters')}
        />
        <StatCard
          label="CPU Usage"
          value={`${latestCpu.toFixed(1)}%`}
          icon={Cpu}
          iconColor="bg-sky-500/15 text-sky-400"
          sparkline={cpuSpark}
          sparkColor="#38bdf8"
        />
        <StatCard
          label="Memory Usage"
          value={`${latestMemory.toFixed(1)}%`}
          icon={MemoryStick}
          iconColor="bg-violet-500/15 text-violet-400"
          sparkline={memorySpark}
          sparkColor="#a78bfa"
        />
        <StatCard
          label="Error Rate"
          value={`${latestErrorRate.toFixed(2)}%`}
          icon={AlertTriangle}
          iconColor={latestErrorRate > 2 ? 'bg-red-500/15 text-red-400' : 'bg-amber-500/15 text-amber-400'}
          sparkline={errorSpark}
          sparkColor="#f43f5e"
        />
        <StatCard
          label="Pod Restarts"
          value={Math.round(recentRestarts)}
          icon={Zap}
          iconColor="bg-red-500/15 text-red-400"
          sparkline={restartSpark}
          sparkColor="#f97316"
        />
        <StatCard
          label="Trace Spans"
          value={summaryQuery.data?.traces ?? traces.length}
          icon={GitBranch}
          iconColor="bg-emerald-500/15 text-emerald-400"
          subtext={`${traceGroups.length} traces sampled`}
        />
      </motion.div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card>
          <CardHeader
            title="CPU & Memory"
            subtitle="Cluster aggregate telemetry"
            icon={<Activity className="w-3.5 h-3.5" />}
            actions={
              <button
                onClick={() => generateTelemetry.mutate()}
                disabled={generateTelemetry.isPending}
                className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 disabled:opacity-60"
              >
                Refresh demo <RotateCcw className={clsx('w-3 h-3', generateTelemetry.isPending && 'animate-spin')} />
              </button>
            }
          />
          <div className="p-4 pt-5">
            <MetricsAreaChart
              data={cpuMemoryChart}
              series={[
                { key: 'cpu_usage_percent', label: 'CPU %', color: '#38bdf8', gradient: 'grad-cpu' },
                { key: 'memory_usage_percent', label: 'Memory %', color: '#a78bfa', gradient: 'grad-memory' },
              ]}
              height={220}
            />
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Reliability Signals"
            subtitle="Error rates and restart trend"
            icon={<AlertTriangle className="w-3.5 h-3.5" />}
          />
          <div className="p-4 pt-5">
            <MetricsAreaChart
              data={reliabilityChart}
              series={[
                { key: 'error_rate_percent', label: 'Error %', color: '#f43f5e', gradient: 'grad-errors' },
                { key: 'pod_restarts', label: 'Restarts', color: '#f97316', gradient: 'grad-restarts' },
              ]}
              height={220}
            />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <TelemetryList title="Recent Logs" icon={FileText} empty="No logs ingested">
          {logs.slice(0, 8).map((log) => (
            <LogRow key={log.id} log={log} />
          ))}
        </TelemetryList>

        <TelemetryList title="Infrastructure Events" icon={Activity} empty="No events ingested">
          {events.slice(0, 8).map((event) => (
            <EventRow key={event.id} event={event} />
          ))}
        </TelemetryList>

        <TelemetryList title="Trace Summaries" icon={GitBranch} empty="No traces ingested">
          {traceGroups.slice(0, 6).map((group) => (
            <TraceRow key={group[0].trace_id} spans={group} />
          ))}
        </TelemetryList>
      </div>

      <Card>
        <CardHeader
          title="Cluster Overview"
          subtitle={`${clusters.length} clusters · ${clusters.reduce((sum, cluster) => sum + cluster.pod_count, 0)} pods`}
          icon={<Server className="w-3.5 h-3.5" />}
          actions={
            <button onClick={() => navigate('/clusters')} className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
              Manage <ArrowRight className="w-3 h-3" />
            </button>
          }
        />
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-3">
          {clusters.map((cluster) => (
            <ClusterTile key={cluster.id} cluster={cluster} onClick={() => navigate('/clusters')} />
          ))}
          {!clusters.length && (
            <div className="col-span-full py-8 text-center text-sm text-gray-500">
              Generate demo infrastructure from the Clusters page or generate demo telemetry to bootstrap the environment.
            </div>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          label="Security Findings"
          value={mockSummary.securityFindings}
          icon={Shield}
          iconColor="bg-amber-500/15 text-amber-400"
          subtext="Security module remains Phase 7-backed"
          onClick={() => navigate('/security')}
        />
        <StatCard
          label="Est. Monthly Savings"
          value={`$${(mockSummary.totalSavings / 1000).toFixed(1)}k`}
          icon={DollarSign}
          iconColor="bg-emerald-500/15 text-emerald-400"
          subtext="Cost optimization module remains Phase 8-backed"
          onClick={() => navigate('/cost')}
        />
        <StatCard
          label="Telemetry Records"
          value={summaryQuery.data ? summaryQuery.data.metrics + summaryQuery.data.logs + summaryQuery.data.events + summaryQuery.data.traces : 0}
          icon={Database}
          iconColor="bg-brand-500/15 text-brand-400"
          subtext={`${summaryQuery.data?.sources ?? 0} sources registered`}
        />
      </div>
    </div>
  )
}

function TelemetryList({ title, icon: Icon, empty, children }: { title: string; icon: ElementType; empty: string; children: ReactNode }) {
  const hasRows = Boolean(children && (Array.isArray(children) ? children.length : true))
  return (
    <Card className="h-full">
      <CardHeader title={title} icon={<Icon className="w-3.5 h-3.5" />} />
      <div className="divide-y divide-white/[0.04]">
        {hasRows ? children : <div className="px-5 py-8 text-center text-sm text-gray-500">{empty}</div>}
      </div>
    </Card>
  )
}

function LogRow({ log }: { log: LogEntry }) {
  return (
    <div className="px-5 py-3 hover:bg-white/[0.02] transition-colors">
      <div className="flex items-center justify-between gap-3">
        <Badge value={log.severity} variant={severityVariant(log.severity)} dot size="xs" />
        <span className="text-[10px] text-gray-600">{formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}</span>
      </div>
      <p className="text-xs text-gray-300 mt-2 line-clamp-2">{log.message}</p>
      <p className="text-[10px] text-gray-600 mt-1 font-mono truncate">{log.namespace_name ?? 'cluster'} / {log.pod_name ?? log.deployment_name ?? log.source}</p>
    </div>
  )
}

function EventRow({ event }: { event: InfrastructureEvent }) {
  return (
    <div className="px-5 py-3 hover:bg-white/[0.02] transition-colors">
      <div className="flex items-center justify-between gap-3">
        <Badge value={event.severity} variant={severityVariant(event.severity)} dot size="xs" />
        <span className="text-[10px] text-gray-600">{event.reason}</span>
      </div>
      <p className="text-xs text-gray-300 mt-2 line-clamp-2">{event.message}</p>
      <p className="text-[10px] text-gray-600 mt-1 font-mono truncate">{event.resource_type}:{event.resource_name}</p>
    </div>
  )
}

function TraceRow({ spans }: { spans: TraceSpan[] }) {
  const root = spans.find((span) => !span.parent_span_id) ?? spans[0]
  const slowest = spans.slice().sort((a, b) => b.duration_ms - a.duration_ms)[0]
  const failed = spans.some((span) => span.status !== 'ok')
  return (
    <div className="px-5 py-3 hover:bg-white/[0.02] transition-colors">
      <div className="flex items-center justify-between gap-3">
        <Badge value={failed ? 'error' : 'ok'} variant={failed ? 'critical' : 'healthy'} dot size="xs" />
        <span className="text-[10px] text-gray-600">{spans.length} spans</span>
      </div>
      <p className="text-xs text-gray-300 mt-2 truncate">{root.operation_name}</p>
      <p className="text-[10px] text-gray-600 mt-1 font-mono truncate">
        slowest {slowest.service_name} · {slowest.duration_ms}ms
      </p>
    </div>
  )
}

function ClusterTile({ cluster, onClick }: { cluster: Cluster; onClick: () => void }) {
  const status = clusterStatus(cluster.status)
  const cpuEstimate = Math.min(100, Math.round(((cluster.cpu_capacity ?? 1) / Math.max(cluster.node_count, 1)) * 8))
  return (
    <button
      onClick={onClick}
      className={clsx(
        'text-left p-3 rounded-lg border transition-colors group',
        status === 'healthy'
          ? 'bg-emerald-500/5 border-emerald-500/15 hover:border-emerald-500/30'
          : status === 'degraded'
          ? 'bg-amber-500/5 border-amber-500/20 hover:border-amber-500/35'
          : 'bg-surface-200 border-white/[0.05] hover:border-white/[0.12]',
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <StatusDot status={status} size="xs" />
        <span className="text-[9px] font-mono text-gray-600 uppercase">{cluster.provider}</span>
      </div>
      <p className="text-xs font-medium text-gray-200 truncate leading-snug">{cluster.display_name}</p>
      <p className="text-[10px] text-gray-600 mt-1">{cluster.node_count} nodes · {cluster.pod_count} pods</p>
      <ProgressBar value={cpuEstimate} height="xs" className="mt-2" />
      <p className="text-[9px] text-gray-700 mt-1 text-right">{cluster.environment}</p>
    </button>
  )
}
