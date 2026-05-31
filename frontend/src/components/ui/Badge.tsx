import clsx from 'clsx'
import type { Severity, HealthStatus, IncidentStatus, FindingStatus } from '@/types'

type BadgeVariant =
  | Severity
  | HealthStatus
  | IncidentStatus
  | FindingStatus
  | 'info'
  | 'pending'
  | 'implementing'
  | 'implemented'
  | 'dismissed'
  | 'aws'
  | 'gcp'
  | 'azure'
  | 'hybrid'
  | 'on-premise'
  | 'maintenance'

const variantClasses: Record<string, string> = {
  critical:      'bg-red-500/15 text-red-400 border-red-500/30',
  high:          'bg-orange-500/15 text-orange-400 border-orange-500/30',
  medium:        'bg-amber-500/15 text-amber-400 border-amber-500/30',
  low:           'bg-blue-500/15 text-blue-400 border-blue-500/30',
  info:          'bg-sky-500/15 text-sky-400 border-sky-500/30',
  healthy:       'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  degraded:      'bg-amber-500/15 text-amber-400 border-amber-500/30',
  unknown:       'bg-gray-500/15 text-gray-400 border-gray-500/30',
  maintenance:   'bg-violet-500/15 text-violet-400 border-violet-500/30',
  open:          'bg-red-500/15 text-red-400 border-red-500/30',
  acknowledged:  'bg-amber-500/15 text-amber-400 border-amber-500/30',
  investigating: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  resolved:      'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  in_progress:   'bg-blue-500/15 text-blue-400 border-blue-500/30',
  suppressed:    'bg-gray-500/15 text-gray-400 border-gray-500/30',
  pending:       'bg-gray-500/15 text-gray-400 border-gray-500/30',
  implementing:  'bg-blue-500/15 text-blue-400 border-blue-500/30',
  implemented:   'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  dismissed:     'bg-gray-600/15 text-gray-500 border-gray-600/30',
  aws:           'bg-orange-500/15 text-orange-400 border-orange-500/30',
  gcp:           'bg-blue-500/15 text-blue-400 border-blue-500/30',
  azure:         'bg-sky-500/15 text-sky-400 border-sky-500/30',
  hybrid:        'bg-violet-500/15 text-violet-400 border-violet-500/30',
  'on-premise':  'bg-gray-500/15 text-gray-400 border-gray-500/30',
}

interface BadgeProps {
  value: string
  variant?: BadgeVariant
  dot?: boolean
  size?: 'xs' | 'sm' | 'md'
  className?: string
}

const dotColors: Record<string, string> = {
  critical: 'bg-red-400',
  high: 'bg-orange-400',
  medium: 'bg-amber-400',
  low: 'bg-blue-400',
  healthy: 'bg-emerald-400',
  degraded: 'bg-amber-400',
  down: 'bg-red-400',
  open: 'bg-red-400',
  investigating: 'bg-blue-400',
  resolved: 'bg-emerald-400',
  acknowledged: 'bg-amber-400',
  maintenance: 'bg-violet-400',
}

export default function Badge({ value, variant, dot, size = 'sm', className }: BadgeProps) {
  const key = (variant ?? value).toLowerCase().replace(' ', '_')
  const colors = variantClasses[key] ?? 'bg-gray-500/15 text-gray-400 border-gray-500/30'
  const dotColor = dotColors[key] ?? 'bg-gray-400'
  const sizeClass = {
    xs: 'text-[10px] px-1.5 py-0.5 gap-1',
    sm: 'text-xs px-2 py-0.5 gap-1.5',
    md: 'text-sm px-3 py-1 gap-2',
  }[size]

  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full border capitalize',
        colors,
        sizeClass,
        className,
      )}
    >
      {dot && <span className={clsx('w-1.5 h-1.5 rounded-full flex-shrink-0', dotColor)} />}
      {value.replace('_', ' ')}
    </span>
  )
}
