import clsx from 'clsx'

interface ProgressBarProps {
  value: number
  max?: number
  className?: string
  height?: 'xs' | 'sm' | 'md'
  color?: 'default' | 'success' | 'warning' | 'danger' | 'brand'
  showLabel?: boolean
  animate?: boolean
}

const colorClasses = {
  default: 'bg-brand-500',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  danger: 'bg-red-500',
  brand: 'bg-brand-500',
}

const heightClasses = {
  xs: 'h-1',
  sm: 'h-1.5',
  md: 'h-2',
}

function getAutoColor(pct: number): keyof typeof colorClasses {
  if (pct >= 90) return 'danger'
  if (pct >= 75) return 'warning'
  return 'success'
}

export default function ProgressBar({
  value,
  max = 100,
  className,
  height = 'sm',
  color,
  showLabel,
  animate,
}: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  const resolvedColor = color ?? getAutoColor(pct)

  return (
    <div className={clsx('w-full', className)}>
      <div className={clsx('w-full bg-surface-300 rounded-full overflow-hidden', heightClasses[height])}>
        <div
          className={clsx('h-full rounded-full transition-all duration-500', colorClasses[resolvedColor])}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500">{value}</span>
          <span className="text-xs text-gray-500">{pct.toFixed(0)}%</span>
        </div>
      )}
    </div>
  )
}
