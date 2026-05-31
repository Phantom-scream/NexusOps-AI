import clsx from 'clsx'
import { type MouseEventHandler, type ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  hover?: boolean
  glow?: boolean
  as?: 'div' | 'article' | 'section'
  onClick?: MouseEventHandler<HTMLElement>
}

export function Card({ children, className, hover, glow, as: Tag = 'div', onClick }: CardProps) {
  return (
    <Tag
      onClick={onClick}
      className={clsx(
        'bg-surface-100 border border-white/[0.06] rounded-xl',
        (hover || onClick) && 'transition-all duration-200 hover:border-white/[0.1] hover:bg-surface-200 cursor-pointer',
        glow && 'shadow-lg shadow-brand-900/20',
        className,
      )}
    >
      {children}
    </Tag>
  )
}

interface CardHeaderProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  icon?: ReactNode
  className?: string
}

export function CardHeader({ title, subtitle, actions, icon, className }: CardHeaderProps) {
  return (
    <div className={clsx('flex items-center justify-between px-5 py-4 border-b border-white/[0.05]', className)}>
      <div className="flex items-center gap-3 min-w-0">
        {icon && (
          <div className="w-7 h-7 rounded-lg bg-surface-300 flex items-center justify-center text-gray-400 flex-shrink-0">
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-gray-100 truncate">{title}</h3>
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2 flex-shrink-0 ml-4">{actions}</div>}
    </div>
  )
}
