import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send,
  Bot,
  User,
  Sparkles,
  RefreshCw,
  Copy,
  Check,
  Zap,
  Shield,
  Server,
  AlertTriangle,
  DollarSign,
  ChevronRight,
} from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import { Card, CardHeader } from '@/components/ui/Card'
import type { AIMessage } from '@/types'
import clsx from 'clsx'

const suggestedPrompts = [
  { icon: Server, label: 'Cluster Health', prompt: 'Analyze the current health of prod-us-east-1 cluster and identify any performance bottlenecks.' },
  { icon: AlertTriangle, label: 'Incident RCA', prompt: 'Investigate the API gateway latency spike detected 2 hours ago and provide root cause analysis.' },
  { icon: Shield, label: 'Security Audit', prompt: 'Perform a security audit of our Kubernetes configurations and identify critical misconfigurations.' },
  { icon: DollarSign, label: 'Cost Analysis', prompt: 'Analyze our current cloud spend and suggest the top 3 cost optimization opportunities.' },
  { icon: Zap, label: 'Performance', prompt: 'Review pod resource requests/limits across all production clusters and recommend optimizations.' },
  { icon: RefreshCw, label: 'Deployment Check', prompt: 'Check the status of recent deployments and flag any that may be causing instability.' },
]

const INITIAL_MESSAGES: AIMessage[] = [
  {
    id: 'welcome',
    role: 'assistant',
    content: `Hello! I'm the NexusOps AI assistant. I can help you investigate infrastructure issues, analyze security findings, optimize costs, and provide insights across your entire cloud environment.

Here are some things I can help with:
- **Root cause analysis** for incidents and alerts
- **Security vulnerability** assessment and remediation guidance
- **Cost optimization** recommendations
- **Cluster health** analysis and capacity planning
- **Deployment risk** assessment

What would you like to investigate today?`,
    timestamp: new Date(Date.now() - 5000).toISOString(),
  },
]

