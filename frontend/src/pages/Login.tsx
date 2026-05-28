import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Zap, Loader2 } from 'lucide-react'
import { api } from '@/services/api'
import { useAuthStore } from '@/store/authStore'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const loginMutation = useMutation({
    mutationFn: () =>
      api.post('/auth/login', { email, password }).then((r) => r.data),
    onSuccess: (data) => {
      setAuth(data.access_token, data.refresh_token, email, 'viewer')
      navigate('/dashboard')
    },
    onError: () => setError('Invalid email or password'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    loginMutation.mutate()
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-brand-600 flex items-center justify-center mx-auto mb-4">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100">NexusOps AI</h1>
          <p className="text-sm text-gray-500 mt-1">AIOps Intelligence Platform</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="card p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Email</label>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="input"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Password</label>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="input"
            />
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loginMutation.isPending}
            className="btn-primary w-full justify-center"
          >
            {loginMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : null}
            {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
