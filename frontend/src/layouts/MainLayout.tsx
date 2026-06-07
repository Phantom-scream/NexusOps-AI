import { Outlet, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Sidebar from '@/components/Sidebar'
import TopBar from '@/components/TopBar'
import { SidebarProvider } from '@/contexts/SidebarContext'

export default function MainLayout() {
  const location = useLocation()
  return (
    <SidebarProvider>
      <div className="relative flex h-screen overflow-hidden bg-surface">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,rgba(109,93,251,0.16),transparent_30rem),radial-gradient(circle_at_85%_10%,rgba(34,211,238,0.1),transparent_28rem)]" />
        <Sidebar />
        <div className="relative flex flex-col flex-1 min-w-0 overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.18, ease: 'easeOut' }}
                className="p-4 md:p-6 min-h-full"
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>
    </SidebarProvider>
  )
}
