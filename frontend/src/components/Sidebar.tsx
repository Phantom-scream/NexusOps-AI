import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Server,
  AlertTriangle,
  Shield,
  DollarSign,
  BrainCircuit,
  Zap,
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/clusters', label: 'Clusters', icon: Server },
  { to: '/incidents', label: 'Incidents', icon: AlertTriangle },
  { to: '/security', label: 'Security', icon: Shield },
  { to: '/cost', label: 'Cost', icon: DollarSign },
  { to: '/ai', label: 'AI Investigation', icon: BrainCircuit },
]

export default function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 bg-surface-100 border-r border-gray-700/50 flex flex-col">
      {/* Logo */}
      <div className="h-14 flex items-center gap-2.5 px-5 border-b border-gray-700/50">
        <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <span className="font-semibold text-sm tracking-tight text-gray-100">NexusOps AI</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150',
                isActive
                  ? 'bg-brand-600/20 text-brand-300 font-medium'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-surface-300',
              )
            }
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-gray-700/50">
        <div className="px-3 py-2 text-xs text-gray-600">v0.1.0 — Enterprise Edition</div>
      </div>
    </aside>
  )
}
