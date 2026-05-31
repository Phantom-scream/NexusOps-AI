import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Server,
  Cpu,
  MemoryStick,
  ChevronRight,
  Search,
  RefreshCw,
  ExternalLink,
  Globe,
} from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import StatusDot from '@/components/ui/StatusDot'
import ProgressBar from '@/components/ui/ProgressBar'
import MiniSparkline from '@/components/charts/MiniSparkline'
import MetricsAreaChart from '@/components/charts/MetricsAreaChart'
import { mockClusters, mockSummary, generateMultiSeries } from '@/data/mock'
import type { Cluster, CloudProvider, HealthStatus } from '@/types'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

const providerLabel: Record<CloudProvider, string> = {
  aws: 'Amazon Web Services',
  gcp: 'Google Cloud Platform',
  azure: 'Microsoft Azure',
  hybrid: 'Hybrid Cloud',
  'on-premise': 'On-Premise',
}

function ClusterCard({ cluster }: { cluster: Cluster }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22 }}
    >
      <Card hover className="overflow-hidden" onClick={() => setExpanded(v => !v)}>
        <div
          className={clsx(
            'h-0.5',
            cluster.status === 'healthy' ? 'bg-emerald-500' :
            cluster.status === 'degraded' ? 'bg-amber-500' :
            cluster.status === 'critical' ? 'bg-red-500' :
            cluster.status === 'maintenance' ? 'bg-violet-500' : 'bg-gray-600',
          )}
        />
        <div className="p-5">
          <div className="flex items-start justify-between gap-3 mb-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <StatusDot status={cluster.status} />
                <h3 className="text-sm font-semibold text-gray-100 truncate font-mono">{cluster.name}</h3>
              </div>
              <div className="flex items-center gap-2">
                <Badge value={cluster.provider} size="xs" />
                <span className="text-[10px] text-gray-600">{cluster.region}</span>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <Badge value={cluster.status} dot size="xs" />
              <ChevronRight className={clsx('w-3.5 h-3.5 text-gray-600 transition-transform', expanded && 'rotate-90')} />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-4">
            <div>
              <p className="text-[10px] text-gray-600 font-medium uppercase tracking-wide mb-1">Nodes</p>
              <p className="text-lg font-bold text-gray-100 tabular-nums">
                {cluster.healthyNodes}<span className="text-xs text-gray-500 font-normal">/{cluster.nodeCount}</span>
              </p>
            </div>
            <div>
              <p className="text-[10px] text-gray-600 font-medium uppercase tracking-wide mb-1">Pods</p>
              <p className="text-lg font-bold text-gray-100 tabular-nums">
                {cluster.podCount}<span className="text-xs text-gray-500 font-normal">/{cluster.totalPods}</span>
              </p>
            </div>
            <div>
              <p className="text-[10px] text-gray-600 font-medium uppercase tracking-wide mb-1">k8s</p>
              <p className="text-sm font-mono font-semibold text-gray-200">{cluster.k8sVersion}</p>
            </div>
          </div>

          <div className="space-y-2 mb-4">
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-[10px] text-gray-600 flex items-center gap-1"><Cpu className="w-2.5 h-2.5" /> CPU</span>
                <span className="text-[10px] font-mono text-gray-400">{cluster.cpuUsage}%</span>
              </div>
              <ProgressBar value={cluster.cpuUsage} height="xs" />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-[10px] text-gray-600 flex items-center gap-1"><MemoryStick className="w-2.5 h-2.5" /> Memory</span>
                <span className="text-[10px] font-mono text-gray-400">{cluster.memoryUsage}%</span>
              </div>
              <ProgressBar value={cluster.memoryUsage} height="xs" />
            </div>
          </div>

          <div className="flex items-end justify-between">
            <div>
              <p className="text-[10px] text-gray-700 mb-1">24h CPU trend</p>
              <MiniSparkline data={cluster.metrics.cpu} color="#6366f1" height={28} width={80} />
            </div>
            <div>
              <p className="text-[10px] text-gray-700 mb-1 text-right">Memory</p>
              <MiniSparkline data={cluster.metrics.memory} color="#10b981" height={28} width={80} />
            </div>
          </div>

          <div className="flex flex-wrap gap-1 mt-3">
            {cluster.tags.map(tag => (
              <span key={tag} className="text-[10px] bg-surface-300 text-gray-500 px-1.5 py-0.5 rounded font-mono">{tag}</span>
            ))}
          </div>
        </div>

        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="border-t border-white/[0.05] px-5 py-4 bg-surface-200/50"
            onClick={e => e.stopPropagation()}
          >
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Provider</span>
                  <span className="text-gray-300 font-medium">{providerLabel[cluster.provider]}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Region</span>
                  <span className="text-gray-300 font-mono">{cluster.region}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Namespaces</span>
                  <span className="text-gray-300">{cluster.namespaceCount}</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Created</span>
                  <span className="text-gray-300">{formatDistanceToNow(new Date(cluster.createdAt), { addSuffix: true })}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last synced</span>
                  <span className="text-gray-300">{formatDistanceToNow(new Date(cluster.lastSync), { addSuffix: true })}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Pod capacity</span>
                  <span className="text-gray-300">{Math.round((cluster.podCount / cluster.totalPods) * 100)}%</span>
                </div>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5">
                <ExternalLink className="w-3 h-3" /> Open Console
              </button>
              <button className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5">
                <RefreshCw className="w-3 h-3" /> Sync Now
              </button>
            </div>
          </motion.div>
        )}
      </Card>
    </motion.div>
  )
}

