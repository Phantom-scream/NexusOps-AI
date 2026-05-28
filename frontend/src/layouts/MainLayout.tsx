import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/Sidebar'
import TopBar from '@/components/TopBar'

export default function MainLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
