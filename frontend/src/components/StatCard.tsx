import { type ReactNode } from 'react'
import clsx from 'clsx'

interface StatCardProps {
  label: string
  value: string | number
  icon?: ReactNode
  trend?: { value: number; positive?: boolean }
  color?: 'default' | 'red' | 'green' | 'yellow' | 'blue' | 'purple'
  className?: string
}

const colorMap = {
  default: 'text-gray-100',
  red: 'text-red-400',
  green: 'text-green-400',
  yellow: 'text-yellow-400',
  blue: 'text-blue-400',
  purple: 'text-brand-400',
}

export default function StatCard({ label, value, icon, trend, color = 'default', className }: StatCardProps) {
  return (
    <div className={clsx('stat-card', className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</span>
        {icon && <span className="text-gray-500">{icon}</span>}
      </div>
      <div className={clsx('text-2xl font-bold mt-1', colorMap[color])}>{value}</div>
      {trend && (
        <div
          className={clsx(
            'text-xs mt-0.5',
            trend.positive ? 'text-green-400' : 'text-red-400',
          )}
        >
          {trend.positive ? '▲' : '▼'} {Math.abs(trend.value)}%
        </div>
      )}
    </div>
  )
}
