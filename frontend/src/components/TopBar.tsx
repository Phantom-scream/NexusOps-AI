import { useLocation, useNavigate, NavLink } from 'react-router-dom'
import { Bell, LogOut, User, Search, RefreshCw, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import { useAuthStore } from '@/store/authStore'
import Badge from '@/components/ui/Badge'
import { mockSummary } from '@/data/mock'

const routeLabels: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/clusters': 'Infrastructure',
  '/observability': 'Observability',
  '/incidents': 'Incidents',
  '/security': 'Security',
  '/cost': 'Cost Optimization',
  '/ai': 'AI Investigation',
  '/settings': 'Settings',
}

export default function TopBar() {
  const { email, role, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchFocused, setSearchFocused] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const currentLabel = routeLabels[location.pathname] ?? 'NexusOps AI'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleRefresh = () => {
    setRefreshing(true)
    setTimeout(() => setRefreshing(false), 1200)
  }

  return (
    <header className="h-14 flex items-center gap-3 px-5 border-b border-white/[0.08] bg-surface-100/72 backdrop-blur-xl flex-shrink-0">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-gray-500 flex-shrink-0">
        <span className="text-gray-600">NexusOps</span>
        <ChevronRight className="w-3 h-3 text-gray-700" />
        <span className="text-gray-300 font-medium">{currentLabel}</span>
      </nav>

      {/* Search */}
      <div
        className={clsx(
          'flex-1 max-w-md mx-4 relative transition-all duration-200',
          searchFocused ? 'max-w-xl' : 'max-w-md',
        )}
      >
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600 pointer-events-none" />
        <input
          type="text"
          placeholder="Search clusters, incidents, resources…"
          onFocus={() => setSearchFocused(true)}
          onBlur={() => setSearchFocused(false)}
          className="w-full bg-surface-200/70 border border-white/[0.08] text-gray-300 placeholder-gray-600 rounded-lg pl-9 pr-4 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-300/20 focus:border-cyan-300/40 focus:bg-surface-300/80 transition-all"
        />
      </div>

      <div className="flex items-center gap-1.5 ml-auto">
        {/* System health chip */}
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 mr-1 shadow-[0_0_24px_rgba(16,185,129,0.08)]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] text-emerald-400 font-medium whitespace-nowrap">
            {mockSummary.healthyClusters}/{mockSummary.totalClusters} clusters
          </span>
        </div>

        {/* Refresh */}
        <button
          onClick={handleRefresh}
          className="p-2 rounded-lg text-gray-500 hover:text-gray-200 hover:bg-white/[0.04] transition-colors"
          title="Refresh"
        >
          <RefreshCw className={clsx('w-3.5 h-3.5', refreshing && 'animate-spin')} />
        </button>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg text-gray-500 hover:text-gray-200 hover:bg-white/[0.04] transition-colors">
          <Bell className="w-3.5 h-3.5" />
          {mockSummary.criticalIncidents > 0 && (
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
          )}
        </button>

        {/* User */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-200/75 border border-white/[0.08] ml-1">
          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-brand-500/50 to-cyan-400/40 border border-cyan-300/20 flex items-center justify-center">
            <User className="w-3 h-3 text-cyan-200" />
          </div>
          <span className="text-xs text-gray-300 hidden sm:block max-w-[120px] truncate">{email}</span>
          {role && <Badge value={role} size="xs" />}
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="p-2 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          title="Log out"
        >
          <LogOut className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  )
}
