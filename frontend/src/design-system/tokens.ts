export const tokens = {
  color: {
    background: '#070A12',
    surface: '#0D1320',
    surfaceElevated: '#121A2B',
    surfacePressed: '#182238',
    border: 'rgba(148, 163, 184, 0.14)',
    borderStrong: 'rgba(148, 163, 184, 0.24)',
    text: '#F8FAFC',
    textSecondary: '#94A3B8',
    textMuted: '#64748B',
    brand: '#6D5DFB',
    brand2: '#22D3EE',
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#F43F5E',
  },
  radius: {
    sm: '6px',
    md: '8px',
    lg: '10px',
    xl: '12px',
  },
  shadow: {
    panel: '0 18px 60px rgba(0, 0, 0, 0.28)',
    glow: '0 0 0 1px rgba(109, 93, 251, 0.12), 0 24px 80px rgba(34, 211, 238, 0.08)',
  },
  motion: {
    fast: '150ms',
    normal: '220ms',
  },
} as const

export type DesignTokens = typeof tokens
