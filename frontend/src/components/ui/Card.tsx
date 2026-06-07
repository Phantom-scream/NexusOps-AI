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
        'relative overflow-hidden bg-surface-100/80 border border-white/[0.08] rounded-xl shadow-panel backdrop-blur-xl',
        'before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent',
        (hover || onClick)
          && 'transition-all duration-200 hover:-translate-y-0.5 hover:border-cyan-300/20 hover:bg-surface-200/85 hover:shadow-glow cursor-pointer',
        glow && 'shadow-glow',
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
    <div className={clsx('flex items-center justify-between px-5 py-4 border-b border-white/[0.07] bg-white/[0.015]', className)}>
      <div className="flex items-center gap-3 min-w-0">
        {icon && (
          <div className="w-7 h-7 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-cyan-300 flex-shrink-0">
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
