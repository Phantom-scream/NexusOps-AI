import { useQuery } from '@tanstack/react-query'
import { Server, AlertTriangle, Shield, DollarSign, Activity, Zap } from 'lucide-react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts'
import StatCard from '@/components/StatCard'
import StatusBadge from '@/components/StatusBadge'
import { clustersApi } from '@/services/clusters'
import { incidentsApi } from '@/services/incidents'

const mockTrendData = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  incidents: Math.floor(Math.random() * 8),
  alerts: Math.floor(Math.random() * 15),
}))

export default function Dashboard() {
  const { data: clusters } = useQuery({
    queryKey: ['clusters'],
    queryFn: () => clustersApi.list({ page_size: 100 }),
  })

  const { data: incidentStats } = useQuery({
    queryKey: ['incident-stats'],
    queryFn: () => incidentsApi.stats(),
  })

  const { data: recentIncidents } = useQuery({
    queryKey: ['recent-incidents'],
    queryFn: () => incidentsApi.list({ page_size: 8, status: 'open' }),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-100">Operations Overview</h1>
        <p className="text-sm text-gray-500 mt-0.5">Real-time infrastructure intelligence dashboard</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          label="Total Clusters"
          value={clusters?.total ?? '—'}
          icon={<Server className="w-4 h-4" />}
          color="purple"
        />
        <StatCard
          label="Open Incidents"
          value={incidentStats?.total_open ?? '—'}
          icon={<AlertTriangle className="w-4 h-4" />}
          color={incidentStats && incidentStats.total_open > 0 ? 'red' : 'green'}
        />
        <StatCard
          label="Critical"
          value={incidentStats?.critical ?? '—'}
          icon={<Zap className="w-4 h-4" />}
          color="red"
        />
        <StatCard
          label="Security Findings"
          value="—"
          icon={<Shield className="w-4 h-4" />}
          color="yellow"
        />
        <StatCard
          label="Est. Monthly Savings"
          value="$—"
          icon={<DollarSign className="w-4 h-4" />}
          color="green"
        />
        <StatCard
          label="Avg Resolution"
          value={incidentStats ? `${incidentStats.avg_resolution_hours.toFixed(1)}h` : '—'}
          icon={<Activity className="w-4 h-4" />}
          color="blue"
        />
      </div>

      {/* Charts + Recent Incidents */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Incident trend */}
        <div className="xl:col-span-2 card p-5">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Incident Activity (24h)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={mockTrendData}>
              <defs>
                <linearGradient id="colorIncidents" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorAlerts" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="hour" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} interval={3} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} width={25} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e2535', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Area type="monotone" dataKey="incidents" stroke="#ef4444" fill="url(#colorIncidents)" strokeWidth={1.5} dot={false} name="Incidents" />
              <Area type="monotone" dataKey="alerts" stroke="#6366f1" fill="url(#colorAlerts)" strokeWidth={1.5} dot={false} name="Alerts" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Cluster status */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Cluster Status</h2>
          <div className="space-y-2">
            {clusters?.items?.slice(0, 8).map((cluster) => (
              <div key={cluster.id} className="flex items-center justify-between py-1.5 border-b border-gray-700/30 last:border-0">
                <div>
                  <p className="text-sm text-gray-200">{cluster.display_name || cluster.name}</p>
                  <p className="text-xs text-gray-500">{cluster.provider} · {cluster.node_count} nodes</p>
                </div>
                <StatusBadge value={cluster.status} />
              </div>
            ))}
            {!clusters?.items?.length && (
              <p className="text-sm text-gray-500 text-center py-6">No clusters registered</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent open incidents */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-gray-300 mb-4">Open Incidents</h2>
        {recentIncidents?.items?.length ? (
          <div className="divide-y divide-gray-700/30">
            {recentIncidents.items.map((inc) => (
              <div key={inc.id} className="flex items-center gap-4 py-3">
                <StatusBadge value={inc.severity} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200 truncate">{inc.title}</p>
                  <p className="text-xs text-gray-500">{inc.namespace ?? 'cluster-wide'} · {inc.source}</p>
                </div>
                <StatusBadge value={inc.status} />
                <span className="text-xs text-gray-500 flex-shrink-0">
                  {new Date(inc.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 text-center py-8">No open incidents</p>
        )}
      </div>
    </div>
  )
}