const statusFilters: Array<{ label: string; value: HealthStatus | 'all' }> = [
  { label: 'All', value: 'all' },
  { label: 'Healthy', value: 'healthy' },
  { label: 'Degraded', value: 'degraded' },
  { label: 'Maintenance', value: 'maintenance' },
]

const providerFilters: Array<{ label: string; value: CloudProvider | 'all' }> = [
  { label: 'All', value: 'all' },
  { label: 'AWS', value: 'aws' },
  { label: 'GCP', value: 'gcp' },
  { label: 'Azure', value: 'azure' },
]

export default function Clusters() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<HealthStatus | 'all'>('all')
  const [providerFilter, setProviderFilter] = useState<CloudProvider | 'all'>('all')
  const metricSeries = useMemo(() => generateMultiSeries(24), [])

  const filtered = useMemo(
    () =>
      mockClusters.filter(c => {
        if (search && !c.name.toLowerCase().includes(search.toLowerCase())) return false
        if (statusFilter !== 'all' && c.status !== statusFilter) return false
        if (providerFilter !== 'all' && c.provider !== providerFilter) return false
        return true
      }),
    [search, statusFilter, providerFilter],
  )

  const avgCpu = Math.round(mockClusters.reduce((s, c) => s + c.cpuUsage, 0) / mockClusters.length)
  const avgMem = Math.round(mockClusters.reduce((s, c) => s + c.memoryUsage, 0) / mockClusters.length)

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Infrastructure"
        subtitle="Multi-cloud Kubernetes cluster management and observability"
        breadcrumb={['Home', 'Infrastructure']}
        actions={
          <button className="btn-primary text-xs py-2 px-4 flex items-center gap-2">
            <Server className="w-3.5 h-3.5" /> Register Cluster
          </button>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Clusters', value: mockSummary.totalClusters, sub: `${mockSummary.healthyClusters} healthy`, color: 'text-brand-400' },
          { label: 'Total Nodes', value: mockSummary.totalNodes, sub: 'across all clusters', color: 'text-sky-400' },
          { label: 'Avg CPU Usage', value: `${avgCpu}%`, sub: 'cluster average', color: avgCpu > 80 ? 'text-red-400' : 'text-emerald-400' },
          { label: 'Avg Memory', value: `${avgMem}%`, sub: 'cluster average', color: avgMem > 80 ? 'text-red-400' : 'text-amber-400' },
        ].map(({ label, value, sub, color }) => (
          <Card key={label} className="p-5">
            <p className="text-2xl font-bold tabular-nums" style={{}}><span className={color}>{value}</span></p>
            <p className="text-xs text-gray-400 font-medium mt-0.5">{label}</p>
            <p className="text-xs text-gray-600 mt-0.5">{sub}</p>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader
          title="Aggregate Cluster Metrics"
          subtitle="Average CPU · Memory · Pod utilization (24h)"
          icon={<Globe className="w-3.5 h-3.5" />}
          actions={
            <div className="flex items-center gap-3">
              {[
                { key: 'cpu', label: 'CPU', color: '#6366f1' },
                { key: 'memory', label: 'Memory', color: '#10b981' },
                { key: 'requests', label: 'Pods %', color: '#f59e0b' },
              ].map(s => (
                <div key={s.key} className="flex items-center gap-1.5 text-xs text-gray-500">
                  <span className="w-3 h-0.5 rounded" style={{ backgroundColor: s.color }} />
                  {s.label}
                </div>
              ))}
            </div>
          }
        />
        <div className="p-4 pt-5">
          <MetricsAreaChart
            data={metricSeries}
            series={[
              { key: 'cpu',      label: 'CPU %',    color: '#6366f1', gradient: 'g-cpu' },
              { key: 'memory',   label: 'Memory %', color: '#10b981', gradient: 'g-mem' },
              { key: 'requests', label: 'Pods %',   color: '#f59e0b', gradient: 'g-req' },
            ]}
            height={180}
          />
        </div>
      </Card>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600 pointer-events-none" />
          <input
            type="text"
            placeholder="Filter clusters…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input pl-9 text-xs py-2"
          />
        </div>
        <div className="flex items-center gap-1 bg-surface-200 border border-white/[0.05] rounded-lg p-0.5">
          {statusFilters.map(f => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={clsx(
                'text-xs px-3 py-1.5 rounded-md font-medium transition-all',
                statusFilter === f.value ? 'bg-surface-400 text-gray-100' : 'text-gray-500 hover:text-gray-300',
              )}
            >{f.label}</button>
          ))}
        </div>
        <div className="flex items-center gap-1 bg-surface-200 border border-white/[0.05] rounded-lg p-0.5">
          {providerFilters.map(f => (
            <button
              key={f.value}
              onClick={() => setProviderFilter(f.value)}
              className={clsx(
                'text-xs px-3 py-1.5 rounded-md font-medium transition-all',
                providerFilter === f.value ? 'bg-surface-400 text-gray-100' : 'text-gray-500 hover:text-gray-300',
              )}
            >{f.label}</button>
          ))}
        </div>
        <span className="text-xs text-gray-600 ml-auto">{filtered.length} clusters</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
        {filtered.map(cluster => <ClusterCard key={cluster.id} cluster={cluster} />)}
        {filtered.length === 0 && (
          <div className="col-span-full flex flex-col items-center gap-3 py-16 text-center">
            <Server className="w-10 h-10 text-gray-700" />
            <p className="text-gray-500">No clusters match your filters</p>
            <button onClick={() => { setSearch(''); setStatusFilter('all'); setProviderFilter('all') }} className="btn-secondary text-xs">
              Clear filters
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
