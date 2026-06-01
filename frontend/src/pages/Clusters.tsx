import { useEffect, useMemo, useState } from 'react'
import type { ElementType } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity,
  Box,
  Cpu,
  GitBranch,
  Layers,
  MemoryStick,
  Network,
  RefreshCw,
  Search,
  Server,
  Workflow,
} from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import StatusDot from '@/components/ui/StatusDot'
import ProgressBar from '@/components/ui/ProgressBar'
import {
  clustersApi,
  demoApi,
  type Cluster,
  type ClusterNode,
  type ClusterTopology,
  type Deployment,
  type KubernetesService,
  type Namespace,
  type Pod,
  type TopologyNode,
} from '@/services/clusters'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

function statusFromCluster(status: string) {
  if (status === 'connected') return 'healthy'
  if (status === 'degraded') return 'degraded'
  if (status === 'disconnected') return 'critical'
  return 'unknown'
}

function ClusterCard({
  cluster,
  active,
  onSelect,
}: {
  cluster: Cluster
  active: boolean
  onSelect: () => void
}) {
  const health = statusFromCluster(cluster.status)
  return (
    <Card
      hover
      onClick={onSelect}
      className={clsx('p-5 border-l-2', active ? 'border-l-brand-500 bg-brand-500/5' : 'border-l-transparent')}
    >
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <StatusDot status={health} />
            <h3 className="text-sm font-semibold text-gray-100 truncate font-mono">{cluster.name}</h3>
          </div>
          <p className="text-xs text-gray-600 truncate">{cluster.display_name}</p>
        </div>
        <Badge value={cluster.provider} size="xs" />
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <Metric label="Nodes" value={cluster.node_count} />
        <Metric label="Pods" value={cluster.pod_count} />
        <Metric label="Deploy" value={cluster.deployment_count} />
      </div>

      <div className="space-y-2">
        <Usage label="CPU" icon={Cpu} value={Math.min(100, Math.round(((cluster.cpu_capacity ?? 0) / Math.max(cluster.node_count * 4, 1)) * 55))} />
        <Usage label="Memory" icon={MemoryStick} value={Math.min(100, Math.round(((cluster.memory_capacity_gb ?? 0) / Math.max(cluster.node_count * 16, 1)) * 60))} />
      </div>

      <div className="flex flex-wrap items-center gap-2 mt-4 text-[10px] text-gray-600">
        <span>{cluster.region ?? 'unknown-region'}</span>
        <span>·</span>
        <span>{cluster.environment}</span>
        <span>·</span>
        <span>{cluster.last_sync_at ? formatDistanceToNow(new Date(cluster.last_sync_at), { addSuffix: true }) : 'never synced'}</span>
      </div>
    </Card>
  )
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <p className="text-[10px] text-gray-600 font-medium uppercase tracking-wide mb-1">{label}</p>
      <p className="text-lg font-bold text-gray-100 tabular-nums">{value}</p>
    </div>
  )
}

function Usage({ label, icon: Icon, value }: { label: string; icon: ElementType; value: number }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] text-gray-600 flex items-center gap-1"><Icon className="w-2.5 h-2.5" /> {label}</span>
        <span className="text-[10px] font-mono text-gray-400">{value}%</span>
      </div>
      <ProgressBar value={value} height="xs" />
    </div>
  )
}

function TopologyTree({ node, depth = 0 }: { node: TopologyNode; depth?: number }) {
  const icon = node.type === 'cluster' ? Server : node.type === 'namespace' ? Layers : node.type === 'service' ? Network : node.type === 'pod' ? Box : Workflow
  const Icon = icon
  return (
    <div>
      <div className="flex items-center gap-2 py-1.5 text-xs" style={{ paddingLeft: depth * 18 }}>
        <Icon className="w-3.5 h-3.5 text-brand-400 flex-shrink-0" />
        <span className="text-gray-200 font-medium font-mono">{node.name}</span>
        <Badge value={node.type} size="xs" />
        {node.status && <span className="text-gray-600 truncate">{node.status}</span>}
      </div>
      {node.children.map((child) => (
        <TopologyTree key={child.id} node={child} depth={depth + 1} />
      ))}
    </div>
  )
}

