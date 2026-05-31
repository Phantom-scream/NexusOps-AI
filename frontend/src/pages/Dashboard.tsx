import { useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Server,
  AlertTriangle,
  Shield,
  DollarSign,
  Activity,
  Zap,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  Clock,
  ArrowRight,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import StatusDot from '@/components/ui/StatusDot'
import ProgressBar from '@/components/ui/ProgressBar'
import MiniSparkline from '@/components/charts/MiniSparkline'
import MetricsAreaChart from '@/components/charts/MetricsAreaChart'
import DonutChart from '@/components/charts/DonutChart'
import {
  mockClusters,
  mockIncidents,
  mockServiceHealth,
  mockSummary,
  generateIncidentTrend,
  generateMultiSeries,
} from '@/data/mock'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

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
  icon: React.ElementType
  iconColor: string
  trend?: { value: number; up: boolean }
  sparkline?: number[]
  sparkColor?: string
  onClick?: () => void
}

function StatCard({ label, value, subtext, icon: Icon, iconColor, trend, sparkline, sparkColor, onClick }: StatCardProps) {
  return (
    <motion.div variants={stagger.item}>
      <Card
        hover={!!onClick}
        className="p-5 group"
        onClick={onClick}
      >
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
        <div className="space-y-0.5">
          <p className="text-2xl font-bold text-gray-50 tabular-nums">{value}</p>
          <p className="text-xs text-gray-500 font-medium">{label}</p>
          {(trend || subtext) && (
            <div className="flex items-center gap-1.5 mt-2">
              {trend && (
                <span className={clsx('flex items-center gap-0.5 text-xs font-medium', trend.up ? 'text-red-400' : 'text-emerald-400')}>
                  {trend.up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  {trend.value}%
                </span>
              )}
              {subtext && <span className="text-xs text-gray-600">{subtext}</span>}
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const incidentTrend = useMemo(() => generateIncidentTrend(24), [])
  const multiSeries = useMemo(() => generateMultiSeries(24), [])

  const openIncidents = mockIncidents.filter(i => i.status !== 'resolved')
  const criticalClusters = mockClusters.filter(c => c.status === 'degraded' || c.status === 'critical')

  const findingsByCategory = [
    { name: 'Vulnerability', value: 3, color: '#f43f5e' },
    { name: 'Misconfig',     value: 4, color: '#f97316' },
    { name: 'Policy',        value: 3, color: '#f59e0b' },
    { name: 'Secret',        value: 1, color: '#a78bfa' },
    { name: 'Network',       value: 2, color: '#38bdf8' },
  ]

  const healthyClusters = mockClusters.filter(c => c.status === 'healthy').length
  const cpuSpark = mockClusters[0].metrics.cpu
  const memSpark = mockClusters[0].metrics.memory

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Operations Center"
        subtitle="Real-time infrastructure intelligence across all environments"
        breadcrumb={['Home', 'Dashboard']}
        statusChips={
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs">
              <StatusDot status="healthy" size="xs" />
              <span className="text-emerald-400 font-medium">{healthyClusters} clusters healthy</span>
            </div>
            <div className="w-px h-3.5 bg-gray-700" />
            <div className="flex items-center gap-1.5 text-xs">
              <StatusDot status="critical" size="xs" />
              <span className="text-red-400 font-medium">{mockSummary.openIncidents} open incidents</span>
            </div>
            <div className="w-px h-3.5 bg-gray-700" />
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              <span>Updated just now</span>
            </div>
          </div>
        }
      />

      {/* Stats grid */}
      <motion.div
        variants={stagger.container}
        initial="initial"
        animate="animate"
        className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4"
      >
        <StatCard
          label="Total Clusters"
          value={mockSummary.totalClusters}
          icon={Server}
          iconColor="bg-brand-500/15 text-brand-400"
          sparkline={cpuSpark}
          sparkColor="#6366f1"
          subtext={`${mockSummary.totalNodes} nodes`}
          onClick={() => navigate('/clusters')}
        />
        <StatCard
          label="Healthy Clusters"
          value={mockSummary.healthyClusters}
          icon={CheckCircle2}
          iconColor="bg-emerald-500/15 text-emerald-400"
          sparkline={mockClusters[1].metrics.cpu}
          sparkColor="#10b981"
          subtext={`${mockSummary.totalClusters - mockSummary.healthyClusters} degraded`}
        />
        <StatCard
          label="Open Incidents"
          value={mockSummary.openIncidents}
          icon={AlertTriangle}
          iconColor={mockSummary.openIncidents > 3 ? 'bg-red-500/15 text-red-400' : 'bg-amber-500/15 text-amber-400'}
          trend={{ value: 12, up: true }}
          sparkline={mockClusters[2].metrics.pods}
          sparkColor="#f43f5e"
          onClick={() => navigate('/incidents')}
        />
        <StatCard
          label="Critical Alerts"
          value={mockSummary.criticalIncidents}
          icon={Zap}
          iconColor="bg-red-500/15 text-red-400"
          sparkline={mockClusters[3].metrics.cpu}
          sparkColor="#f43f5e"
          subtext="Active now"
        />
        <StatCard
          label="Security Findings"
          value={mockSummary.securityFindings}
          icon={Shield}
          iconColor="bg-amber-500/15 text-amber-400"
          trend={{ value: 3, up: false }}
          sparkline={memSpark}
          sparkColor="#f59e0b"
          onClick={() => navigate('/security')}
        />
        <StatCard
          label="Est. Monthly Savings"
          value={`$${(mockSummary.totalSavings / 1000).toFixed(1)}k`}
          icon={DollarSign}
          iconColor="bg-emerald-500/15 text-emerald-400"
          sparkline={mockClusters[4].metrics.memory}
          sparkColor="#10b981"
          subtext="6 recommendations"
          onClick={() => navigate('/cost')}
        />
      </motion.div>

      {/* Main charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Incident trend chart */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12, duration: 0.3 }}
          className="xl:col-span-2"
        >
          <Card>
            <CardHeader
              title="Incident & Alert Trend"
              subtitle="Last 24 hours"
              icon={<Activity className="w-3.5 h-3.5" />}
              actions={
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <span className="w-3 h-0.5 rounded bg-red-400" />
                    Incidents
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <span className="w-3 h-0.5 rounded bg-amber-400" />
                    Alerts
                  </div>
                </div>
              }
            />
            <div className="p-4 pt-5">
              <MetricsAreaChart
                data={incidentTrend}
                series={[
                  { key: 'incidents', label: 'Incidents', color: '#f43f5e', gradient: 'grad-incidents' },
                  { key: 'alerts',    label: 'Alerts',    color: '#f59e0b', gradient: 'grad-alerts'    },
                ]}
                height={200}
              />
            </div>
          </Card>
        </motion.div>

        {/* Security findings donut */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.16, duration: 0.3 }}
        >
          <Card className="h-full">
            <CardHeader
              title="Security Findings"
              subtitle="By category"
              icon={<Shield className="w-3.5 h-3.5" />}
              actions={
                <button
                  onClick={() => navigate('/security')}
                  className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"
                >
                  View all <ArrowRight className="w-3 h-3" />
                </button>
              }
            />
            <div className="p-5 flex items-center justify-center">
              <DonutChart
                data={findingsByCategory}
                size={150}
                innerRadius={48}
                outerRadius={68}
                centerValue={13}
                centerLabel="total"
              />
            </div>
          </Card>
        </motion.div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Recent incidents */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.3 }}
          className="xl:col-span-2"
        >
          <Card>
            <CardHeader
              title="Recent Incidents"
              subtitle={`${openIncidents.length} open`}
              icon={<AlertTriangle className="w-3.5 h-3.5" />}
              actions={
                <button
                  onClick={() => navigate('/incidents')}
                  className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"
                >
                  All incidents <ArrowRight className="w-3 h-3" />
                </button>
              }
            />
            <div className="divide-y divide-white/[0.04]">
              {openIncidents.slice(0, 5).map((inc) => (
                <div key={inc.id} className="flex items-start gap-3 px-5 py-3.5 hover:bg-white/[0.02] transition-colors">
                  <Badge value={inc.severity} dot size="xs" className="mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-200 font-medium leading-snug truncate">{inc.title}</p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                      <span className="font-mono">{inc.affectedCluster}</span>
                      <span>·</span>
                      <span>{inc.affectedService}</span>
                      <span>·</span>
                      <span>{formatDistanceToNow(new Date(inc.createdAt), { addSuffix: true })}</span>
                    </div>
                  </div>
                  <Badge value={inc.status} size="xs" className="flex-shrink-0 mt-0.5" />
                </div>
              ))}
              {openIncidents.length === 0 && (
                <div className="flex flex-col items-center gap-2 py-10 text-center">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500/50" />
                  <p className="text-sm text-gray-500">No open incidents</p>
                </div>
              )}
            </div>
          </Card>
        </motion.div>

        {/* Service health */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.24, duration: 0.3 }}
        >
          <Card className="h-full">
            <CardHeader
              title="Service Health"
              subtitle={`${mockSummary.healthyServices}/${mockSummary.totalServices} operational`}
              icon={<Activity className="w-3.5 h-3.5" />}
            />
            <div className="divide-y divide-white/[0.04]">
              {mockServiceHealth.slice(0, 8).map((svc) => (
                <div key={svc.name} className="flex items-center gap-3 px-5 py-2.5 hover:bg-white/[0.02] transition-colors">
                  <StatusDot status={svc.status} size="sm" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-300 truncate">{svc.name}</p>
                    <p className="text-[10px] text-gray-600 mt-0.5">{svc.responseTime > 0 ? `${svc.responseTime}ms` : 'Down'} · {svc.uptime}% uptime</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    {svc.errorRate > 0 && (
                      <p className="text-[10px] text-red-400">{svc.errorRate}% err</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>
      </div>

      {/* Cluster overview strip */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.28, duration: 0.3 }}
      >
        <Card>
          <CardHeader
            title="Cluster Overview"
            subtitle={`${mockSummary.totalClusters} clusters · ${mockSummary.totalNodes} nodes`}
            icon={<Server className="w-3.5 h-3.5" />}
            actions={
              <button
                onClick={() => navigate('/clusters')}
                className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"
              >
                Manage <ArrowRight className="w-3 h-3" />
              </button>
            }
          />
          <div className="p-4 grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3">
            {mockClusters.map((cluster) => (
              <div
                key={cluster.id}
                className={clsx(
                  'p-3 rounded-lg border transition-colors cursor-pointer group',
                  cluster.status === 'healthy'
                    ? 'bg-emerald-500/5 border-emerald-500/15 hover:border-emerald-500/30'
                    : cluster.status === 'degraded'
                    ? 'bg-amber-500/5 border-amber-500/20 hover:border-amber-500/35'
                    : cluster.status === 'maintenance'
                    ? 'bg-violet-500/5 border-violet-500/15 hover:border-violet-500/30'
                    : 'bg-surface-200 border-white/[0.05]',
                )}
                onClick={() => navigate('/clusters')}
              >
                <div className="flex items-center justify-between mb-2">
                  <StatusDot status={cluster.status} size="xs" />
                  <span className="text-[9px] font-mono text-gray-600 uppercase">{cluster.provider}</span>
                </div>
                <p className="text-xs font-medium text-gray-200 truncate leading-snug">{cluster.name}</p>
                <p className="text-[10px] text-gray-600 mt-1">{cluster.nodeCount} nodes</p>
                <ProgressBar value={cluster.cpuUsage} height="xs" className="mt-2" />
                <p className="text-[9px] text-gray-700 mt-1 text-right">{cluster.cpuUsage}% CPU</p>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>
    </div>
  )
}
