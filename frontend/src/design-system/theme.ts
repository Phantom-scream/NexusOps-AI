import { tokens } from './tokens'

export const severityPalette = {
  critical: tokens.color.danger,
  high: '#FB7185',
  medium: tokens.color.warning,
  low: '#38BDF8',
  info: tokens.color.brand2,
  healthy: tokens.color.success,
  degraded: tokens.color.warning,
  unknown: tokens.color.textMuted,
} as const

export const chartPalette = {
  cyan: tokens.color.brand2,
  violet: tokens.color.brand,
  emerald: tokens.color.success,
  amber: tokens.color.warning,
  rose: tokens.color.danger,
  blue: '#60A5FA',
} as const
