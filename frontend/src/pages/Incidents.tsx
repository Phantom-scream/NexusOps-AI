import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle, BrainCircuit } from 'lucide-react'
import StatusBadge from '@/components/StatusBadge'
import StatCard from '@/components/StatCard'
import { incidentsApi, type Incident } from '@/services/incidents'
import { formatDistanceToNow } from 'date-fns'

export default function Incidents() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => incidentsApi.list({ page_size: 50 }),
  })

  const { data: stats } = useQuery({
    queryKey: ['incident-stats'],
    queryFn: () => incidentsApi.stats(),
  })

  const resolveMutation = useMutation({
    mutationFn: (id: string) => incidentsApi.resolve(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['incidents'] }),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-100">Incidents</h1>
        <p className="text-sm text-gray-500 mt-0.5">Incident tracking and AI-powered investigation</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Open" value={stats?.total_open ?? '—'} color="red" />
        <StatCard label="Critical" value={stats?.critical ?? '—'} color="red" />
        <StatCard label="High" value={stats?.high ?? '—'} color="yellow" />
        <StatCard label="Resolved Today" value={stats?.resolved_today ?? '—'} color="green" />
      </div>

      {/* Incidents Table */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-700/50 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-300">All Incidents</h2>
          <span className="text-xs text-gray-500">{data?.total ?? 0} total</span>
        </div>

        {isLoading ? (
          <div className="p-10 text-center text-gray-500">Loading…</div>
        ) : (
          <div className="divide-y divide-gray-700/30">
            {data?.items.map((incident: Incident) => (
              <div key={incident.id} className="px-5 py-4 hover:bg-surface-200/50 transition-colors">
                <div className="flex items-start gap-3">
                  <AlertTriangle
                    className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                      incident.severity === 'critical' ? 'text-red-400' :
                      incident.severity === 'high' ? 'text-orange-400' :
                      'text-yellow-400'
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-gray-100">{incident.title}</p>
                      <StatusBadge value={incident.severity} />
                      <StatusBadge value={incident.status} />
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      <span>{incident.source}</span>
                      {incident.namespace && <span>· {incident.namespace}</span>}
                      {incident.workload && <span>/ {incident.workload}</span>}
                      <span>· {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}</span>
                    </div>
                    {incident.root_cause && (
                      <p className="text-xs text-gray-400 mt-1.5 line-clamp-2">
                        <span className="text-brand-400">Root cause:</span> {incident.root_cause}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    {incident.status !== 'resolved' && incident.status !== 'closed' && (
                      <>
                        <button className="btn-secondary text-xs py-1 px-2.5">
                          <BrainCircuit className="w-3.5 h-3.5" />
                          Investigate
                        </button>
                        <button
                          onClick={() => resolveMutation.mutate(incident.id)}
                          className="btn-secondary text-xs py-1 px-2.5 text-green-400"
                        >
                          <CheckCircle className="w-3.5 h-3.5" />
                          Resolve
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {!data?.items.length && (
              <div className="p-12 text-center text-gray-500">No incidents found</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
