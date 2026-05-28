import clsx from 'clsx'

interface StatusBadgeProps {
  value: string
  size?: 'sm' | 'md'
}

const severityMap: Record<string, string> = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
  healthy: 'badge-healthy',
  active: 'badge-healthy',
  running: 'badge-healthy',
  open: 'badge-error',
  investigating: 'badge-medium',
  resolved: 'badge-healthy',
  closed: 'bg-gray-500/15 text-gray-400 border border-gray-500/30',
  degraded: 'badge-medium',
  error: 'badge-error',
  unknown: 'bg-gray-500/15 text-gray-400 border border-gray-500/30',
}

export default function StatusBadge({ value, size = 'sm' }: StatusBadgeProps) {
  const colorClass = severityMap[value?.toLowerCase()] ?? 'badge-low'
  return (
    <span
      className={clsx(
        'badge capitalize',
        colorClass,
        size === 'md' && 'text-sm px-3 py-1',
      )}
    >
      {value}
    </span>
  )
}
