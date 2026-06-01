import { useMemo, useState, type ElementType } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  AlertTriangle,
  Bot,
  Brain,
  CheckCircle2,
  Database,
  FileText,
  GitBranch,
  Loader2,
  Play,
  RefreshCw,
  Sparkles,
  Wrench,
} from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import ProgressBar from '@/components/ui/ProgressBar'
import { incidentsApi, type Incident } from '@/services/incidents'
import { investigationsApi, type Investigation, type InvestigationEvidence, type Recommendation } from '@/services/investigations'
import clsx from 'clsx'

const investigationPrompts = [
  'Investigate this incident using topology, metrics, logs, events, and traces. Identify the most probable root cause and immediate remediation.',
  'Determine whether this incident is caused by a recent deployment, resource exhaustion, or downstream dependency failure.',
  'Correlate pod restarts, high latency traces, and Kubernetes events to produce a production-ready RCA.',
]

function severityVariant(value?: string) {
  if (value === 'critical' || value === 'error') return 'critical'
  if (value === 'high') return 'high'
  if (value === 'medium' || value === 'warning' || value === 'warn') return 'medium'
  if (value === 'low') return 'low'
  return 'info'
}

export default function AIInvestigation() {
  const queryClient = useQueryClient()
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('')
  const [selectedInvestigationId, setSelectedInvestigationId] = useState<string>('')
  const [query, setQuery] = useState(investigationPrompts[0])

  const incidentsQuery = useQuery({
    queryKey: ['ai-incidents'],
    queryFn: () => incidentsApi.list({ page_size: 50 }),
  })
  const investigationsQuery = useQuery({
    queryKey: ['investigations'],
    queryFn: () => investigationsApi.list({ page_size: 50 }),
  })
  const selectedInvestigationQuery = useQuery({
    queryKey: ['investigation', selectedInvestigationId],
    queryFn: () => investigationsApi.get(selectedInvestigationId),
    enabled: Boolean(selectedInvestigationId),
  })
  const evidenceQuery = useQuery({
    queryKey: ['investigation-evidence', selectedInvestigationId],
    queryFn: () => investigationsApi.evidence(selectedInvestigationId),
    enabled: Boolean(selectedInvestigationId),
  })

  const incidents = incidentsQuery.data?.items ?? []
  const investigations = investigationsQuery.data?.items ?? []
  const selectedIncident = useMemo(
    () => incidents.find((incident) => incident.id === selectedIncidentId) ?? incidents[0],
    [incidents, selectedIncidentId],
  )
  const selectedInvestigation = selectedInvestigationQuery.data ?? investigations.find((item) => item.id === selectedInvestigationId) ?? investigations[0]
  const evidence = evidenceQuery.data ?? []

  const createInvestigation = useMutation({
    mutationFn: () =>
      investigationsApi.create({
        incident_id: selectedIncident?.id,
        cluster_id: selectedIncident?.cluster_id,
        title: selectedIncident ? `RCA: ${selectedIncident.title}` : 'Ad-hoc AI Investigation',
        query,
        run_immediately: true,
      }),
    onSuccess: (investigation) => {
      setSelectedInvestigationId(investigation.id)
      queryClient.invalidateQueries({ queryKey: ['investigations'] })
      queryClient.invalidateQueries({ queryKey: ['ai-incidents'] })
      queryClient.invalidateQueries({ queryKey: ['investigation-evidence', investigation.id] })
    },
  })

  const rerunInvestigation = useMutation({
    mutationFn: (id: string) => investigationsApi.run(id),
    onSuccess: ({ investigation }) => {
      setSelectedInvestigationId(investigation.id)
      queryClient.invalidateQueries({ queryKey: ['investigations'] })
      queryClient.invalidateQueries({ queryKey: ['investigation', investigation.id] })
      queryClient.invalidateQueries({ queryKey: ['investigation-evidence', investigation.id] })
    },
  })

  const generateDemo = useMutation({
    mutationFn: investigationsApi.generateDemoIncidents,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-incidents'] })
      queryClient.invalidateQueries({ queryKey: ['investigations'] })
    },
  })

  const isRunning = createInvestigation.isPending || rerunInvestigation.isPending

  return (
    <div className="space-y-5 max-w-[1600px]">
      <PageHeader
        title="AI Investigation"
        subtitle="Root cause analysis generated from topology, telemetry, traces, events, logs, and incident history"
        breadcrumb={['Home', 'AI Investigation']}
        actions={
          <button
            onClick={() => generateDemo.mutate()}
            disabled={generateDemo.isPending}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-2"
          >
            <RefreshCw className={clsx('w-3.5 h-3.5', generateDemo.isPending && 'animate-spin')} />
            Generate Demo Incidents
          </button>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-[360px_minmax(0,1fr)] gap-4">
        <div className="space-y-4">
          <Card>
            <CardHeader title="Incident Queue" subtitle={`${incidents.length} available`} icon={<AlertTriangle className="w-3.5 h-3.5" />} />
            <div className="max-h-[390px] overflow-y-auto divide-y divide-white/[0.04]">
              {incidents.map((incident) => (
                <button
                  key={incident.id}
                  onClick={() => {
                    setSelectedIncidentId(incident.id)
                    setQuery(investigationPrompts[0])
                  }}
                  className={clsx(
                    'w-full text-left px-4 py-3 hover:bg-white/[0.03] transition-colors',
                    selectedIncident?.id === incident.id && 'bg-brand-500/10',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <Badge value={incident.severity} variant={severityVariant(incident.severity)} dot size="xs" />
                    <span className="text-[10px] text-gray-600">{incident.status}</span>
                  </div>
                  <p className="text-sm text-gray-200 mt-2 line-clamp-2">{incident.title}</p>
                  <p className="text-[10px] text-gray-600 mt-1 font-mono truncate">
                    {incident.namespace ?? 'all'} / {incident.affected_workload ?? incident.cluster_name ?? incident.cluster_id}
                  </p>
                </button>
              ))}
              {!incidents.length && (
                <div className="px-4 py-8 text-center text-sm text-gray-500">
                  No incidents yet. Generate demo incidents to try the RCA workflow.
                </div>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Investigation History" subtitle={`${investigations.length} runs`} icon={<FileText className="w-3.5 h-3.5" />} />
            <div className="max-h-[360px] overflow-y-auto divide-y divide-white/[0.04]">
              {investigations.map((investigation) => (
                <button
                  key={investigation.id}
                  onClick={() => setSelectedInvestigationId(investigation.id)}
                  className={clsx(
                    'w-full text-left px-4 py-3 hover:bg-white/[0.03] transition-colors',
                    selectedInvestigation?.id === investigation.id && 'bg-brand-500/10',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <Badge value={investigation.severity} variant={severityVariant(investigation.severity)} dot size="xs" />
                    <span className="text-[10px] text-gray-600">{investigation.status}</span>
                  </div>
                  <p className="text-sm text-gray-200 mt-2 line-clamp-2">{investigation.title}</p>
                  <p className="text-[10px] text-gray-600 mt-1">
                    {investigation.confidence_score ? `${Math.round(investigation.confidence_score * 100)}% confidence` : 'Not analyzed'}
                  </p>
                </button>
              ))}
              {!investigations.length && (
                <div className="px-4 py-8 text-center text-sm text-gray-500">No investigation history yet.</div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Investigation Runbook"
              subtitle={selectedIncident ? selectedIncident.title : 'Select an incident or run ad-hoc'}
              icon={<Brain className="w-3.5 h-3.5" />}
              actions={
                <button
                  onClick={() => createInvestigation.mutate()}
                  disabled={!query.trim() || isRunning}
                  className="btn-primary text-xs py-2 px-3 flex items-center gap-2 disabled:opacity-50"
                >
                  {isRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  Run Investigation
                </button>
              }
            />
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {investigationPrompts.map((prompt, index) => (
                  <button
                    key={prompt}
                    onClick={() => setQuery(prompt)}
                    className="text-left rounded-lg border border-white/[0.06] bg-surface-200 p-3 text-xs text-gray-400 hover:border-brand-500/30 hover:text-gray-200"
                  >
                    <span className="text-brand-400 font-medium">Prompt {index + 1}</span>
                    <span className="block mt-1 line-clamp-3">{prompt}</span>
                  </button>
                ))}
              </div>
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                rows={4}
                className="w-full rounded-xl border border-white/[0.06] bg-surface-200 px-4 py-3 text-sm text-gray-200 outline-none focus:border-brand-500/40"
                placeholder="Describe what the AI should investigate..."
              />
            </div>
          </Card>

          {selectedInvestigation ? (
            <InvestigationResult
              investigation={selectedInvestigation}
              evidence={evidence}
              onRerun={() => rerunInvestigation.mutate(selectedInvestigation.id)}
              rerunning={rerunInvestigation.isPending}
            />
          ) : (
            <Card className="p-10 text-center">
              <Sparkles className="w-10 h-10 mx-auto text-brand-400/70 mb-3" />
              <h3 className="text-lg font-semibold text-gray-100">Ready for AI-assisted operations</h3>
              <p className="text-sm text-gray-500 max-w-2xl mx-auto mt-1">
                Generate demo incidents or select an existing incident, then run an investigation to collect evidence and produce a structured RCA.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

function InvestigationResult({
  investigation,
  evidence,
  onRerun,
  rerunning,
}: {
  investigation: Investigation
  evidence: InvestigationEvidence[]
  onRerun: () => void
  rerunning: boolean
}) {
  const confidence = Math.round((investigation.confidence_score ?? 0) * 100)
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <MetricCard icon={CheckCircle2} label="Status" value={investigation.status} color="text-emerald-400" />
        <MetricCard icon={AlertTriangle} label="Severity" value={investigation.severity} color="text-red-400" />
        <MetricCard icon={Bot} label="Provider" value={investigation.llm_provider ?? 'pending'} color="text-brand-400" />
        <Card className="p-4">
          <p className="text-xs text-gray-500">Confidence</p>
          <p className="text-2xl font-bold text-gray-50 mt-1">{confidence}%</p>
          <ProgressBar value={confidence} className="mt-3" />
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Root Cause Analysis"
          subtitle={investigation.llm_model ?? 'NexusOps investigation engine'}
          icon={<Brain className="w-3.5 h-3.5" />}
          actions={
            <button onClick={onRerun} disabled={rerunning} className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
              <RefreshCw className={clsx('w-3 h-3', rerunning && 'animate-spin')} />
              Rerun
            </button>
          }
        />
        <div className="p-5 space-y-4">
          <section>
            <p className="text-xs uppercase tracking-wide text-gray-600 mb-2">Summary</p>
            <p className="text-sm text-gray-300 leading-relaxed">{investigation.summary ?? 'No summary generated yet.'}</p>
          </section>
          <section>
            <p className="text-xs uppercase tracking-wide text-gray-600 mb-2">Probable Root Cause</p>
            <p className="text-base text-gray-100 leading-relaxed">{investigation.root_cause ?? 'Analysis pending.'}</p>
          </section>
          {investigation.root_cause_detail && (
            <section>
              <p className="text-xs uppercase tracking-wide text-gray-600 mb-2">Technical Detail</p>
              <p className="text-sm text-gray-400 leading-relaxed">{investigation.root_cause_detail}</p>
            </section>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card>
          <CardHeader title="Supporting Evidence" subtitle={`${evidence.length} collected signals`} icon={<Database className="w-3.5 h-3.5" />} />
          <div className="divide-y divide-white/[0.04] max-h-[430px] overflow-y-auto">
            {evidence.slice(0, 12).map((item) => (
              <div key={item.id} className="px-5 py-3">
                <div className="flex items-center justify-between gap-2">
                  <Badge value={item.severity} variant={severityVariant(item.severity)} dot size="xs" />
                  <span className="text-[10px] text-gray-600 uppercase">{item.evidence_type}</span>
                </div>
                <p className="text-sm text-gray-200 mt-2">{item.title}</p>
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{item.description}</p>
                <p className="text-[10px] text-gray-700 mt-1 font-mono truncate">
                  {item.namespace_name ?? 'cluster'} / {item.resource_name ?? item.source_type}
                </p>
              </div>
            ))}
            {!evidence.length && <div className="px-5 py-8 text-center text-sm text-gray-500">Evidence will appear after the investigation runs.</div>}
          </div>
        </Card>

        <Card>
          <CardHeader title="Remediation" subtitle="Recommended actions" icon={<Wrench className="w-3.5 h-3.5" />} />
          <div className="divide-y divide-white/[0.04]">
            {(investigation.remediation_recommendations ?? []).map((item: Recommendation, index) => (
              <div key={`${item.title}-${index}`} className="px-5 py-4">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded bg-brand-500/15 text-brand-300 text-xs flex items-center justify-center">
                    {item.priority ?? index + 1}
                  </span>
                  <p className="text-sm font-medium text-gray-100">{item.title}</p>
                </div>
                <p className="text-xs text-gray-500 mt-2">{item.description}</p>
                {item.command && (
                  <pre className="mt-3 overflow-x-auto rounded-lg bg-black/30 border border-white/[0.05] px-3 py-2 text-[11px] text-gray-300">
                    {item.command}
                  </pre>
                )}
              </div>
            ))}
            {!investigation.remediation_recommendations?.length && (
              <div className="px-5 py-8 text-center text-sm text-gray-500">No remediation generated yet.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, color }: { icon: ElementType; label: string; value: string; color: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-500">{label}</p>
          <Icon className={clsx('w-4 h-4', color)} />
        </div>
        <p className="text-xl font-semibold text-gray-100 mt-2 capitalize truncate">{value}</p>
      </Card>
    </motion.div>
  )
}
