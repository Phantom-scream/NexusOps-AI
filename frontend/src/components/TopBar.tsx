import { Bell, LogOut, User } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useNavigate } from 'react-router-dom'

export default function TopBar() {
  const { email, role, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-gray-700/50 bg-surface-100 flex-shrink-0">
      <div />
      <div className="flex items-center gap-3">
        <button className="relative p-1.5 rounded-lg text-gray-400 hover:text-gray-100 hover:bg-surface-300 transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-red-500 rounded-full" />
        </button>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-200 border border-gray-700/50">
          <User className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-xs text-gray-300">{email}</span>
          <span className="badge badge-healthy">{role}</span>
        </div>

        <button
          onClick={handleLogout}
          className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          title="Log out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
