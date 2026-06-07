import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  GitBranch,
  Layers3,
  RefreshCw,
  Search,
  Shield,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import DonutChart from '@/components/charts/DonutChart'
import { terraformApi, type TerraformDrift, type TerraformFinding } from '@/services/terraform'

const severityFilters = ['all', 'critical', 'high', 'medium', 'low']
const categoryFilters = ['all', 'iam', 'network', 'encryption', 'secrets', 'kubernetes', 'rbac', 'policy', 'compliance']

const categoryColors: Record<string, string> = {
  iam: '#f97316',
  network: '#38bdf8',
  encryption: '#10b981',
  secrets: '#a78bfa',
  kubernetes: '#6366f1',
  rbac: '#f59e0b',
  policy: '#ef4444',
  compliance: '#14b8a6',
  drift: '#eab308',
}

export default function Security() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [selectedFinding, setSelectedFinding] = useState<TerraformFinding | null>(null)

  const statsQuery = useQuery({ queryKey: ['terraform', 'stats'], queryFn: terraformApi.stats })
  const findingsQuery = useQuery({
    queryKey: ['terraform', 'findings', severityFilter, categoryFilter],
    queryFn: () => terraformApi.findings({
      page_size: 100,
      severity: severityFilter === 'all' ? undefined : severityFilter,
      category: categoryFilter === 'all' ? undefined : categoryFilter,
    }),
  })
  const driftQuery = useQuery({
    queryKey: ['terraform', 'drift'],
    queryFn: () => terraformApi.drift({ page_size: 50, status: 'open' }),
  })
  const scansQuery = useQuery({ queryKey: ['terraform', 'scans'], queryFn: terraformApi.scans })

  const demoMutation = useMutation({
    mutationFn: () => terraformApi.analyze({ demo: true, scan_name: 'Demo Terraform security and drift analysis' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['terraform'] })
    },
  })

  const findings = findingsQuery.data?.items ?? []
  const drift = driftQuery.data?.items ?? []
  const stats = statsQuery.data
  const latestScan = scansQuery.data?.[0]

  const filteredFindings = useMemo(() => {
    const needle = search.trim().toLowerCase()
    if (!needle) return findings
    return findings.filter((finding) =>
      [finding.title, finding.description, finding.rule_id, finding.resource_address, finding.file_path]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle)),
    )
  }, [findings, search])

  const categoryData = Object.entries(stats?.category_breakdown ?? {})
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({
      name,
      value,
      color: categoryColors[name] ?? '#6b7280',
    }))

  const isLoading = statsQuery.isLoading || findingsQuery.isLoading || driftQuery.isLoading

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Terraform Security & Drift"
        subtitle="IaC posture, OPA policy evaluation, AI explanations, and desired-vs-actual drift"
        breadcrumb={['Home', 'Security']}
        actions={
          <button
            onClick={() => demoMutation.mutate()}
            disabled={demoMutation.isPending}
            className="btn-primary text-xs py-2 px-4 flex items-center gap-2 disabled:opacity-60"
          >
            <RefreshCw className={clsx('w-3.5 h-3.5', demoMutation.isPending && 'animate-spin')} />
            {demoMutation.isPending ? 'Analyzing Demo' : 'Run Demo Analysis'}
          </button>
        }
      />

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <SummaryCard label="Open Findings" value={stats?.open_findings ?? 0} sub="Terraform risks" tone="text-red-400" />
        <SummaryCard label="Critical / High" value={`${stats?.critical_findings ?? 0}/${stats?.high_findings ?? 0}`} sub="priority queue" tone="text-orange-400" />
        <SummaryCard label="Drift Records" value={stats?.drift_count ?? 0} sub="desired vs actual" tone="text-amber-400" />
        <SummaryCard label="Workspaces" value={stats?.total_workspaces ?? 0} sub={`${stats?.total_resources ?? 0} resources`} tone="text-sky-400" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card>
          <CardHeader title="Severity Breakdown" icon={<Shield className="w-3.5 h-3.5" />} />
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

        <Card>
          <CardHeader title="Finding Categories" icon={<Layers3 className="w-3.5 h-3.5" />} />
          <div className="p-5 flex items-center justify-center">
            <DonutChart
              data={categoryData}
              size={160}
              innerRadius={52}
              outerRadius={72}
              centerValue={stats?.total_findings ?? 0}
              centerLabel="findings"
              showLegend
            />
          </div>
        </Card>

        <Card>
          <CardHeader title="Latest Scan" icon={<GitBranch className="w-3.5 h-3.5" />} />
          <div className="p-5 space-y-4">
            {latestScan ? (
              <>
                <div>
                  <p className="text-sm text-gray-200 font-medium">{latestScan.scan_name}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatDistanceToNow(new Date(latestScan.created_at), { addSuffix: true })}
                  </p>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <MiniMetric label="Findings" value={latestScan.findings_count} />
                  <MiniMetric label="Policy" value={latestScan.policy_violation_count} />
                  <MiniMetric label="Drift" value={latestScan.drift_count} />
                </div>
                <p className="text-xs text-gray-500 leading-relaxed">{latestScan.ai_summary}</p>
              </>
            ) : (
              <EmptyState text="Run the demo analysis to seed Terraform security data." />
            )}
          </div>
        </Card>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[220px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600 pointer-events-none" />
          <input
            type="text"
            placeholder="Search findings, rules, resources..."
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
        <select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)} className="input text-xs py-2 pr-8">
          {categoryFilters.map((category) => <option key={category} value={category}>{category}</option>)}
        </select>
        <span className="text-xs text-gray-600 ml-auto">{filteredFindings.length} findings</span>
      </div>

      <Card>
        <CardHeader title="Security Findings" subtitle="OPA, static analysis, and AI-enriched remediation" icon={<AlertTriangle className="w-3.5 h-3.5" />} />
        {isLoading ? (
          <div className="p-8 text-sm text-gray-500">Loading Terraform findings...</div>
        ) : filteredFindings.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/[0.05]">
                  {['Severity', 'Rule', 'Finding', 'Category', 'Resource', 'Scanner', 'Confidence', 'Found'].map((header) => (
                    <th key={header} className="text-left text-[10px] text-gray-600 font-medium uppercase tracking-wider px-4 py-3 first:pl-5">{header}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredFindings.map((finding) => (
                  <motion.tr
                    key={finding.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className={clsx('hover:bg-white/[0.02] transition-colors cursor-pointer', selectedFinding?.id === finding.id && 'bg-brand-500/5')}
                    onClick={() => setSelectedFinding(selectedFinding?.id === finding.id ? null : finding)}
                  >
                    <td className="px-4 py-3 pl-5"><Badge value={finding.severity} dot size="xs" /></td>
                    <td className="px-4 py-3"><span className="text-[10px] font-mono text-sky-400">{finding.rule_id ?? 'policy'}</span></td>
                    <td className="px-4 py-3 max-w-md">
                      <p className="text-xs text-gray-200 font-medium leading-snug">{finding.title}</p>
                      <p className="text-[11px] text-gray-600 mt-0.5 line-clamp-1">{finding.description}</p>
                    </td>
                    <td className="px-4 py-3"><span className="text-xs text-gray-500 capitalize">{finding.category}</span></td>
                    <td className="px-4 py-3"><span className="text-xs text-gray-500 font-mono">{finding.resource_address ?? finding.file_path ?? 'workspace'}</span></td>
                    <td className="px-4 py-3"><span className="text-xs text-gray-600">{finding.scanner}</span></td>
                    <td className="px-4 py-3"><span className="text-xs text-gray-500 font-mono">{Math.round((finding.confidence_score ?? 0) * 100)}%</span></td>
                    <td className="px-4 py-3"><span className="text-xs text-gray-600">{formatDistanceToNow(new Date(finding.created_at), { addSuffix: true })}</span></td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState text="No Terraform findings yet. Run the demo analysis to populate this dashboard." />
        )}
      </Card>

      <Card>
        <CardHeader title="Drift Dashboard" subtitle="Desired Terraform state compared with ingested actual state" icon={<GitBranch className="w-3.5 h-3.5" />} />
        {drift.length ? (
          <div className="divide-y divide-white/[0.04]">
            {drift.map((item) => <DriftRow key={item.id} item={item} />)}
          </div>
        ) : (
          <EmptyState text="No drift records found for the current Terraform workspaces." />
        )}
      </Card>

      {selectedFinding && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader
              title={selectedFinding.title}
              subtitle={selectedFinding.rule_id ?? selectedFinding.id}
              icon={<Bot className="w-3.5 h-3.5 text-sky-400" />}
              actions={
                <div className="flex items-center gap-2">
                  <Badge value={selectedFinding.severity} dot />
                  <button onClick={() => setSelectedFinding(null)} className="btn-secondary text-xs py-1 px-2">Close</button>
                </div>
              }
            />
            <div className="p-5 grid grid-cols-1 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2 space-y-4">
                <DetailBlock title="Description" value={selectedFinding.description} />
                <DetailBlock title="Impact" value={selectedFinding.impact ?? 'Impact not provided.'} />
                <DetailBlock title="AI Explanation" value={selectedFinding.ai_explanation ?? 'No AI explanation available.'} />
                <DetailBlock title="Remediation" value={selectedFinding.remediation ?? 'Review and remediate according to the rule guidance.'} />
              </div>
              <div className="space-y-3 text-xs">
                {[
                  ['Category', selectedFinding.category],
                  ['Scanner', selectedFinding.scanner],
                  ['Resource', selectedFinding.resource_address ?? 'workspace'],
                  ['File', selectedFinding.file_path ?? '-'],
                  ['Line', selectedFinding.line_number?.toString() ?? '-'],
                  ['Confidence', `${Math.round((selectedFinding.confidence_score ?? 0) * 100)}%`],
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

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-surface-200 border border-white/[0.05] p-3">
      <p className="text-lg font-semibold text-gray-100 tabular-nums">{value}</p>
      <p className="text-[10px] text-gray-600 uppercase tracking-wide">{label}</p>
    </div>
  )
}

function DriftRow({ item }: { item: TerraformDrift }) {
  return (
    <div className="px-5 py-4 flex items-start gap-4">
      <GitBranch className="w-4 h-4 text-amber-400 mt-1 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <Badge value={item.severity} dot size="xs" />
          <span className="text-xs text-gray-500 font-mono">{item.resource_address}</span>
        </div>
        <p className="text-sm text-gray-200">{item.description}</p>
        <p className="text-xs text-gray-600 mt-1">
          {item.attribute_path}: desired <code>{JSON.stringify(item.desired_value)}</code>, actual <code>{JSON.stringify(item.actual_value)}</code>
        </p>
      </div>
      <Badge value={item.status} size="xs" />
    </div>
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
    <div className="flex flex-col items-center gap-3 py-14 text-center">
      <CheckCircle2 className="w-10 h-10 text-emerald-500/25" />
      <p className="text-gray-500 text-sm">{text}</p>
    </div>
  )
}

function severityColor(severity: string) {
  if (severity === 'critical') return 'bg-red-500'
  if (severity === 'high') return 'bg-orange-500'
  if (severity === 'medium') return 'bg-amber-500'
  return 'bg-sky-500'
}
