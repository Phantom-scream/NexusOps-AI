import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { BrainCircuit, Send, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'
import { aiApi } from '@/services/ai'
import { clustersApi } from '@/services/clusters'
import clsx from 'clsx'

interface Finding {
  severity: string
  root_cause: string
  contributing_factors: string[]
  remediation: Record<string, string>
  confidence: number
  analysis_detail: string
  tokens_used?: number
}

export default function AIInvestigation() {
  const [selectedCluster, setSelectedCluster] = useState('')
  const [query, setQuery] = useState('')
  const [namespace, setNamespace] = useState('')
  const [result, setResult] = useState<Finding | null>(null)

  const { data: clusters } = useQuery({
    queryKey: ['clusters'],
    queryFn: () => clustersApi.list(),
  })

  const investigateMutation = useMutation({
    mutationFn: aiApi.investigate,
    onSuccess: (data) => setResult(data),
  })

  const handleInvestigate = () => {
    if (!selectedCluster || !query.trim()) return
    investigateMutation.mutate({
      cluster_id: selectedCluster,
      query: query.trim(),
      namespace: namespace || undefined,
      context_window_minutes: 60,
    })
  }

  const confidenceColor = result
    ? result.confidence >= 0.8 ? 'text-green-400'
      : result.confidence >= 0.5 ? 'text-yellow-400'
      : 'text-red-400'
    : ''

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-semibold text-gray-100 flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-brand-400" />
          AI Investigation
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Describe an infrastructure problem — NexusOps AI will investigate root cause and recommend remediation
        </p>
      </div>

      {/* Input panel */}
      <div className="card p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Cluster *</label>
            <select
              value={selectedCluster}
              onChange={(e) => setSelectedCluster(e.target.value)}
              className="input"
            >
              <option value="">Select a cluster…</option>
              {clusters?.items.map((c) => (
                <option key={c.id} value={c.id}>{c.display_name || c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Namespace (optional)</label>
            <input
              type="text"
              placeholder="e.g. production"
              value={namespace}
              onChange={(e) => setNamespace(e.target.value)}
              className="input"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5">Investigation Query *</label>
          <textarea
            rows={4}
            placeholder="Describe the problem… e.g. 'Pods in the checkout service are crash-looping with OOMKilled. CPU spikes observed at 14:30 UTC.'"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="input resize-none"
          />
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleInvestigate}
            disabled={!selectedCluster || !query.trim() || investigateMutation.isPending}
            className="btn-primary"
          >
            {investigateMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            {investigateMutation.isPending ? 'Analyzing…' : 'Investigate'}
          </button>
        </div>
      </div>

      {/* Error */}
      {investigateMutation.isError && (
        <div className="card p-4 border-red-500/30 bg-red-500/10 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <p className="text-sm text-red-300">Investigation failed. Check that the backend is running and the cluster is reachable.</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="card p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              Analysis Complete
            </h2>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <span>Confidence: <span className={clsx('font-semibold', confidenceColor)}>{(result.confidence * 100).toFixed(0)}%</span></span>
              {result.tokens_used && <span>Tokens: {result.tokens_used}</span>}
            </div>
          </div>

          <div className="space-y-1">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Root Cause</p>
            <p className="text-sm text-gray-100 leading-relaxed">{result.root_cause}</p>
          </div>

          {result.contributing_factors?.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Contributing Factors</p>
              <ul className="space-y-1.5">
                {result.contributing_factors.map((factor, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-300">
                    <span className="text-brand-400 mt-0.5">•</span>
                    {factor}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.analysis_detail && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Analysis Detail</p>
              <p className="text-sm text-gray-400 leading-relaxed">{result.analysis_detail}</p>
            </div>
          )}

          {Object.keys(result.remediation ?? {}).length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Remediation Steps</p>
              <div className="space-y-2">
                {Object.entries(result.remediation).map(([key, value]) => (
                  <div key={key} className="bg-surface-200 rounded-lg p-3">
                    <p className="text-xs font-medium text-brand-300 mb-1 capitalize">{key.replace(/_/g, ' ')}</p>
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">{value}</pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
