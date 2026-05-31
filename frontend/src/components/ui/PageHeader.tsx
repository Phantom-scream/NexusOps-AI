import { type ReactNode } from 'react'
import clsx from 'clsx'

interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  breadcrumb?: string[]
  statusChips?: ReactNode
  className?: string
}

export default function PageHeader({
  title,
  subtitle,
  actions,
  breadcrumb,
  statusChips,
  className,
}: PageHeaderProps) {
  return (
    <div className={clsx('flex items-start justify-between gap-4 mb-6', className)}>
      <div>
        {breadcrumb && breadcrumb.length > 0 && (
          <div className="flex items-center gap-1.5 mb-1.5">
            {breadcrumb.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1.5">
                {i > 0 && <span className="text-gray-600 text-xs">/</span>}
                <span className="text-xs text-gray-500">{crumb}</span>
              </span>
            ))}
          </div>
        )}
        <h1 className="text-xl font-bold text-gray-50 tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
        {statusChips && <div className="flex items-center gap-2 mt-3">{statusChips}</div>}
      </div>
      {actions && (
        <div className="flex items-center gap-2 flex-shrink-0 pt-0.5">{actions}</div>
      )}
    </div>
  )
}
