import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  type TooltipProps,
} from 'recharts'
import type { MetricPoint } from '@/types'

interface SeriesConfig {
  key: string
  label: string
  color: string
  gradient: string
}

interface MetricsAreaChartProps {
  data: MetricPoint[]
  series: SeriesConfig[]
  height?: number
  showGrid?: boolean
  showAxes?: boolean
}

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-200 border border-white/[0.08] rounded-lg p-3 shadow-xl text-xs min-w-[120px]">
      <p className="text-gray-400 mb-2 font-medium">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4 mb-1">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-gray-400">{entry.name}</span>
          </span>
          <span className="text-gray-100 font-semibold">{entry.value}</span>
        </div>
      ))}
    </div>
  )
}

export default function MetricsAreaChart({
  data,
  series,
  height = 200,
  showGrid = true,
  showAxes = true,
}: MetricsAreaChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
        <defs>
          {series.map((s) => (
            <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={s.color} stopOpacity={0.35} />
              <stop offset="95%" stopColor={s.color} stopOpacity={0.0} />
            </linearGradient>
          ))}
        </defs>
        {showGrid && (
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.04)"
            vertical={false}
          />
        )}
        {showAxes && (
          <XAxis
            dataKey="time"
            tick={{ fill: '#6b7280', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
        )}
        {showAxes && (
          <YAxis
            tick={{ fill: '#6b7280', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={30}
          />
        )}
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.08)', strokeWidth: 1 }} />
        {series.map((s) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={s.color}
            strokeWidth={1.5}
            fill={`url(#grad-${s.key})`}
            dot={false}
            activeDot={{ r: 3, fill: s.color, stroke: 'transparent' }}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}
