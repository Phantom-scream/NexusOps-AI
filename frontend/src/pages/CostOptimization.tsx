import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock,
  Cpu,
  DollarSign,
  Gauge,
  HardDrive,
  RefreshCw,
  Search,
  Server,
  TrendingDown,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import DonutChart from '@/components/charts/DonutChart'
import MetricsBarChart from '@/components/charts/MetricsBarChart'
import { optimizationApi, type CostRecommendation } from '@/services/optimization'

const typeLabels: Record<string, string> = {
  cpu_oversizing: 'CPU Oversizing',
  memory_oversizing: 'Memory Oversizing',
  excessive_replicas: 'Excess Replicas',
  idle_service: 'Idle Services',
  missing_autoscaling: 'Autoscaling',
  restart_waste: 'Restart Waste',
  right_sizing: 'Right Sizing',
  idle_removal: 'Idle Removal',
  autoscaling: 'Autoscaling',
}

const typeColors: Record<string, string> = {
  cpu_oversizing: '#38bdf8',
  memory_oversizing: '#a78bfa',
  excessive_replicas: '#f59e0b',
  idle_service: '#ef4444',
  missing_autoscaling: '#10b981',
  restart_waste: '#f97316',
  right_sizing: '#6366f1',
  idle_removal: '#ef4444',
  autoscaling: '#10b981',
}

const severityFilters = ['all', 'critical', 'high', 'medium', 'low']

