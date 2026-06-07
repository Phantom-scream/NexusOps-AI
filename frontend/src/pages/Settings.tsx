import { CheckCircle2, KeyRound, Palette, ServerCog, ShieldCheck } from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'

const settings = [
  ['Backend API', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'],
  ['WebSocket URL', import.meta.env.VITE_WS_URL || 'ws://localhost:8000'],
  ['Design Source', 'Google Stitch · NexusOps AI Command Center'],
  ['Theme', 'Enterprise dark command center'],
]

export default function Settings() {
  return (
    <div className="space-y-6 max-w-[1200px]">
      <PageHeader
        title="Settings"
        subtitle="Runtime, design-system, and integration posture for the NexusOps AI console"
        breadcrumb={['Home', 'Settings']}
        statusChips={<Badge value="portfolio ready" variant="healthy" size="sm" dot />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader title="Runtime Configuration" icon={<ServerCog className="w-3.5 h-3.5" />} />
          <div className="divide-y divide-white/[0.05]">
            {settings.map(([label, value]) => (
              <div key={label} className="px-5 py-4 flex items-center justify-between gap-4">
                <span className="text-xs text-gray-500">{label}</span>
                <span className="text-xs text-gray-200 font-mono text-right">{value}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title="Stitch Integration" icon={<Palette className="w-3.5 h-3.5" />} />
          <div className="p-5 space-y-4 text-sm text-gray-400">
            <p>
              The console uses a centralized design system based on the provided Stitch project inventory.
              MCP configuration is stored in <span className="font-mono text-gray-200">.mcp.json</span>.
            </p>
            <div className="rounded-lg border border-white/[0.06] bg-surface-200/70 p-4 space-y-2">
              <Row label="Project ID" value="17469866534806598593" />
              <Row label="Artifact Path" value="docs/design/stitch" />
              <Row label="Screens" value="8 references" />
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="Security Posture" icon={<ShieldCheck className="w-3.5 h-3.5" />} />
          <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {['JWT authentication', 'OPA policy hooks', 'OpenTelemetry traces', 'Demo-safe AI fallback'].map((item) => (
              <div key={item} className="flex items-center gap-2 rounded-lg bg-white/[0.03] border border-white/[0.06] px-3 py-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-xs text-gray-300">{item}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title="Credentials" icon={<KeyRound className="w-3.5 h-3.5" />} />
          <div className="p-5 text-sm text-gray-400 space-y-3">
            <p>Production environments should provide real values through platform secrets:</p>
            <div className="flex flex-wrap gap-2">
              {['DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY', 'OPENAI_API_KEY', 'STITCH_API_KEY'].map((key) => (
                <Badge key={key} value={key} variant="info" size="xs" />
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 text-xs">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-200 font-mono">{value}</span>
    </div>
  )
}
