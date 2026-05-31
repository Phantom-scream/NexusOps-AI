import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'

interface MiniSparklineProps {
  data: number[]
  color?: string
  height?: number
  width?: number
}

export default function MiniSparkline({
  data,
  color = '#6366f1',
  height = 36,
  width = 80,
}: MiniSparklineProps) {
  const chartData = data.map((value, i) => ({ i, value }))
  return (
    <ResponsiveContainer width={width} height={height}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
        <Tooltip
          content={() => null}
          cursor={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
