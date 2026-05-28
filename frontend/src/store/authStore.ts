import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  refreshToken: string | null
  email: string | null
  role: string | null
  setAuth: (token: string, refreshToken: string, email: string, role: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      email: null,
      role: null,
      setAuth: (token, refreshToken, email, role) =>
        set({ token, refreshToken, email, role }),
      logout: () => set({ token: null, refreshToken: null, email: null, role: null }),
    }),
    { name: 'nexusops-auth' },
  ),
)
