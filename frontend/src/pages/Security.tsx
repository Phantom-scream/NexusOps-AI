import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  AlertTriangle,
  Search,
  Eye,
  CheckCircle2,
  Clock,
  ExternalLink,
  ScanLine,
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import DonutChart from '@/components/charts/DonutChart'
import { mockFindings, mockSummary } from '@/data/mock'
import type { Severity, FindingCategory, FindingStatus } from '@/types'
import clsx from 'clsx'

const severityFilters: Array<{ label: string; value: Severity | 'all' }> = [
  { label: 'All', value: 'all' },
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
]

const categoryFilters: Array<{ label: string; value: FindingCategory | 'all' }> = [
  { label: 'All Categories', value: 'all' },
  { label: 'Vulnerability', value: 'vulnerability' },
  { label: 'Misconfiguration', value: 'misconfig' },
  { label: 'Policy Violation', value: 'policy' },
  { label: 'Secret Exposure', value: 'secret' },
  { label: 'Network', value: 'network' },
]

const statusFilters: Array<{ label: string; value: FindingStatus | 'all' }> = [
  { label: 'All Status', value: 'all' },
  { label: 'Open', value: 'open' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Suppressed', value: 'suppressed' },
]

const categoryColors: Record<string, string> = {
  vulnerability: '#f43f5e',
  misconfig: '#f97316',
  policy: '#f59e0b',
  secret: '#a78bfa',
  network: '#38bdf8',
}

const categoryLabel: Record<string, string> = {
  vulnerability: 'Vulnerability',
  misconfig: 'Misconfiguration',
  policy: 'Policy Violation',
  secret: 'Secret Exposure',
  network: 'Network Exposure',
}

export default function Security() {
  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState<Severity | 'all'>('all')
  const [categoryFilter, setCategoryFilter] = useState<FindingCategory | 'all'>('all')
  const [statusFilter, setStatusFilter] = useState<FindingStatus | 'all'>('open')
  const [selected, setSelected] = useState<string | null>(null)

  const filtered = useMemo(() =>
    mockFindings.filter(f => {
      if (search && !f.title.toLowerCase().includes(search.toLowerCase()) && !(f.cveId ?? '').toLowerCase().includes(search.toLowerCase())) return false
      if (severityFilter !== 'all' && f.severity !== severityFilter) return false
      if (categoryFilter !== 'all' && f.category !== categoryFilter) return false
      if (statusFilter !== 'all' && f.status !== statusFilter) return false
      return true
    }), [search, severityFilter, categoryFilter, statusFilter])

  const counts = {
    critical: mockFindings.filter(f => f.severity === 'critical').length,
    high: mockFindings.filter(f => f.severity === 'high').length,
    medium: mockFindings.filter(f => f.severity === 'medium').length,
    low: mockFindings.filter(f => f.severity === 'low').length,
  }

  const byCategoryData = Object.entries(
    mockFindings.reduce((acc, f) => {
      acc[f.category] = (acc[f.category] ?? 0) + 1
      return acc
    }, {} as Record<string, number>)
  ).map(([name, value]) => ({ name: categoryLabel[name] ?? name, value, color: categoryColors[name] ?? '#6b7280' }))

  const selectedFinding = selected ? mockFindings.find(f => f.id === selected) : null

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Security"
        subtitle="Continuous security scanning, vulnerability management, and compliance"
        breadcrumb={['Home', 'Security']}
        actions={
          <button className="btn-primary text-xs py-2 px-4 flex items-center gap-2">
            <ScanLine className="w-3.5 h-3.5" /> Run Scan
          </button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Critical', value: counts.critical, color: 'text-red-500', bg: 'bg-red-500/10' },
          { label: 'High', value: counts.high, color: 'text-orange-400', bg: 'bg-orange-500/10' },
          { label: 'Medium', value: counts.medium, color: 'text-amber-400', bg: 'bg-amber-500/10' },
          { label: 'Low', value: counts.low, color: 'text-sky-400', bg: 'bg-sky-500/10' },
        ].map(({ label, value, color, bg }) => (
          <Card key={label} className={clsx('p-5', bg, 'border border-white/[0.05]')}>
            <p className={clsx('text-3xl font-bold tabular-nums', color)}>{value}</p>
            <p className="text-xs text-gray-400 font-medium mt-1">{label} severity</p>
          </Card>
        ))}
      </div>

      {/* Chart + summary */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card className="xl:col-span-1">
          <CardHeader title="Findings by Category" icon={<Shield className="w-3.5 h-3.5" />} />
          <div className="p-5 flex items-center justify-center">
            <DonutChart
              data={byCategoryData}
              size={160}
              innerRadius={52}
              outerRadius={72}
              centerValue={mockFindings.length}
              centerLabel="findings"
              showLegend
            />
          </div>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader title="CVSS Score Distribution" subtitle="Open findings" icon={<AlertTriangle className="w-3.5 h-3.5" />} />
          <div className="p-5">
            <div className="space-y-3">
              {mockFindings.filter(f => f.status === 'open' || f.status === 'in_progress').slice(0, 6).map(f => (
                <div key={f.id} className="flex items-center gap-3">
                  <Badge value={f.severity} dot size="xs" className="flex-shrink-0 w-20" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-xs text-gray-300 truncate">{f.title}</p>
                      {f.cvssScore && <span className="text-xs font-mono text-gray-400 ml-2 flex-shrink-0">{f.cvssScore.toFixed(1)}</span>}
                    </div>
                    <div className="h-1 bg-surface-300 rounded-full overflow-hidden">
                      <div
                        className={clsx('h-full rounded-full', f.severity === 'critical' ? 'bg-red-500' : f.severity === 'high' ? 'bg-orange-500' : f.severity === 'medium' ? 'bg-amber-500' : 'bg-sky-500')}
                        style={{ width: `${((f.cvssScore ?? 5) / 10) * 100}%` }}
                      />
                    </div>
                  </div>
                  {f.cveId && (
                    <span className="text-[10px] font-mono text-gray-600 flex-shrink-0">{f.cveId}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600 pointer-events-none" />
          <input type="text" placeholder="Search findings…" value={search} onChange={e => setSearch(e.target.value)} className="input pl-9 text-xs py-2" />
        </div>
        <div className="flex items-center gap-1 bg-surface-200 border border-white/[0.05] rounded-lg p-0.5">
          {severityFilters.map(f => (
            <button key={f.value} onClick={() => setSeverityFilter(f.value)} className={clsx('text-xs px-3 py-1.5 rounded-md font-medium transition-all', severityFilter === f.value ? 'bg-surface-400 text-gray-100' : 'text-gray-500 hover:text-gray-300')}>{f.label}</button>
          ))}
        </div>
        <select
          value={categoryFilter}
          onChange={e => setCategoryFilter(e.target.value as FindingCategory | 'all')}
          className="input text-xs py-2 pr-8"
        >
          {categoryFilters.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value as FindingStatus | 'all')}
          className="input text-xs py-2 pr-8"
        >
          {statusFilters.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        <span className="text-xs text-gray-600 ml-auto">{filtered.length} findings</span>
      </div>

      {/* Findings table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.05]">
                {['Severity', 'Title', 'Category', 'CVE ID', 'CVSS', 'Resource', 'Cluster', 'Status', 'Found', ''].map(h => (
                  <th key={h} className="text-left text-[10px] text-gray-600 font-medium uppercase tracking-wider px-4 py-3 first:pl-5 last:pr-5">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {filtered.map(f => (
                <motion.tr
                  key={f.id}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={clsx('group hover:bg-white/[0.02] transition-colors cursor-pointer', selected === f.id && 'bg-brand-500/5')}
                  onClick={() => setSelected(selected === f.id ? null : f.id)}
                >
                  <td className="px-4 py-3 pl-5"><Badge value={f.severity} dot size="xs" /></td>
                  <td className="px-4 py-3 max-w-xs">
                    <p className="text-xs text-gray-200 font-medium leading-snug line-clamp-2">{f.title}</p>
                  </td>
                  <td className="px-4 py-3"><span className="text-xs text-gray-500">{categoryLabel[f.category] ?? f.category}</span></td>
                  <td className="px-4 py-3"><span className="text-[10px] font-mono text-sky-400">{f.cveId ?? '—'}</span></td>
                  <td className="px-4 py-3"><span className={clsx('text-xs font-mono font-semibold', (f.cvssScore ?? 0) >= 9 ? 'text-red-400' : (f.cvssScore ?? 0) >= 7 ? 'text-orange-400' : 'text-amber-400')}>{f.cvssScore?.toFixed(1) ?? '—'}</span></td>
                  <td className="px-4 py-3"><span className="text-xs text-gray-500 font-mono">{f.resource}</span></td>
                  <td className="px-4 py-3"><span className="text-xs text-gray-600 font-mono">{f.cluster}</span></td>
                  <td className="px-4 py-3"><Badge value={f.status} size="xs" /></td>
                  <td className="px-4 py-3"><span className="text-xs text-gray-600">{formatDistanceToNow(new Date(f.createdAt), { addSuffix: true })}</span></td>
                  <td className="px-4 py-3 pr-5">
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100">
                      <button className="p-1 rounded hover:bg-surface-300 text-gray-500 hover:text-gray-300" title="View details">
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1 rounded hover:bg-surface-300 text-gray-500 hover:text-gray-300" title="External link">
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <Shield className="w-10 h-10 text-emerald-500/30" />
              <p className="text-gray-500 text-sm">No findings match your filters</p>
            </div>
          )}
        </div>
      </Card>

      {/* Detail panel */}
      {selectedFinding && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader
              title={selectedFinding.title}
              subtitle={selectedFinding.cveId ?? `Finding ${selectedFinding.id}`}
              icon={<Shield className="w-3.5 h-3.5 text-amber-400" />}
              actions={
                <div className="flex items-center gap-2">
                  <Badge value={selectedFinding.severity} dot />
                  <Badge value={selectedFinding.status} />
                  <button onClick={() => setSelected(null)} className="btn-secondary text-xs py-1 px-2">Close</button>
                </div>
              }
            />
            <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="md:col-span-2 space-y-4">
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Description</h4>
                  <p className="text-sm text-gray-300 leading-relaxed">{selectedFinding.description}</p>
                </div>
                {selectedFinding.remediationAvailable && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Remediation</h4>
                    <p className="text-sm text-gray-300 leading-relaxed">Automated remediation is available for this finding. Click &ldquo;Apply Fix&rdquo; to start the remediation workflow.</p>
                  </div>
                )}
              </div>
              <div className="space-y-3 text-xs">
                {[
                  ['Category', categoryLabel[selectedFinding.category]],
                  ['CVE ID', selectedFinding.cveId ?? '—'],
                  ['CVSS Score', selectedFinding.cvssScore?.toFixed(1) ?? '—'],
                  ['Affected Resource', selectedFinding.resource],
                  ['Cluster', selectedFinding.cluster],
                  ['Discovered', format(new Date(selectedFinding.createdAt), 'MMM d, yyyy HH:mm')],
                ].map(([label, value]) => (
                  <div key={label as string} className="flex justify-between border-b border-white/[0.04] pb-2 last:border-0">
                    <span className="text-gray-600">{label as string}</span>
                    <span className="text-gray-300 font-medium font-mono">{value as string}</span>
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