export default function CostOptimization() {
  const queryClient = useQueryClient()
  const [severityFilter, setSeverityFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<CostRecommendation | null>(null)

  const statsQuery = useQuery({ queryKey: ['optimization', 'stats'], queryFn: optimizationApi.stats })
  const recommendationsQuery = useQuery({
    queryKey: ['optimization', 'recommendations', severityFilter],
    queryFn: () => optimizationApi.recommendations({
      page_size: 100,
      status: 'open',
      severity: severityFilter === 'all' ? undefined : severityFilter,
    }),
  })
  const findingsQuery = useQuery({
    queryKey: ['optimization', 'findings'],
    queryFn: () => optimizationApi.findings({ page_size: 100, status: 'open' }),
  })
  const reportsQuery = useQuery({
    queryKey: ['optimization', 'reports'],
    queryFn: () => optimizationApi.reports({ page_size: 8 }),
  })

  const analyzeMutation = useMutation({
    mutationFn: () => optimizationApi.analyze({ demo: true, analysis_window_hours: 24, report_name: 'Demo cost optimization analysis' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['optimization'] })
    },
  })

  const stats = statsQuery.data
  const recommendations = recommendationsQuery.data?.items ?? []
  const findings = findingsQuery.data?.items ?? []
  const reports = reportsQuery.data?.items ?? []

  const filteredRecommendations = useMemo(() => {
    const needle = search.trim().toLowerCase()
    if (!needle) return recommendations
    return recommendations.filter((item) =>
      [item.title, item.description, item.workload_name, item.namespace, item.optimization_type]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle)),
    )
  }, [recommendations, search])

  const typeData = Object.entries(stats?.type_breakdown ?? {})
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({
      name: typeLabels[name] ?? name,
      value,
      color: typeColors[name] ?? '#6b7280',
    }))

  const savingsBars = filteredRecommendations.slice(0, 8).map((item) => ({
    time: item.workload_name ?? item.resource_name ?? 'resource',
    name: item.workload_name ?? item.resource_name ?? 'resource',
    savings: Math.round(item.estimated_monthly_savings_usd ?? 0),
  }))

  const isLoading = statsQuery.isLoading || recommendationsQuery.isLoading

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Cost Optimization"
        subtitle="Resource intelligence, utilization analysis, and Kubernetes savings recommendations"
        breadcrumb={['Home', 'Cost Optimization']}
        actions={
          <button
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending}
            className="btn-primary text-xs py-2 px-4 flex items-center gap-2 disabled:opacity-60"
          >
            <RefreshCw className={clsx('w-3.5 h-3.5', analyzeMutation.isPending && 'animate-spin')} />
            {analyzeMutation.isPending ? 'Analyzing' : 'Run Demo Analysis'}
          </button>
        }
      />

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <SummaryCard label="Monthly Savings" value={currency(stats?.estimated_monthly_savings_usd ?? 0)} sub={`${currency(stats?.estimated_annual_savings_usd ?? 0)}/yr`} tone="text-emerald-400" />
        <SummaryCard label="Open Recommendations" value={stats?.open_recommendations ?? 0} sub={`${stats?.total_findings ?? 0} findings`} tone="text-sky-400" />
        <SummaryCard label="Critical / High" value={`${stats?.critical_findings ?? 0}/${stats?.high_findings ?? 0}`} sub="priority opportunities" tone="text-orange-400" />
        <SummaryCard label="Optimization Score" value={`${stats?.optimization_score ?? 100}`} sub="higher is healthier" tone="text-violet-400" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card className="xl:col-span-2">
          <CardHeader
            title="Savings Opportunities"
            subtitle="Top monthly savings by workload"
            icon={<DollarSign className="w-3.5 h-3.5" />}
          />
          <div className="p-4 pt-2">
            {savingsBars.length ? (
              <MetricsBarChart
                data={savingsBars}
                bars={[{ key: 'savings', label: 'Savings ($/mo)', color: '#10b981' }]}
                height={210}
              />
            ) : (
              <EmptyState text="Run analysis to generate savings estimates." />
            )}
          </div>
        </Card>

        <Card>
          <CardHeader title="Finding Types" icon={<Gauge className="w-3.5 h-3.5" />} />
          <div className="p-5 flex items-center justify-center">
            <DonutChart
              data={typeData}
              size={170}
              innerRadius={54}
              outerRadius={76}
              centerValue={stats?.total_findings ?? 0}
              centerLabel="findings"
              showLegend
            />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card>
          <CardHeader title="Severity Breakdown" icon={<TrendingDown className="w-3.5 h-3.5" />} />
          <div className="p-5 space-y-3">
            {severityFilters.filter((item) => item !== 'all').map((severity) => {
              const value = stats?.severity_breakdown?.[severity] ?? 0
              const total = Math.max(stats?.total_findings ?? 1, 1)
              return (
                <div key={severity}>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <Badge value={severity} dot size="xs" />
                    <span className="text-gray-500 font-mono">{value}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-surface-300 overflow-hidden">
                    <div className={clsx('h-full rounded-full', severityColor(severity))} style={{ width: `${(value / total) * 100}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader title="Latest Reports" subtitle="Optimization report history" icon={<Clock className="w-3.5 h-3.5" />} />
          <div className="divide-y divide-white/[0.04]">
            {reports.length ? reports.map((report) => (
              <div key={report.id} className="px-5 py-3 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm text-gray-200 font-medium truncate">{report.report_name}</p>
                  <p className="text-xs text-gray-600 mt-0.5">
                    {report.total_resources_analyzed} resources, {report.total_recommendations} recommendations
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-sm text-emerald-400 font-semibold">{currency(report.estimated_monthly_savings_usd)}/mo</p>
                  <p className="text-xs text-gray-600">{formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}</p>
                </div>
              </div>
            )) : <EmptyState text="No optimization reports yet." />}
          </div>
        </Card>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[220px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600 pointer-events-none" />
          <input
            type="text"
            placeholder="Search recommendations..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="input pl-9 text-xs py-2"
          />
        </div>
        <div className="flex items-center gap-1 bg-surface-200 border border-white/[0.05] rounded-lg p-0.5">
          {severityFilters.map((severity) => (
            <button
              key={severity}
              onClick={() => setSeverityFilter(severity)}
              className={clsx('text-xs px-3 py-1.5 rounded-md font-medium transition-all capitalize', severityFilter === severity ? 'bg-surface-400 text-gray-100' : 'text-gray-500 hover:text-gray-300')}
            >
              {severity}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-600 ml-auto">{filteredRecommendations.length} recommendations</span>
      </div>

      <Card>
        <CardHeader
          title="Recommendations"
          subtitle="Prioritized actions with estimated savings and remediation guidance"
          icon={<TrendingDown className="w-3.5 h-3.5" />}
        />
        {isLoading ? (
          <div className="p-8 text-sm text-gray-500">Loading optimization data...</div>
        ) : filteredRecommendations.length ? (
          <div className="divide-y divide-white/[0.04]">
            {filteredRecommendations.map((rec, index) => (
              <RecommendationRow
                key={rec.id}
                recommendation={rec}
                index={index}
                selected={selected?.id === rec.id}
                onSelect={() => setSelected(selected?.id === rec.id ? null : rec)}
              />
            ))}
          </div>
        ) : (
          <EmptyState text="No recommendations yet. Run demo analysis to populate optimization data." />
        )}
      </Card>

      {selected && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader
              title={selected.title}
              subtitle={`${selected.namespace ?? 'default'}/${selected.workload_name ?? selected.resource_name}`}
              icon={<Bot className="w-3.5 h-3.5 text-sky-400" />}
              actions={
                <div className="flex items-center gap-2">
                  <Badge value={selected.severity} dot />
                  <button onClick={() => setSelected(null)} className="btn-secondary text-xs py-1 px-2">Close</button>
                </div>
              }
            />
            <div className="p-5 grid grid-cols-1 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2 space-y-4">
                <DetailBlock title="Why This Exists" value={selected.ai_explanation ?? selected.description ?? 'No explanation available.'} />
                <DetailBlock title="Expected Impact" value={selected.impact ?? `Estimated savings of ${currency(selected.estimated_monthly_savings_usd ?? 0)} per month.`} />
                <DetailBlock title="Suggested Remediation" value={selected.recommendation ?? 'Review workload utilization and right-size resource requests.'} />
                {selected.remediation_yaml && (
                  <pre className="text-xs text-gray-300 bg-surface-200 border border-white/[0.05] rounded-lg p-3 overflow-x-auto">
                    {selected.remediation_yaml}
                  </pre>
                )}
              </div>
              <div className="space-y-3 text-xs">
                {[
                  ['Type', typeLabels[selected.optimization_type] ?? selected.optimization_type],
                  ['Savings', `${currency(selected.estimated_monthly_savings_usd ?? 0)}/mo`],
                  ['CPU', `${selected.current_cpu_request_millicores ?? '-'}m → ${selected.recommended_cpu_request_millicores ?? '-' }m`],
                  ['Memory', `${selected.current_memory_request_mb ?? '-'}Mi → ${selected.recommended_memory_request_mb ?? '-'}Mi`],
                  ['Replicas', `${selected.current_replicas ?? '-'} → ${selected.recommended_replicas ?? '-'}`],
                  ['Confidence', `${Math.round((selected.confidence_score ?? 0) * 100)}%`],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between border-b border-white/[0.04] pb-2 last:border-0">
                    <span className="text-gray-600">{label}</span>
                    <span className="text-gray-300 font-medium font-mono text-right">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {!!findings.length && (
        <Card>
          <CardHeader title="Optimization Findings" subtitle="Raw resource intelligence signals" icon={<Server className="w-3.5 h-3.5" />} />
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 p-4">
            {findings.slice(0, 9).map((finding) => (
              <div key={finding.id} className="rounded-lg border border-white/[0.05] bg-surface-200 p-4">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <Badge value={finding.severity} dot size="xs" />
                  <span className="text-[10px] text-gray-600 font-mono">{Math.round((finding.confidence_score ?? 0) * 100)}%</span>
                </div>
                <p className="text-sm text-gray-200 font-medium">{finding.title}</p>
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{finding.description}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

function SummaryCard({ label, value, sub, tone }: { label: string; value: string | number; sub: string; tone: string }) {
  return (
    <Card className="p-5">
      <p className={clsx('text-2xl font-bold tabular-nums', tone)}>{value}</p>
      <p className="text-xs text-gray-400 font-medium mt-0.5">{label}</p>
      <p className="text-xs text-gray-600 mt-0.5">{sub}</p>
    </Card>
  )
}

function RecommendationRow({
  recommendation,
  index,
  selected,
  onSelect,
}: {
  recommendation: CostRecommendation
  index: number
  selected: boolean
  onSelect: () => void
}) {
  const Icon = iconFor(recommendation.optimization_type)
  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.025 }}
      onClick={onSelect}
      className={clsx('w-full text-left flex items-start gap-4 px-5 py-4 hover:bg-white/[0.02] transition-colors', selected && 'bg-brand-500/5')}
    >
      <div className="w-9 h-9 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Icon className="w-4 h-4 text-emerald-400" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-3 mb-1">
          <h3 className="text-sm font-medium text-gray-200 leading-snug">{recommendation.title}</h3>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge value={recommendation.severity} dot size="xs" />
            <Badge value={recommendation.status} size="xs" />
          </div>
        </div>
        <p className="text-xs text-gray-500 leading-relaxed mb-2 line-clamp-2">{recommendation.description}</p>
        <div className="flex items-center gap-4 text-xs text-gray-600 flex-wrap">
          <span className="font-mono text-emerald-400 font-semibold">+{currency(recommendation.estimated_monthly_savings_usd ?? 0)}/mo</span>
          <span className="capitalize">{typeLabels[recommendation.optimization_type] ?? recommendation.optimization_type}</span>
          <span className="font-mono">{recommendation.namespace}/{recommendation.workload_name}</span>
        </div>
      </div>
      <ArrowRight className="w-4 h-4 text-gray-600 mt-2 flex-shrink-0" />
    </motion.button>
  )
}

function DetailBlock({ title, value }: { title: string; value: string }) {
  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">{title}</h4>
      <p className="text-sm text-gray-300 leading-relaxed">{value}</p>
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-center">
      <CheckCircle2 className="w-10 h-10 text-emerald-500/25" />
      <p className="text-gray-500 text-sm">{text}</p>
    </div>
  )
}

function iconFor(type: string) {
  if (type.includes('memory')) return HardDrive
  if (type.includes('cpu') || type.includes('right')) return Cpu
  if (type.includes('idle')) return Clock
  return Server
}

function severityColor(severity: string) {
  if (severity === 'critical') return 'bg-red-500'
  if (severity === 'high') return 'bg-orange-500'
  if (severity === 'medium') return 'bg-amber-500'
  return 'bg-sky-500'
}

function currency(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: value >= 1000 ? 0 : 2,
  }).format(value)
}