function MessageBubble({ msg, onCopy }: { msg: AIMessage; onCopy: (text: string) => void }) {
  const isAssistant = msg.role === 'assistant'
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    onCopy(msg.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={clsx('flex items-start gap-3', !isAssistant && 'flex-row-reverse')}
    >
      {/* Avatar */}
      <div className={clsx(
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5',
        isAssistant ? 'bg-brand-500/20 text-brand-300' : 'bg-surface-300 text-gray-300',
      )}>
        {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
      </div>

      {/* Bubble */}
      <div className={clsx('max-w-[80%] group', !isAssistant && 'items-end flex flex-col')}>
        <div className={clsx(
          'rounded-xl px-4 py-3 text-sm leading-relaxed',
          isAssistant
            ? 'bg-surface-200 border border-white/[0.05] text-gray-200'
            : 'bg-brand-600 text-white',
        )}>
          {isAssistant ? (
            <div className="prose prose-invert prose-sm max-w-none">
              {msg.content.split('\n').map((line, i) => {
                if (line.startsWith('**') && line.endsWith('**')) {
                  return <p key={i} className="font-semibold text-gray-100 mt-2 mb-0.5">{line.replace(/\*\*/g, '')}</p>
                }
                if (line.startsWith('- ')) {
                  return <p key={i} className="flex items-start gap-1.5 text-gray-300 my-0.5"><ChevronRight className="w-3 h-3 mt-0.5 text-brand-400 flex-shrink-0" />{line.slice(2)}</p>
                }
                if (line === '') return <div key={i} className="h-1" />
                return <p key={i} className="text-gray-300">{line}</p>
              })}
            </div>
          ) : (
            <p>{msg.content}</p>
          )}
        </div>

        <div className={clsx('flex items-center gap-2 mt-1', !isAssistant && 'flex-row-reverse')}>
          <span className="text-[10px] text-gray-700">
            {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          {isAssistant && (
            <button
              onClick={handleCopy}
              className="p-1 rounded hover:bg-surface-300 text-gray-700 hover:text-gray-400 transition-colors opacity-0 group-hover:opacity-100"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function ThinkingIndicator() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-brand-500/20 text-brand-300 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4" />
      </div>
      <div className="bg-surface-200 border border-white/[0.05] rounded-xl px-4 py-3">
        <div className="flex items-center gap-1.5">
          {[0, 1, 2].map(i => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 bg-brand-400 rounded-full"
              animate={{ y: [0, -4, 0] }}
              transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  )
}

// Simulated AI response generator
function generateResponse(userMessage: string): string {
  const lower = userMessage.toLowerCase()
  if (lower.includes('health') || lower.includes('cluster')) {
    return `**Cluster Health Analysis Complete**

After analyzing the prod-us-east-1 cluster, I found the following:

**Current Status:** Degraded (2 of 12 nodes under pressure)

**Identified Issues:**
- Node ip-10-0-45-123 is at 94% memory utilization — approaching OOM threshold
- 3 pods in the \`payments\` namespace have been restarting (CrashLoopBackOff) for 45 minutes
- etcd latency is elevated at 12ms (normal: <5ms), suggesting disk I/O contention

**Recommendations:**
- Immediately drain node ip-10-0-45-123 and reschedule workloads
- Investigate the payments pods — likely memory leak in payments-processor v2.1.4
- Check etcd disk IOPS and consider migrating to GP3 volumes

Estimated resolution time: 20-30 minutes if action is taken now.`
  }
  if (lower.includes('incident') || lower.includes('latency') || lower.includes('rca')) {
    return `**Root Cause Analysis — API Gateway Latency Spike**

**Timeline Reconstruction:**
- 14:23 UTC: Latency began climbing from baseline 45ms → 340ms
- 14:31 UTC: Error rate crossed 1% threshold, PagerDuty alert triggered
- 14:45 UTC: Latency peaked at 1.2s P99

**Root Cause Identified:**
The spike correlates precisely with deployment \`api-gateway:v3.2.1\` pushed at 14:22 UTC. The new version introduced a synchronous database call in the request path that was previously async.

**Affected Services:** api-gateway, auth-service, user-service

**Immediate Action:**
\`\`\`
kubectl rollout undo deployment/api-gateway -n production
\`\`\`

**Long-term Fix:** Restore async database connection pattern. Review PR #847 for the problematic change.`
  }
  if (lower.includes('security') || lower.includes('audit') || lower.includes('vulnerab')) {
    return `**Security Audit Results — Kubernetes Configurations**

**Critical Findings (3):**
- \`privileged: true\` containers running in staging-central (2 pods)
- Service account \`default\` has cluster-admin binding in 3 namespaces
- Secrets stored as environment variables in payments-processor deployment

**High Severity (5):**
- NetworkPolicy missing for 6 namespaces allowing unrestricted pod-to-pod traffic
- Image tag \`:latest\` used in 4 production deployments (no version pinning)
- No pod security standards enforced on ml-training-gpu cluster

**Remediation Priority:**
1. Immediately remove cluster-admin binding from default service account
2. Rotate all secrets currently in environment variables
3. Apply NetworkPolicies using the templates I can generate

Would you like me to generate the remediation manifests?`
  }
  if (lower.includes('cost') || lower.includes('spend') || lower.includes('saving')) {
    return `**Cost Analysis — Top Optimization Opportunities**

**Current Monthly Spend:** $47,230
**Potential Savings:** $12,840/mo (27% reduction)

**Top 3 Opportunities:**

1. **Right-size over-provisioned nodes** (+$6,200/mo savings)
   - 8 nodes in dev/staging clusters at <15% avg CPU utilization
   - Migrate to t3.medium from m5.xlarge → immediate savings

2. **Reserved Instance Coverage** (+$3,800/mo savings)
   - Production clusters have only 34% RI coverage
   - Purchasing 1-year RIs for baseline capacity saves 40%

3. **Spot Instance Adoption** (+$2,840/mo savings)
   - ML training workloads are fault-tolerant and ideal for Spot
   - Current on-demand spend for ml-training-gpu: $7,100/mo

Shall I create a detailed implementation plan for any of these?`
  }
  return `I've analyzed your request: "${userMessage}"

Based on the current state of your infrastructure, here's what I found:

**Analysis in Progress**
I'm cross-referencing your query against live cluster metrics, recent incident history, and security findings.

**Key Observations:**
- All 8 clusters are currently reporting metrics
- 2 clusters have elevated CPU utilization (>80%)
- No critical security incidents in the last 24 hours

For more specific analysis, try asking about a particular cluster, service, or incident. I can also run targeted diagnostics if you provide more context.

What specific aspect would you like me to investigate further?`
}

export default function AIInvestigation() {
  const [messages, setMessages] = useState<AIMessage[]>(INITIAL_MESSAGES)
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  async function sendMessage(text: string) {
    const trimmed = text.trim()
    if (!trimmed || isThinking) return

    const userMsg: AIMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsThinking(true)

    await new Promise(r => setTimeout(r, 1200 + Math.random() * 800))

    const assistantMsg: AIMessage = {
      id: `ai-${Date.now()}`,
      role: 'assistant',
      content: generateResponse(trimmed),
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, assistantMsg])
    setIsThinking(false)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  function handleCopy(text: string) {
    navigator.clipboard.writeText(text).catch(() => {})
  }

  function clearChat() {
    setMessages(INITIAL_MESSAGES)
  }

  return (
    <div className="flex flex-col space-y-4 max-w-[1200px] h-[calc(100vh-140px)]">
      <PageHeader
        title="AI Investigation"
        subtitle="Intelligent analysis, root cause investigation, and automated remediation"
        breadcrumb={['Home', 'AI Investigation']}
        actions={
          <button onClick={clearChat} className="btn-secondary text-xs py-2 px-3 flex items-center gap-2">
            <RefreshCw className="w-3.5 h-3.5" /> New Session
          </button>
        }
      />

      {/* Quick actions */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2">
        {suggestedPrompts.map(({ icon: Icon, label, prompt }) => (
          <button
            key={label}
            onClick={() => sendMessage(prompt)}
            disabled={isThinking}
            className="flex items-center gap-2 px-3 py-2 bg-surface-200 border border-white/[0.05] rounded-lg hover:border-brand-500/30 hover:bg-brand-500/5 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <Icon className="w-3.5 h-3.5 text-brand-400 flex-shrink-0 group-hover:text-brand-300" />
            <span className="text-xs text-gray-400 group-hover:text-gray-200 truncate">{label}</span>
          </button>
        ))}
      </div>

      {/* Chat window */}
      <Card className="flex-1 flex flex-col min-h-0">
        <CardHeader
          title="AI Assistant"
          subtitle="Powered by NexusOps Intelligence"
          icon={<Sparkles className="w-3.5 h-3.5 text-brand-400" />}
          actions={
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-emerald-400 font-medium">Online</span>
            </div>
          }
        />

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 min-h-0">
          <AnimatePresence initial={false}>
            {messages.map(msg => (
              <MessageBubble key={msg.id} msg={msg} onCopy={handleCopy} />
            ))}
            {isThinking && <ThinkingIndicator key="thinking" />}
          </AnimatePresence>
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-white/[0.05] p-4">
          <div className="flex items-end gap-3 bg-surface-200 border border-white/[0.06] rounded-xl px-4 py-3 focus-within:border-brand-500/40 transition-colors">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about clusters, incidents, security, costs…"
              rows={1}
              disabled={isThinking}
              className="flex-1 bg-transparent text-sm text-gray-200 placeholder:text-gray-600 resize-none outline-none leading-relaxed max-h-32 disabled:opacity-50"
              style={{ minHeight: '24px' }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isThinking}
              className="w-8 h-8 rounded-lg bg-brand-500 hover:bg-brand-400 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center flex-shrink-0 transition-colors"
            >
              <Send className="w-3.5 h-3.5 text-white" />
            </button>
          </div>
          <p className="text-[10px] text-gray-700 mt-2 text-center">Press Enter to send · Shift+Enter for new line · Responses are AI-generated for demo purposes</p>
        </div>
      </Card>
    </div>
  )
}
