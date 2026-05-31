import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  AlertTriangle,
  CheckCircle2,
  Eye,
  UserCheck,
  ChevronUp,
  ChevronDown,
  Search,
} from 'lucide-react'
import { formatDistanceToNow, format } from 'date-fns'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import StatusDot from '@/components/ui/StatusDot'
import MetricsAreaChart from '@/components/charts/MetricsAreaChart'
import { mockIncidents, generateIncidentTrend } from '@/data/mock'
import type { Incident, Severity, IncidentStatus } from '@/types'
import clsx from 'clsx'

const severityOrder: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }

const statusFilters: Array<{ label: string; value: IncidentStatus | 'all' }> = [
  { label: 'All', value: 'all' },
  { label: 'Open', value: 'open' },
  { label: 'Acknowledged', value: 'acknowledged' },
  { label: 'Investigating', value: 'investigating' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Resolved', value: 'resolved' },
]

const severityFilters: Array<{ label: string; value: Severity | 'all' }> = [
  { label: 'All Severities', value: 'all' },
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
]

type SortField = 'severity' | 'createdAt' | 'title'

export default function Incidents() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<IncidentStatus | 'all'>('all')
  const [severityFilter, setSeverityFilter] = useState<Severity | 'all'>('all')
  const [sortField, setSortField] = useState<SortField>('severity')
  const [sortAsc, setSortAsc] = useState(true)
  const [selected, setSelected] = useState<string | null>(null)
  const trendData = useMemo(() => generateIncidentTrend(24), [])

  const filtered = useMemo(() => {
    let list = mockIncidents.filter(i => {
      if (search && !i.title.toLowerCase().includes(search.toLowerCase()) && !i.affectedService.toLowerCase().includes(search.toLowerCase())) return false
      if (statusFilter !== 'all' && i.status !== statusFilter) return false
      if (severityFilter !== 'all' && i.severity !== severityFilter) return false
      return true
    })
    list = [...list].sort((a, b) => {
      let cmp = 0
      if (sortField === 'severity') cmp = severityOrder[a.severity] - severityOrder[b.severity]
      else if (sortField === 'createdAt') cmp = new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      else cmp = a.title.localeCompare(b.title)
      return sortAsc ? cmp : -cmp
    })
    return list
  }, [search, statusFilter, severityFilter, sortField, sortAsc])

  const counts = {
    open: mockIncidents.filter(i => i.status === 'open').length,
    critical: mockIncidents.filter(i => i.severity === 'critical').length,
    investigating: mockIncidents.filter(i => i.status === 'investigating').length,
    resolved: mockIncidents.filter(i => i.status === 'resolved').length,
  }

  function toggleSort(field: SortField) {
    if (sortField === field) setSortAsc(v => !v)
    else { setSortField(field); setSortAsc(true) }
  }

  function SortIcon({ field }: { field: SortField }) {
    if (sortField !== field) return <ChevronUp className="w-3 h-3 text-gray-700" />
    return sortAsc ? <ChevronUp className="w-3 h-3 text-brand-400" /> : <ChevronDown className="w-3 h-3 text-brand-400" />
  }

  const selectedIncident = selected ? mockIncidents.find(i => i.id === selected) : null

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Incidents"
        subtitle="Unified incident management across all clusters and services"
        breadcrumb={['Home', 'Incidents']}
        actions={
          <button className="btn-primary text-xs py-2 px-4 flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5" /> Create Incident
          </button>
        }
      />

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Open Incidents', value: counts.open, color: 'text-red-400', dot: 'critical' as Severity },
          { label: 'Critical', value: counts.critical, color: 'text-red-500', dot: 'critical' as Severity },
          { label: 'Investigating', value: counts.investigating, color: 'text-amber-400', dot: 'high' as Severity },
          { label: 'Resolved (all time)', value: counts.resolved, color: 'text-emerald-400', dot: 'low' as Severity },
        ].map(({ label, value, color, dot }) => (
          <Card key={label} className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <StatusDot status={dot === 'critical' ? 'critical' : dot === 'high' ? 'degraded' : 'healthy'} size="sm" />
              <span className="text-xs text-gray-500 font-medium">{label}</span>
            </div>
            <p className={clsx('text-3xl font-bold tabular-nums', color)}>{value}</p>
          </Card>
        ))}
      </div>

      {/* Trend chart */}
      <Card>
        <CardHeader title="Incident Trend" subtitle="Last 24 hours" icon={<AlertTriangle className="w-3.5 h-3.5" />} />
        <div className="p-4 pt-2">
          <MetricsAreaChart
            data={trendData}
            series={[
              { key: 'incidents', label: 'Incidents', color: '#f43f5e', gradient: 'g-inc' },
              { key: 'alerts',    label: 'Alerts',    color: '#f59e0b', gradient: 'g-alr' },
            ]}
            height={140}
          />
        </div>
      </Card>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600 pointer-events-none" />
          <input
            type="text"
            placeholder="Search incidents…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input pl-9 text-xs py-2"
          />
        </div>
        <div className="flex items-center gap-1 bg-surface-200 border border-white/[0.05] rounded-lg p-0.5">
          {statusFilters.map(f => (
            <button key={f.value} onClick={() => setStatusFilter(f.value)} className={clsx('text-xs px-3 py-1.5 rounded-md font-medium transition-all', statusFilter === f.value ? 'bg-surface-400 text-gray-100' : 'text-gray-500 hover:text-gray-300')}>{f.label}</button>
          ))}
        </div>
        <div className="flex items-center gap-1 bg-surface-200 border border-white/[0.05] rounded-lg p-0.5">
          {severityFilters.map(f => (
            <button key={f.value} onClick={() => setSeverityFilter(f.value)} className={clsx('text-xs px-3 py-1.5 rounded-md font-medium transition-all', severityFilter === f.value ? 'bg-surface-400 text-gray-100' : 'text-gray-500 hover:text-gray-300')}>{f.label}</button>
          ))}
        </div>
        <span className="text-xs text-gray-600 ml-auto">{filtered.length} incidents</span>
      </div>

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.05]">
                {[
                  { label: 'Severity', field: 'severity' as SortField, w: 'w-24' },
                  { label: 'Title', field: 'title' as SortField, w: '' },
                  { label: 'Service', field: null, w: 'w-36' },
                  { label: 'Cluster', field: null, w: 'w-40' },
                  { label: 'Status', field: null, w: 'w-28' },
                  { label: 'Detected by', field: null, w: 'w-28' },
                  { label: 'Age', field: 'createdAt' as SortField, w: 'w-28' },
                  { label: 'Assignee', field: null, w: 'w-28' },
                  { label: '', field: null, w: 'w-20' },
                ].map(({ label, field, w }) => (
                  <th
                    key={label}
                    className={clsx('text-left text-[10px] text-gray-600 font-medium uppercase tracking-wider px-4 py-3 first:pl-5 last:pr-5', w)}
                    onClick={field ? () => toggleSort(field) : undefined}
                    style={{ cursor: field ? 'pointer' : 'default' }}
                  >
                    <div className="flex items-center gap-1">
                      {label}
                      {field && <SortIcon field={field} />}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {filtered.map((inc) => (
                <motion.tr
                  key={inc.id}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={clsx(
                    'group hover:bg-white/[0.02] transition-colors cursor-pointer',
                    selected === inc.id && 'bg-brand-500/5 border-l-2 border-brand-500',
                  )}
                  onClick={() => setSelected(selected === inc.id ? null : inc.id)}
                >
                  <td className="px-4 py-3 pl-5">
                    <Badge value={inc.severity} dot size="xs" />
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="text-gray-200 font-medium text-xs leading-snug">{inc.title}</p>
                      <p className="text-gray-600 text-[10px] mt-0.5 line-clamp-1">{inc.description}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-400 font-mono">{inc.affectedService}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-500 font-mono">{inc.affectedCluster}</span>
                  </td>
                  <td className="px-4 py-3">
                    <Badge value={inc.status} size="xs" />
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-500">{inc.detectedBy}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-500">{formatDistanceToNow(new Date(inc.createdAt), { addSuffix: false })}</span>
                  </td>
                  <td className="px-4 py-3">
                    {inc.assignee ? (
                      <div className="flex items-center gap-1.5">
                        <div className="w-5 h-5 rounded-full bg-brand-500/30 flex items-center justify-center text-[9px] font-bold text-brand-300">
                          {inc.assignee.split(' ').map(p => p[0]).join('')}
                        </div>
                        <span className="text-xs text-gray-500">{inc.assignee.split(' ')[0]}</span>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-700">Unassigned</span>
                    )}
                  </td>
                  <td className="px-4 py-3 pr-5">
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-1 rounded hover:bg-surface-300 text-gray-500 hover:text-gray-300" title="Acknowledge">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1 rounded hover:bg-surface-300 text-gray-500 hover:text-gray-300" title="Investigate">
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1 rounded hover:bg-surface-300 text-gray-500 hover:text-gray-300" title="Assign">
                        <UserCheck className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <CheckCircle2 className="w-10 h-10 text-emerald-500/30" />
              <p className="text-gray-500 text-sm">No incidents match your filters</p>
            </div>
          )}
        </div>
      </Card>

      {/* Detail panel */}
      {selectedIncident && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader
              title={selectedIncident.title}
              subtitle={`Incident ${selectedIncident.id}`}
              icon={<AlertTriangle className="w-3.5 h-3.5 text-red-400" />}
              actions={
                <div className="flex items-center gap-2">
                  <Badge value={selectedIncident.severity} dot />
                  <Badge value={selectedIncident.status} />
                  <button onClick={() => setSelected(null)} className="btn-secondary text-xs py-1 px-2">Close</button>
                </div>
              }
            />
            <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="md:col-span-2 space-y-4">
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Description</h4>
                  <p className="text-sm text-gray-300 leading-relaxed">{selectedIncident.description}</p>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Root Cause</h4>
                  <p className="text-sm text-gray-300 leading-relaxed">{selectedIncident.rootCause || 'Under investigation…'}</p>
                </div>
                {selectedIncident.resolution && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Resolution</h4>
                    <p className="text-sm text-gray-300 leading-relaxed">{selectedIncident.resolution}</p>
                  </div>
                )}
              </div>
              <div className="space-y-3 text-xs">
                {([
                  ['Cluster', selectedIncident.affectedCluster],
                  ['Service', selectedIncident.affectedService],
                  ['Namespace', selectedIncident.namespace ?? 'production'],
                  ['Detected by', selectedIncident.detectedBy],
                  ['Assignee', selectedIncident.assignee || 'Unassigned'],
                  ['Created', format(new Date(selectedIncident.createdAt), 'MMM d, HH:mm')],
                  selectedIncident.resolvedAt ? ['Resolved', format(new Date(selectedIncident.resolvedAt), 'MMM d, HH:mm')] : null,
                ] as Array<[string, string] | null>).filter((item): item is [string, string] => item !== null).map(([label, value]) => (
                  <div key={label} className="flex justify-between border-b border-white/[0.04] pb-2 last:border-0">
                    <span className="text-gray-600">{label}</span>
                    <span className="text-gray-300 font-medium font-mono">{value}</span>
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
