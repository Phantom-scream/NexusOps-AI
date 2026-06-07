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
    <div className={clsx('relative overflow-hidden rounded-xl border border-white/[0.08] bg-surface-100/55 p-5 shadow-panel backdrop-blur-xl mb-6', className)}>
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-300/35 to-transparent" />
      <div className="pointer-events-none absolute -right-16 -top-20 h-48 w-48 rounded-full bg-cyan-400/10 blur-3xl" />
      <div className="relative flex items-start justify-between gap-4">
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
    </div>
  )
}
