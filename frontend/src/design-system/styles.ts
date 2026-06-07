export const surface = {
  panel: 'bg-surface-100/80 border border-white/[0.08] shadow-panel backdrop-blur-xl',
  panelHover:
    'transition-all duration-200 hover:border-cyan-300/20 hover:bg-surface-200/85 hover:shadow-glow',
  inset: 'bg-surface-200/70 border border-white/[0.06]',
  iconTile: 'rounded-lg bg-white/[0.04] border border-white/[0.06]',
}

export const focusRing =
  'focus:outline-none focus:ring-2 focus:ring-cyan-300/30 focus:border-cyan-300/40'

export const button = {
  primary:
    'inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-brand-500 to-cyan-400 px-4 py-2 text-sm font-semibold text-white shadow-glow transition-all duration-200 hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60',
  secondary:
    'inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.04] px-4 py-2 text-sm font-medium text-gray-200 transition-all duration-200 hover:border-white/[0.16] hover:bg-white/[0.08] disabled:cursor-not-allowed disabled:opacity-60',
  ghost:
    'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-400 transition-all duration-200 hover:bg-white/[0.06] hover:text-gray-100',
}
