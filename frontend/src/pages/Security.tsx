import { useQuery } from '@tanstack/react-query'
import { Shield, Upload } from 'lucide-react'
import { api } from '@/services/api'
import StatusBadge from '@/components/StatusBadge'
import StatCard from '@/components/StatCard'

export default function Security() {
  const { data: stats } = useQuery({
    queryKey: ['security-dashboard'],
    queryFn: () => api.get('/security/dashboard').then((r) => r.data),
  })

  const { data: findings, isLoading } = useQuery({
    queryKey: ['security-findings'],
    queryFn: () => api.get('/security/findings?page_size=30').then((r) => r.data),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-100">Security</h1>
          <p className="text-sm text-gray-500 mt-0.5">Vulnerability management & Terraform drift analysis</p>
        </div>
        <button className="btn-primary">
          <Upload className="w-4 h-4" />
          Scan Terraform
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Critical" value={stats?.critical_findings ?? '—'} color="red" />
        <StatCard label="High" value={stats?.high_findings ?? '—'} color="yellow" />
        <StatCard label="Open" value={stats?.open_findings ?? '—'} color="red" />
        <StatCard label="Remediated" value={stats?.remediated_findings ?? '—'} color="green" />
      </div>

      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-700/50 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-300">Security Findings</h2>
          <span className="text-xs text-gray-500">{findings?.total ?? 0} total</span>
        </div>

        {isLoading ? (
          <div className="p-10 text-center text-gray-500">Loading…</div>
        ) : (
          <div className="divide-y divide-gray-700/30">
            {findings?.items?.map((finding: Record<string, unknown>) => (
              <div key={String(finding.id)} className="px-5 py-4 hover:bg-surface-200/50">
                <div className="flex items-start gap-3">
                  <Shield className="w-4 h-4 mt-0.5 text-orange-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-gray-100">{String(finding.title ?? '')}</p>
                      <StatusBadge value={String(finding.severity ?? '')} />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {String(finding.category ?? '')}
                      {finding.cve_id && ` · ${String(finding.cve_id)}`}
                    </p>
                    {finding.ai_explanation && (
                      <p className="text-xs text-gray-400 mt-1.5 line-clamp-2">{String(finding.ai_explanation)}</p>
                    )}
                  </div>
                  <StatusBadge value={String(finding.status ?? '')} />
                </div>
              </div>
            ))}
            {!findings?.items?.length && (
              <div className="p-12 text-center text-gray-500">No security findings</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
