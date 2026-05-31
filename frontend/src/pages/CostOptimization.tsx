import { useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  DollarSign,
  TrendingDown,
  CheckCircle2,
  Clock,
  Server,
  Network,
  HardDrive,
  ArrowRight,
} from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import MetricsBarChart from '@/components/charts/MetricsBarChart'
import DonutChart from '@/components/charts/DonutChart'
import { mockCostRecs, generateCostTrend } from '@/data/mock'
import type { CostCategory } from '@/types'
import clsx from 'clsx'

const categoryIcon: Record<CostCategory, React.ElementType> = {
  rightsizing: Server,
  reserved: DollarSign,
  idle: Clock,
  storage: HardDrive,
  network: Network,
}

const categoryColor: Record<CostCategory, string> = {
  rightsizing: '#6366f1',
  reserved: '#10b981',
  idle: '#f59e0b',
  storage: '#38bdf8',
  network: '#a78bfa',
}

const effortColors: Record<string, string> = {
  low: 'text-emerald-400 bg-emerald-500/10',
  medium: 'text-amber-400 bg-amber-500/10',
  high: 'text-red-400 bg-red-500/10',
}

export default function CostOptimization() {
  const costTrend = useMemo(() => generateCostTrend(6), [])

  const totalSavings = mockCostRecs.filter(r => r.status !== 'dismissed').reduce((s, r) => s + r.monthlySavings, 0)
  const implemented = mockCostRecs.filter(r => r.status === 'implemented').length
  const pending = mockCostRecs.filter(r => r.status === 'pending').length
  const inProgress = mockCostRecs.filter(r => r.status === 'implementing').length

  const byCategoryData = Object.entries(
    mockCostRecs.reduce((acc, r) => {
      if (r.status !== 'dismissed') {
        acc[r.category] = (acc[r.category] ?? 0) + r.monthlySavings
      }
      return acc
    }, {} as Record<string, number>)
  ).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: Math.round(value),
    color: categoryColor[name as CostCategory] ?? '#6b7280',
  }))

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Cost Optimization"
        subtitle="Cloud spend analysis, waste elimination, and savings recommendations"
        breadcrumb={['Home', 'Cost Optimization']}
        actions={
          <button className="btn-primary text-xs py-2 px-4 flex items-center gap-2">
            <TrendingDown className="w-3.5 h-3.5" /> Analyze Costs
          </button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Est. Monthly Savings', value: `$${(totalSavings / 1000).toFixed(1)}k`, sub: `from ${mockCostRecs.filter(r => r.status !== 'dismissed').length} recommendations`, color: 'text-emerald-400' },
          { label: 'Implemented', value: implemented, sub: 'recommendations applied', color: 'text-sky-400' },
          { label: 'In Progress', value: inProgress, sub: 'being applied now', color: 'text-amber-400' },
          { label: 'Pending', value: pending, sub: 'awaiting action', color: 'text-gray-400' },
        ].map(({ label, value, sub, color }) => (
          <Card key={label} className="p-5">
            <p className={clsx('text-2xl font-bold tabular-nums', color)}>{value}</p>
            <p className="text-xs text-gray-400 font-medium mt-0.5">{label}</p>
            <p className="text-xs text-gray-600 mt-0.5">{sub}</p>
          </Card>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card className="xl:col-span-2">
          <CardHeader
            title="Cost Trend"
            subtitle="Actual vs Optimized spend (6 months)"
            icon={<DollarSign className="w-3.5 h-3.5" />}
            actions={
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 text-xs text-gray-500"><span className="w-3 h-0.5 rounded bg-red-400" />Actual</div>
                <div className="flex items-center gap-1.5 text-xs text-gray-500"><span className="w-3 h-0.5 rounded bg-emerald-400" />Optimized</div>
              </div>
            }
          />
          <div className="p-4 pt-2">
            <MetricsBarChart
              data={costTrend}
              bars={[
                { key: 'actual', label: 'Actual ($k)', color: '#f43f5e' },
                { key: 'optimized', label: 'Optimized ($k)', color: '#10b981' },
              ]}
              height={200}
            />
          </div>
        </Card>

        <Card>
          <CardHeader title="Savings by Category" icon={<DollarSign className="w-3.5 h-3.5" />} />
          <div className="p-5 flex items-center justify-center">
            <DonutChart
              data={byCategoryData}
              size={160}
              innerRadius={52}
              outerRadius={72}
              centerValue={`$${(totalSavings / 1000).toFixed(0)}k`}
              centerLabel="savings"
              showLegend
            />
          </div>
        </Card>
      </div>

      {/* Recommendations list */}
      <Card>
        <CardHeader
          title="Recommendations"
          subtitle={`${pending + inProgress} actionable items`}
          icon={<TrendingDown className="w-3.5 h-3.5" />}
        />
        <div className="divide-y divide-white/[0.04]">
          {mockCostRecs.map((rec, idx) => {
            const Icon = categoryIcon[rec.category]
            return (
              <motion.div
                key={rec.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.04 }}
                className={clsx(
                  'flex items-start gap-4 px-5 py-4 hover:bg-white/[0.02] transition-colors',
                  rec.status === 'dismissed' && 'opacity-40',
                )}
              >
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                  style={{ backgroundColor: `${categoryColor[rec.category]}15` }}
                >
                  <Icon className="w-4 h-4" style={{ color: categoryColor[rec.category] }} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3 mb-1">
                    <h3 className="text-sm font-medium text-gray-200 leading-snug">{rec.title}</h3>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={clsx('text-[10px] font-medium px-2 py-0.5 rounded-full uppercase tracking-wide', effortColors[rec.effort])}>
                        {rec.effort} effort
                      </span>
                      <Badge value={rec.status} size="xs" />
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed mb-2">{rec.description}</p>
                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span className="font-mono text-emerald-400 font-semibold">+${rec.monthlySavings.toLocaleString()}/mo</span>
                    <span className="capitalize text-gray-600">{rec.category}</span>
                    <span className="font-mono">{rec.resource}</span>
                  </div>
                </div>

                {rec.status === 'pending' && (
                  <button className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 flex-shrink-0">
                    Apply <ArrowRight className="w-3 h-3" />
                  </button>
                )}
                {rec.status === 'implementing' && (
                  <div className="flex items-center gap-1.5 text-xs text-amber-400 flex-shrink-0">
                    <Clock className="w-3 h-3" /> Applying
                  </div>
                )}
                {rec.status === 'implemented' && (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400 flex-shrink-0">
                    <CheckCircle2 className="w-3 h-3" /> Done
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}
