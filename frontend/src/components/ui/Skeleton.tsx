import clsx from 'clsx'

interface SkeletonProps {
  className?: string
  rounded?: 'sm' | 'md' | 'lg' | 'full'
  style?: React.CSSProperties
}

export function Skeleton({ className, rounded = 'md', style }: SkeletonProps) {
  const r = { sm: 'rounded', md: 'rounded-lg', lg: 'rounded-xl', full: 'rounded-full' }[rounded]
  return (
    <div
      className={clsx(
        'animate-pulse bg-gradient-to-r from-surface-200 via-surface-300 to-surface-200 bg-[length:200%_100%]',
        r,
        className,
      )}
      style={{ backgroundSize: '200% 100%', animation: 'shimmer 1.8s infinite', ...style }}
    />
  )
}

export function MetricCardSkeleton() {
  return (
    <div className="card p-5 space-y-3">
      <div className="flex justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-6 w-6" rounded="lg" />
      </div>
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-3 w-20" />
    </div>
  )
}

export function TableRowSkeleton({ cols = 5 }: { cols?: number }) {
  return (
    <tr>
      {Array.from({ length: cols }, (_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-3.5" style={{ width: `${50 + (i % 3) * 20}%` } as React.CSSProperties} />
        </td>
      ))}
    </tr>
  )
}

export function ChartSkeleton({ height = 200 }: { height?: number }) {
  return (
    <div className="w-full animate-pulse flex items-end gap-1 px-4" style={{ height }}>
      {Array.from({ length: 24 }, (_, i) => (
        <div
          key={i}
          className="flex-1 bg-surface-300 rounded-t"
          style={{ height: `${34 + Math.sin(i * 0.55) * 26 + (i % 5) * 4}%` }}
        />
      ))}
    </div>
  )
}
