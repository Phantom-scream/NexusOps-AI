import { useQuery } from '@tanstack/react-query'
import { DollarSign, TrendingDown } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'
import { api } from '@/services/api'
import StatCard from '@/components/StatCard'

export default function CostOptimization() {
  const { data: dashboard } = useQuery({
    queryKey: ['cost-dashboard'],
    queryFn: () => api.get('/cost/dashboard').then((r) => r.data),
  })

  const { data: recommendations, isLoading } = useQuery({
    queryKey: ['cost-recommendations'],
    queryFn: () => api.get('/cost/recommendations').then((r) => r.data),
  })

  const byTypeData = Object.entries(dashboard?.recommendations_by_type ?? {}).map(([type, count]) => ({
    type: type.replace(/_/g, ' '),
    count: Number(count),
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-100">Cost Optimization</h1>
        <p className="text-sm text-gray-500 mt-0.5">AI-powered cloud spend recommendations</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <StatCard
          label="Potential Monthly Savings"
          value={`$${dashboard?.estimated_monthly_savings_usd?.toFixed(0) ?? '—'}`}
          color="green"
          icon={<DollarSign className="w-4 h-4" />}
        />
        <StatCard
          label="Open Recommendations"
          value={dashboard?.total_open_recommendations ?? '—'}
          icon={<TrendingDown className="w-4 h-4" />}
          color="yellow"
        />
        <StatCard
          label="Types Identified"
          value={Object.keys(dashboard?.recommendations_by_type ?? {}).length}
          color="blue"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Chart */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Recommendations by Type</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={byTypeData}>
              <XAxis dataKey="type" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} width={25} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e2535', border: '1px solid #374151', borderRadius: '8px' }}
                cursor={{ fill: 'rgba(99,102,241,0.1)' }}
              />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top opportunities */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Top Opportunities</h2>
          <div className="space-y-2">
            {dashboard?.top_opportunities?.map((op: Record<string, unknown>) => (
              <div key={String(op.id)} className="flex items-center justify-between py-2 border-b border-gray-700/30 last:border-0">
                <div>
                  <p className="text-sm text-gray-200">{String(op.title ?? '')}</p>
                  <p className="text-xs text-gray-500">{String(op.cluster_name ?? '')}</p>
                </div>
                <span className="text-green-400 font-medium text-sm">
                  ${Number(op.estimated_monthly_savings_usd).toFixed(0)}/mo
                </span>
              </div>
            ))}
            {!dashboard?.top_opportunities?.length && (
              <p className="text-sm text-gray-500 text-center py-6">No recommendations yet</p>
            )}
          </div>
        </div>
      </div>

      {/* All recommendations */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-700/50">
          <h2 className="text-sm font-semibold text-gray-300">All Recommendations</h2>
        </div>
        {isLoading ? (
          <div className="p-10 text-center text-gray-500">Loading…</div>
        ) : (
          <div className="divide-y divide-gray-700/30">
            {recommendations?.items?.map((rec: Record<string, unknown>) => (
              <div key={String(rec.id)} className="px-5 py-4 hover:bg-surface-200/50">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-100">{String(rec.title ?? '')}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {String(rec.cluster_name ?? '')} · {String(rec.namespace ?? '')} · {String(rec.workload_name ?? '')}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-green-400 font-semibold text-sm">
                      ${Number(rec.estimated_monthly_savings_usd).toFixed(0)}/mo
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 capitalize">{String(rec.optimization_type ?? '').replace(/_/g, ' ')}</p>
                  </div>
                </div>
              </div>
            ))}
            {!recommendations?.items?.length && (
              <div className="p-12 text-center text-gray-500">No recommendations found</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
