import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from '@/layouts/MainLayout'
import Dashboard from '@/pages/Dashboard'
import Clusters from '@/pages/Clusters'
import Incidents from '@/pages/Incidents'
import Security from '@/pages/Security'
import CostOptimization from '@/pages/CostOptimization'
import AIInvestigation from '@/pages/AIInvestigation'
import Login from '@/pages/Login'
import { useAuthStore } from '@/store/authStore'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <MainLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="clusters" element={<Clusters />} />
          <Route path="incidents" element={<Incidents />} />
          <Route path="security" element={<Security />} />
          <Route path="cost" element={<CostOptimization />} />
          <Route path="ai" element={<AIInvestigation />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
