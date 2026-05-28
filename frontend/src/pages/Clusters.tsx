import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Server, RefreshCw, Plus, Trash2, ExternalLink } from 'lucide-react'
import StatusBadge from '@/components/StatusBadge'
import { clustersApi, type Cluster } from '@/services/clusters'

export default function Clusters() {
  const qc = useQueryClient()
  const [syncingId, setSyncingId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['clusters'],
    queryFn: () => clustersApi.list(),
  })

  const syncMutation = useMutation({
    mutationFn: (id: string) => clustersApi.sync(id),
    onMutate: (id) => setSyncingId(id),
    onSettled: () => {
      setSyncingId(null)
      qc.invalidateQueries({ queryKey: ['clusters'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => clustersApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clusters'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-100">Kubernetes Clusters</h1>
          <p className="text-sm text-gray-500 mt-0.5">Manage and monitor registered clusters</p>
        </div>
        <button className="btn-primary">
          <Plus className="w-4 h-4" />
          Register Cluster
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-20 text-gray-500">Loading clusters…</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {data?.items.map((cluster: Cluster) => (
            <div key={cluster.id} className="card p-5 space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-brand-600/20 flex items-center justify-center">
                    <Server className="w-4 h-4 text-brand-400" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-100 text-sm">{cluster.display_name || cluster.name}</p>
                    <p className="text-xs text-gray-500">{cluster.provider} · {cluster.region}</p>
                  </div>
                </div>
                <StatusBadge value={cluster.status} />
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                {[
                  { label: 'Nodes', value: cluster.node_count },
                  { label: 'Pods', value: cluster.pod_count },
                  { label: 'Namespaces', value: cluster.namespace_count },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-surface-200 rounded-lg p-2">
                    <p className="text-base font-semibold text-gray-100">{value}</p>
                    <p className="text-xs text-gray-500">{label}</p>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>k8s {cluster.kubernetes_version ?? 'unknown'}</span>
                {cluster.last_sync_at && (
                  <span>synced {new Date(cluster.last_sync_at).toLocaleTimeString()}</span>
                )}
              </div>

              <div className="flex gap-2 pt-1 border-t border-gray-700/30">
                <button
                  onClick={() => syncMutation.mutate(cluster.id)}
                  disabled={syncingId === cluster.id}
                  className="btn-secondary flex-1 justify-center text-xs py-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${syncingId === cluster.id ? 'animate-spin' : ''}`} />
                  Sync
                </button>
                <button className="btn-secondary flex-1 justify-center text-xs py-1.5">
                  <ExternalLink className="w-3.5 h-3.5" />
                  Details
                </button>
                <button
                  onClick={() => confirm('Delete cluster?') && deleteMutation.mutate(cluster.id)}
                  className="btn-danger px-2.5 text-xs py-1.5"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}

          {!data?.items.length && (
            <div className="col-span-3 card p-12 text-center">
              <Server className="w-10 h-10 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No clusters registered yet</p>
              <p className="text-sm text-gray-600 mt-1">Register a Kubernetes cluster to get started</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
