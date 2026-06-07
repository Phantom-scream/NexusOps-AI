import { NavLink } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  Server,
  AlertTriangle,
  Shield,
  DollarSign,
  BrainCircuit,
  Zap,
  ChevronLeft,
  ChevronRight,
  Activity,
  Settings,
  HelpCircle,
  LineChart,
} from 'lucide-react'
import clsx from 'clsx'
import { useSidebar } from '@/contexts/SidebarContext'
import StatusDot from '@/components/ui/StatusDot'
import { mockSummary } from '@/data/mock'

interface NavItem {
  to: string
  label: string
  icon: React.ElementType
  badge?: number
  badgeColor?: string
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const navGroups: NavGroup[] = [
  {
    label: 'Overview',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    label: 'Infrastructure',
    items: [
      { to: '/clusters', label: 'Clusters', icon: Server },
      { to: '/observability', label: 'Observability', icon: LineChart },
    ],
  },
  {
    label: 'Operations',
    items: [
      { to: '/incidents', label: 'Incidents', icon: AlertTriangle, badge: mockSummary.openIncidents, badgeColor: 'bg-red-500' },
      { to: '/cost', label: 'Cost', icon: DollarSign },
    ],
  },
  {
    label: 'Security & AI',
    items: [
      { to: '/security', label: 'Security', icon: Shield, badge: mockSummary.criticalFindings, badgeColor: 'bg-red-500' },
      { to: '/ai', label: 'AI Investigation', icon: BrainCircuit },
      { to: '/settings', label: 'Settings', icon: Settings },
    ],
  },
]

export default function Sidebar() {
  const { collapsed, toggle } = useSidebar()

  return (
    <motion.aside
      animate={{ width: collapsed ? 64 : 220 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className="relative z-10 flex-shrink-0 bg-surface-100/82 border-r border-white/[0.08] flex flex-col overflow-hidden backdrop-blur-xl"
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-brand-500/10 to-transparent" />
      {/* Logo */}
      <div className="relative h-14 flex items-center px-4 border-b border-white/[0.08] flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-cyan-400 flex items-center justify-center shadow-glow flex-shrink-0">
            <Zap className="w-3.5 h-3.5 text-white" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -6 }}
                transition={{ duration: 0.15 }}
                className="font-bold text-sm tracking-tight text-gray-50 whitespace-nowrap"
              >
                NexusOps AI
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Nav */}
      <nav className="relative flex-1 py-3 overflow-y-auto overflow-x-hidden">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-1">
            <AnimatePresence>
              {!collapsed && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="px-4 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-gray-600"
                >
                  {group.label}
                </motion.p>
              )}
            </AnimatePresence>
            {collapsed && <div className="h-3" />}
            {group.items.map(({ to, label, icon: Icon, badge, badgeColor }) => (
              <NavLink
                key={to}
                to={to}
                title={collapsed ? label : undefined}
                className={({ isActive }) =>
                  clsx(
                    'relative flex items-center gap-3 mx-2 px-2.5 py-2 rounded-lg text-sm transition-all duration-200 group',
                    collapsed && 'justify-center',
                    isActive
                      ? 'bg-gradient-to-r from-brand-500/18 to-cyan-400/10 text-gray-50 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)]'
                      : 'text-gray-500 hover:text-gray-200 hover:bg-white/[0.05]',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="absolute left-0 top-1 bottom-1 w-0.5 bg-cyan-300 rounded-full shadow-[0_0_18px_rgba(34,211,238,0.8)]"
                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                      />
                    )}
                    <Icon className={clsx('w-4 h-4 flex-shrink-0', isActive ? 'text-cyan-300' : '')} />
                    <AnimatePresence>
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          className="flex-1 whitespace-nowrap font-medium"
                        >
                          {label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                    {!collapsed && badge !== undefined && badge > 0 && (
                      <span className={clsx('text-[10px] font-bold text-white px-1.5 py-0.5 rounded-full leading-none', badgeColor ?? 'bg-brand-600')}>
                        {badge}
                      </span>
                    )}
                    {collapsed && badge !== undefined && badge > 0 && (
                      <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* System Status */}
      <div className="relative border-t border-white/[0.08] p-3 space-y-2 bg-black/10">
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="px-1 py-1.5 flex items-center gap-2"
            >
              <StatusDot status="healthy" size="xs" />
              <span className="text-[11px] text-gray-600">
                {mockSummary.healthyServices}/{mockSummary.totalServices} services healthy
              </span>
            </motion.div>
          )}
        </AnimatePresence>
        <div className={clsx('flex gap-1', collapsed && 'flex-col')}>
          <button className="p-2 rounded-lg text-gray-600 hover:text-gray-400 hover:bg-white/[0.04] transition-colors" title="Settings">
            <Settings className="w-3.5 h-3.5" />
          </button>
          <button className="p-2 rounded-lg text-gray-600 hover:text-gray-400 hover:bg-white/[0.04] transition-colors" title="Help">
            <HelpCircle className="w-3.5 h-3.5" />
          </button>
          <button className="p-2 rounded-lg text-gray-600 hover:text-gray-400 hover:bg-white/[0.04] transition-colors" title="Activity">
            <Activity className="w-3.5 h-3.5" />
          </button>
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="px-1 text-[10px] text-gray-700 font-mono"
            >
              v0.1.0 · Enterprise
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Toggle button */}
      <button
        onClick={toggle}
        className="absolute -right-3 top-16 w-6 h-6 rounded-full bg-surface-300 border border-white/[0.12] flex items-center justify-center text-gray-500 hover:text-gray-200 hover:bg-surface-400 transition-colors shadow-lg z-10"
      >
        {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
      </button>
    </motion.aside>
  )
}