function ResourceTable({
  namespaces,
  deployments,
  pods,
  services,
  nodes,
}: {
  namespaces: Namespace[]
  deployments: Deployment[]
  pods: Pod[]
  services: KubernetesService[]
  nodes: ClusterNode[]
}) {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <Card>
        <CardHeader title="Deployments" subtitle={`${deployments.length} discovered`} icon={<Workflow className="w-3.5 h-3.5" />} />
        <div className="divide-y divide-white/[0.04]">
          {deployments.slice(0, 8).map((deployment) => (
            <div key={deployment.id} className="px-5 py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs text-gray-200 font-medium font-mono truncate">{deployment.name}</p>
                <p className="text-[10px] text-gray-600">{deployment.namespace_name} · {deployment.image ?? 'image unknown'}</p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-xs font-mono text-gray-400">{deployment.replicas_ready}/{deployment.replicas_desired}</span>
                <StatusDot status={deployment.is_healthy ? 'healthy' : 'degraded'} />
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader title="Pods" subtitle={`${pods.length} running objects`} icon={<Box className="w-3.5 h-3.5" />} />
        <div className="divide-y divide-white/[0.04]">
          {pods.slice(0, 8).map((pod) => (
            <div key={pod.id} className="px-5 py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs text-gray-200 font-medium font-mono truncate">{pod.name}</p>
                <p className="text-[10px] text-gray-600">{pod.namespace_name} · {pod.node_name ?? 'unscheduled'}</p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {pod.restart_count > 0 && <span className="text-[10px] text-amber-400">{pod.restart_count} restarts</span>}
                <Badge value={pod.status} size="xs" />
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader title="Services" subtitle={`${services.length} network front doors`} icon={<Network className="w-3.5 h-3.5" />} />
        <div className="divide-y divide-white/[0.04]">
          {services.slice(0, 8).map((service) => (
            <div key={service.id} className="px-5 py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs text-gray-200 font-medium font-mono truncate">{service.name}</p>
                <p className="text-[10px] text-gray-600">{service.namespace_name} · {service.cluster_ip ?? 'no cluster IP'}</p>
              </div>
              <Badge value={service.service_type} size="xs" />
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader title="Namespaces & Nodes" subtitle={`${namespaces.length} namespaces · ${nodes.length} nodes`} icon={<Server className="w-3.5 h-3.5" />} />
        <div className="p-5 grid grid-cols-2 gap-4">
          <div className="space-y-2">
            {namespaces.map((namespace) => (
              <div key={namespace.id} className="flex items-center gap-2 text-xs">
                <Layers className="w-3 h-3 text-brand-400" />
                <span className="text-gray-300 font-mono truncate">{namespace.name}</span>
              </div>
            ))}
          </div>
          <div className="space-y-2">
            {nodes.map((node) => (
              <div key={node.id} className="flex items-center justify-between gap-2 text-xs">
                <span className="text-gray-300 font-mono truncate">{node.name}</span>
                <StatusDot status={node.status === 'Ready' ? 'healthy' : 'degraded'} />
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  )
}

export default function Clusters() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const clustersQuery = useQuery({
    queryKey: ['clusters'],
    queryFn: () => clustersApi.list({ page_size: 100, active_only: true }),
  })

  const clusters = clustersQuery.data?.items ?? []
  useEffect(() => {
    if (!selectedId && clusters.length > 0) setSelectedId(clusters[0].id)
  }, [clusters, selectedId])

  const selectedCluster = clusters.find((cluster) => cluster.id === selectedId) ?? clusters[0]
  const selectedClusterId = selectedCluster?.id

  const nodesQuery = useQuery({ queryKey: ['cluster-nodes', selectedClusterId], queryFn: () => clustersApi.nodes(selectedClusterId!), enabled: !!selectedClusterId })
  const namespacesQuery = useQuery({ queryKey: ['cluster-namespaces', selectedClusterId], queryFn: () => clustersApi.namespaces(selectedClusterId!), enabled: !!selectedClusterId })
  const deploymentsQuery = useQuery({ queryKey: ['cluster-deployments', selectedClusterId], queryFn: () => clustersApi.deployments(selectedClusterId!), enabled: !!selectedClusterId })
  const podsQuery = useQuery({ queryKey: ['cluster-pods', selectedClusterId], queryFn: () => clustersApi.pods(selectedClusterId!), enabled: !!selectedClusterId })
  const servicesQuery = useQuery({ queryKey: ['cluster-services', selectedClusterId], queryFn: () => clustersApi.services(selectedClusterId!), enabled: !!selectedClusterId })
  const topologyQuery = useQuery<ClusterTopology>({ queryKey: ['cluster-topology', selectedClusterId], queryFn: () => clustersApi.topology(selectedClusterId!), enabled: !!selectedClusterId })

  const generateDemo = useMutation({
    mutationFn: demoApi.generate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
    },
  })

  const syncCluster = useMutation({
    mutationFn: (id: string) => clustersApi.sync(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      queryClient.invalidateQueries({ queryKey: ['cluster-topology', id] })
    },
  })

  const filtered = useMemo(
    () =>
      clusters.filter((cluster) =>
        !search ||
        cluster.name.toLowerCase().includes(search.toLowerCase()) ||
        cluster.display_name.toLowerCase().includes(search.toLowerCase()) ||
        cluster.provider.toLowerCase().includes(search.toLowerCase()),
      ),
    [clusters, search],
  )

  const nodes = nodesQuery.data ?? []
  const namespaces = namespacesQuery.data ?? []
  const deployments = deploymentsQuery.data ?? []
  const pods = podsQuery.data ?? []
  const services = servicesQuery.data ?? []

  const healthyClusters = clusters.filter((cluster) => cluster.status === 'connected').length
  const degradedPods = pods.filter((pod) => !pod.ready || pod.restart_count > 0).length

  return (
    <div className="space-y-6 max-w-[1600px]">
      <PageHeader
        title="Infrastructure"
        subtitle="Provider-backed Kubernetes discovery, ingestion, and topology"
        breadcrumb={['Home', 'Infrastructure']}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => generateDemo.mutate()}
              disabled={generateDemo.isPending}
              className="btn-secondary text-xs py-2 px-4 flex items-center gap-2"
            >
              <GitBranch className="w-3.5 h-3.5" /> {generateDemo.isPending ? 'Generating…' : 'Generate Demo'}
            </button>
            {selectedClusterId && (
              <button
                onClick={() => syncCluster.mutate(selectedClusterId)}
                disabled={syncCluster.isPending}
                className="btn-primary text-xs py-2 px-4 flex items-center gap-2"
              >
                <RefreshCw className={clsx('w-3.5 h-3.5', syncCluster.isPending && 'animate-spin')} /> Sync Cluster
              </button>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Clusters', value: clusters.length, sub: `${healthyClusters} connected`, icon: Server, color: 'text-brand-400' },
          { label: 'Namespaces', value: namespaces.length, sub: selectedCluster?.name ?? 'select cluster', icon: Layers, color: 'text-sky-400' },
          { label: 'Deployments', value: deployments.length, sub: `${deployments.filter((d) => !d.is_healthy).length} degraded`, icon: Workflow, color: 'text-emerald-400' },
          { label: 'Pods', value: pods.length, sub: `${degradedPods} need attention`, icon: Box, color: degradedPods > 0 ? 'text-amber-400' : 'text-emerald-400' },
        ].map(({ label, value, sub, icon: Icon, color }) => (
          <Card key={label} className="p-5">
            <div className="flex items-center gap-2 mb-2">
              <Icon className={clsx('w-4 h-4', color)} />
              <span className="text-xs text-gray-500 font-medium">{label}</span>
            </div>
            <p className={clsx('text-3xl font-bold tabular-nums', color)}>{value}</p>
            <p className="text-xs text-gray-600 mt-0.5">{sub}</p>
          </Card>
        ))}
      </div>

      {clustersQuery.isError && (
        <Card className="p-5 border-red-500/20 bg-red-500/5">
          <p className="text-sm text-red-300">Unable to load infrastructure data. Confirm the backend is running and your session is authenticated.</p>
        </Card>
      )}

      {!clustersQuery.isLoading && clusters.length === 0 && (
        <Card className="p-8 text-center">
          <Activity className="w-10 h-10 text-brand-400 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-gray-100">No infrastructure has been ingested yet</h3>
          <p className="text-sm text-gray-500 mt-1">Generate the demo environment or register and sync a Kubernetes cluster.</p>
          <button onClick={() => generateDemo.mutate()} className="btn-primary mt-5 text-xs">
            Generate Demo Infrastructure
          </button>
        </Card>
      )}

      {clusters.length > 0 && (
        <>
          <div className="flex items-center gap-3 flex-wrap">
            <div className="relative flex-1 min-w-[220px] max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600 pointer-events-none" />
              <input
                type="text"
                placeholder="Filter clusters…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="input pl-9 text-xs py-2"
              />
            </div>
            <span className="text-xs text-gray-600 ml-auto">{filtered.length} clusters</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filtered.map((cluster) => (
              <ClusterCard
                key={cluster.id}
                cluster={cluster}
                active={cluster.id === selectedClusterId}
                onSelect={() => setSelectedId(cluster.id)}
              />
            ))}
          </div>

          {selectedCluster && (
            <div className="grid grid-cols-1 2xl:grid-cols-3 gap-4">
              <div className="2xl:col-span-2">
                <ResourceTable
                  namespaces={namespaces}
                  deployments={deployments}
                  pods={pods}
                  services={services}
                  nodes={nodes}
                />
              </div>
              <Card>
                <CardHeader title="Topology" subtitle="Cluster → Namespace → Deployment → Pod" icon={<GitBranch className="w-3.5 h-3.5" />} />
                <div className="p-4 max-h-[720px] overflow-y-auto">
                  {topologyQuery.data ? (
                    <TopologyTree node={topologyQuery.data.root} />
                  ) : (
                    <p className="text-sm text-gray-500">Topology will appear after this cluster is synced.</p>
                  )}
                </div>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  )
}
