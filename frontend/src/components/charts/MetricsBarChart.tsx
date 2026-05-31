import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  type TooltipProps,
} from 'recharts'
import type { MetricPoint } from '@/types'

interface BarConfig {
  key: string
  label: string
  color: string
}

interface MetricsBarChartProps {
  data: MetricPoint[]
  bars: BarConfig[]
  height?: number
  showGrid?: boolean
}

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-200 border border-white/[0.08] rounded-lg p-3 shadow-xl text-xs min-w-[130px]">
      <p className="text-gray-400 mb-2 font-medium">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4 mb-1">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: entry.color }} />
            <span className="text-gray-400">{entry.name}</span>
          </span>
          <span className="text-gray-100 font-semibold">
            ${typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function MetricsBarChart({ data, bars, height = 200, showGrid = true }: MetricsBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
        {showGrid && (
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
        )}
        <XAxis
          dataKey="time"
          tick={{ fill: '#6b7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#6b7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          width={40}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        {bars.map((b, i) => (
          <Bar
            key={b.key}
            dataKey={b.key}
            name={b.label}
            fill={b.color}
            radius={i === bars.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
            fillOpacity={0.85}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
