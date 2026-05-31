import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, type TooltipProps } from 'recharts'

export interface DonutSlice {
  name: string
  value: number
  color: string
}

interface DonutChartProps {
  data: DonutSlice[]
  size?: number
  innerRadius?: number
  outerRadius?: number
  showLegend?: boolean
  centerLabel?: string
  centerValue?: string | number
}

function CustomTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  const item = payload[0]
  return (
    <div className="bg-surface-200 border border-white/[0.08] rounded-lg px-3 py-2 shadow-xl text-xs">
      <p className="font-medium text-gray-200">{item.name}</p>
      <p className="text-gray-400 mt-0.5">{item.value} findings</p>
    </div>
  )
}

export default function DonutChart({
  data,
  size = 160,
  innerRadius = 50,
  outerRadius = 72,
  showLegend = true,
  centerLabel,
  centerValue,
}: DonutChartProps) {
  const total = data.reduce((s, d) => s + d.value, 0)

  return (
    <div className="flex items-center gap-6">
      <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={innerRadius}
              outerRadius={outerRadius}
              dataKey="value"
              strokeWidth={0}
              paddingAngle={2}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} opacity={0.9} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        {(centerLabel || centerValue) && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            {centerValue !== undefined && (
              <span className="text-2xl font-bold text-gray-100">{centerValue}</span>
            )}
            {centerLabel && <span className="text-xs text-gray-500 mt-0.5">{centerLabel}</span>}
          </div>
        )}
      </div>
      {showLegend && (
        <div className="flex flex-col gap-2 min-w-0">
          {data.map((item) => (
            <div key={item.name} className="flex items-center gap-2 text-xs">
              <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: item.color }} />
              <span className="text-gray-400 flex-1 truncate">{item.name}</span>
              <span className="text-gray-200 font-semibold ml-auto pl-2">
                {item.value}
                <span className="text-gray-600 font-normal ml-1 text-[10px]">
                  ({total ? Math.round((item.value / total) * 100) : 0}%)
                </span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
