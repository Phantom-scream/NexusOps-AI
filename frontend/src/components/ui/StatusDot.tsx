import clsx from 'clsx'

type Status = 'healthy' | 'degraded' | 'critical' | 'down' | 'unknown' | 'maintenance'

const sizeMap = { xs: 'w-1.5 h-1.5', sm: 'w-2 h-2', md: 'w-2.5 h-2.5', lg: 'w-3 h-3' }
const colorMap: Record<Status, string> = {
  healthy:     'bg-emerald-400',
  degraded:    'bg-amber-400',
  critical:    'bg-red-400',
  down:        'bg-red-500',
  unknown:     'bg-gray-500',
  maintenance: 'bg-violet-400',
}
const pulseMap: Record<Status, string> = {
  healthy:     'animate-pulse',
  degraded:    'animate-pulse',
  critical:    'animate-ping',
  down:        'animate-ping',
  unknown:     '',
  maintenance: '',
}

interface StatusDotProps {
  status: Status | string
  size?: 'xs' | 'sm' | 'md' | 'lg'
  className?: string
}

export default function StatusDot({ status, size = 'sm', className }: StatusDotProps) {
  const s = status as Status
  const color = colorMap[s] ?? 'bg-gray-500'
  const pulse = pulseMap[s] ?? ''
  const sz = sizeMap[size]

  return (
    <span className={clsx('relative inline-flex', sz, className)}>
      {pulse && (
        <span className={clsx('absolute inset-0 rounded-full opacity-75', color, pulse)} />
      )}
      <span className={clsx('relative rounded-full', color, sz)} />
    </span>
  )
}
