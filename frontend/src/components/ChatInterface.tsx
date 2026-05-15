import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Bot, User, ShieldCheck, FileText, Star, Zap, Globe, Database, GitBranch, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import legalApi from '../services/api'
import { QueryResult } from '../types'

interface Source { document: string; score: number; source_type?: string; source_label?: string }
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  result?: QueryResult & { retrieved_chunks?: Source[] }
  timestamp: Date
  typing?: boolean
}

/* ── RAG pipeline badge ─────────────────────────────────────────────────── */
function RagBadge({ strategy }: { strategy?: string }) {
  if (!strategy || strategy === 'none') return null
  const labels: Record<string, { label: string; color: string; icon: JSX.Element }> = {
    ensemble_hybrid: { label: 'Ensemble RAG', color: 'bg-indigo-100 text-indigo-700', icon: <Zap className="w-3 h-3" /> },
    vector: { label: 'Vector RAG', color: 'bg-blue-100 text-blue-700', icon: <Database className="w-3 h-3" /> },
    corrective: { label: 'Corrective RAG', color: 'bg-green-100 text-green-700', icon: <GitBranch className="w-3 h-3" /> },
    web_case_law: { label: 'Web Case Law', color: 'bg-orange-100 text-orange-700', icon: <Globe className="w-3 h-3" /> },
  }
  const info = labels[strategy] || { label: strategy, color: 'bg-gray-100 text-gray-600', icon: <Database className="w-3 h-3" /> }
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${info.color}`}>
      {info.icon}{info.label}
    </span>
  )
}

/* ── Source cards with scores ──────────────────────────────────────────── */
function SourceCards({ sources }: { sources: Source[] }) {
  if (!sources?.length) return null
  const unique = Array.from(new Map(sources.map(s => [s.document || s.source_label, s])).values()).slice(0, 5)
  const scoreColor = (s: number) => s >= 0.8 ? 'bg-green-500' : s >= 0.6 ? 'bg-yellow-500' : 'bg-orange-400'
  const typeIcon = (t?: string) => t === 'web_case_law' || t === 'web_government' ? <Globe className="w-3 h-3" /> : <FileText className="w-3 h-3" />

  return (
    <div className="mt-2 space-y-1.5">
      <p className="text-xs text-gray-400 flex items-center gap-1"><FileText className="w-3 h-3" /> Sources retrieved</p>
      <div className="flex flex-wrap gap-1.5">
        {unique.map((s, i) => {
          const score = s.score ?? 0
          const pct = Math.round(score * 100)
          const label = (s.source_label || s.document || 'Document').replace(/\.(md|pdf|txt)$/, '')
          return (
            <div
              key={i}
              className="flex items-center gap-1.5 bg-white border border-gray-200 rounded-lg px-2 py-1 text-xs shadow-sm"
              style={{ animation: `slideIn 0.3s ease ${i * 0.05}s both` }}
            >
              <span className="text-gray-400">{typeIcon(s.source_type)}</span>
              <span className="text-gray-700 max-w-[120px] truncate" title={label}>{label}</span>
              <div className="flex items-center gap-1">
                <div className="w-12 bg-gray-200 rounded-full h-1">
                  <div className={`h-1 rounded-full ${scoreColor(score)}`} style={{ width: `${pct}%` }} />
                </div>
                <span className={`font-bold ${score >= 0.8 ? 'text-green-600' : score >= 0.6 ? 'text-yellow-600' : 'text-orange-500'}`}>
                  {pct}%
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ── Confidence meter ─────────────────────────────────────────────────── */
function ConfidenceMeter({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 75 ? '#22c55e' : pct >= 50 ? '#eab308' : '#f97316'
  const label = pct >= 75 ? 'High Confidence' : pct >= 50 ? 'Moderate' : 'Low Confidence'
  return (
    <div className="flex items-center gap-2 mt-1.5">
      <Star className="w-3.5 h-3.5 text-yellow-400 flex-shrink-0" />
      <div className="flex-1 bg-gray-200 rounded-full h-1.5 overflow-hidden">
        <div
          className="h-1.5 rounded-full transition-all duration-1000"
          style={{ width: `${pct}%`, backgroundColor: color, animation: 'growWidth 1s ease' }}
        />
      </div>
      <span className="text-xs text-gray-500 whitespace-nowrap">{label} {pct}%</span>
    </div>
  )
}

/* ── Human-loop guardrail banner ─────────────────────────────────────── */
function GuardrailBanner({ needsHuman, riskLevel }: { needsHuman?: boolean; riskLevel?: string }) {
  if (!needsHuman && riskLevel !== 'HIGH' && riskLevel !== 'CRITICAL') return null
  return (
    <div className="mt-2 flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2 text-xs text-amber-800"
      style={{ animation: 'fadeIn 0.5s ease' }}>
      <ShieldCheck className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
      <div>
        <span className="font-semibold">Human Review Triggered</span> — Risk Level: {riskLevel}.
        This response has been flagged by the guardrails system. Please consult a qualified lawyer before taking legal action.
      </div>
    </div>
  )
}

/* ── Animated typing indicator ─────────────────────────────────────────── */
function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0, 1, 2].map(i => (
        <span key={i} className="w-2 h-2 rounded-full bg-blue-500"
          style={{ animation: `bounce 1.2s ease infinite`, animationDelay: `${i * 0.15}s` }} />
      ))}
      <span className="text-xs text-gray-400 ml-2">Analysing across all sources…</span>
    </div>
  )
}

/* ── Pipeline status bar ─────────────────────────────────────────────── */
function PipelineStatus({ active }: { active: boolean }) {
  const steps = ['Vector RAG', 'BM25', 'KG Search', 'Web Cases', 'MCTS', 'Agents', 'Guardrails']
  const [step, setStep] = useState(0)
  useEffect(() => {
    if (!active) { setStep(0); return }
    const t = setInterval(() => setStep(s => (s + 1) % steps.length), 600)
    return () => clearInterval(t)
  }, [active])
  if (!active) return null
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 rounded-full text-xs">
      <Zap className="w-3 h-3 text-yellow-400 animate-pulse" />
      <span className="text-gray-400">Running:</span>
      <span className="text-blue-400 font-medium" style={{ minWidth: 80 }}>{steps[step]}</span>
      <div className="flex gap-0.5">
        {steps.map((_, i) => (
          <div key={i} className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${i <= step ? 'bg-blue-400' : 'bg-gray-600'}`} />
        ))}
      </div>
    </div>
  )
}

/* ── Message bubble ─────────────────────────────────────────────────── */
function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'
  const chunks: Source[] = (msg.result as any)?.retrieved_chunks || []
  const risk = msg.result?.risk_score
  const needsHuman = msg.result?.needs_human_review
  const strategy = msg.result?.rag_strategy
  const conf = risk ? Math.max(0, (100 - (risk.score ?? 50)) / 100) : null

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
      style={{ animation: 'fadeSlideUp 0.3s ease both' }}>
      {/* Avatar */}
      <div className={`w-9 h-9 rounded-2xl flex-shrink-0 flex items-center justify-center shadow-md ${
        isUser
          ? 'bg-gradient-to-br from-blue-500 to-blue-700'
          : 'bg-gradient-to-br from-slate-700 via-slate-800 to-blue-900'
      }`}>
        {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
      </div>

      {/* Content */}
      <div className={`max-w-[78%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm ${
          isUser
            ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-tr-sm'
            : 'bg-white border border-gray-100 text-gray-800 rounded-tl-sm'
        }`}>
          {msg.typing ? <TypingIndicator /> : (
            <p className="whitespace-pre-wrap">{msg.content}</p>
          )}
          <p className={`text-xs mt-1.5 ${isUser ? 'text-blue-200' : 'text-gray-400'}`}>
            {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>

        {/* Metadata for assistant */}
        {!isUser && !msg.typing && msg.result && (
          <div className="w-full mt-1.5 space-y-1.5 px-1">
            <div className="flex flex-wrap gap-1.5">
              <RagBadge strategy={strategy} />
              {msg.result.mcts_path?.length > 0 && (
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                  <GitBranch className="w-3 h-3" />MCTS: {msg.result.mcts_path[0]?.action?.replace(/_/g, ' ')}
                </span>
              )}
            </div>
            {conf !== null && <ConfidenceMeter score={conf} />}
            <SourceCards sources={chunks} />
            <GuardrailBanner needsHuman={needsHuman} riskLevel={risk?.level} />
            {msg.result.lawyers?.length > 0 && needsHuman && (
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs">
                <p className="text-slate-600 font-semibold mb-1 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-orange-500" /> Suggested Lawyers
                </p>
                {msg.result.lawyers.slice(0, 2).map((l, i) => (
                  <p key={i} className="text-slate-500">{l.name} — {l.firm}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Main ChatInterface ─────────────────────────────────────────────── */
export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([{
    id: '0',
    role: 'assistant',
    content: 'Hello! I am your AI Legal Advisor, powered by Ensemble RAG — combining Vector search, BM25 keyword matching, Knowledge Graph, and live Web search for Indian case law.\n\nAsk me anything about your legal situation. I will cite the exact section, case law, actionable steps, and source confidence scores.',
    timestamp: new Date(),
  }])
  const [input, setInput] = useState('')
  const [jurisdiction, setJurisdiction] = useState('India')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async () => {
    if (!input.trim() || loading) return
    const q = input.trim()
    setInput('')
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: q, timestamp: new Date() }
    setMessages(p => [...p, userMsg])
    setLoading(true)

    try {
      const { data } = await legalApi.query(q, jurisdiction)
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer || 'Analysis complete.',
        result: { ...data, retrieved_chunks: (data as any).retrieved_chunks || [] },
        timestamp: new Date(),
      }
      setMessages(p => [...p, assistantMsg])
    } catch (err: any) {
      toast.error(err.message)
      setMessages(p => [...p, {
        id: (Date.now() + 1).toString(), role: 'assistant',
        content: `Error: ${err.message}`, timestamp: new Date(),
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <style>{`
        @keyframes fadeSlideUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
        @keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
        @keyframes slideIn { from { opacity:0; transform:translateX(-8px); } to { opacity:1; transform:translateX(0); } }
        @keyframes growWidth { from { width:0; } to { width: var(--target-width, 100%); } }
        @keyframes bounce { 0%,80%,100% { transform:translateY(0); opacity:.4; } 40% { transform:translateY(-6px); opacity:1; } }
      `}</style>

      {/* Pipeline status */}
      <div className="flex justify-center mb-2">
        <PipelineStatus active={loading} />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1 min-h-0">
        {messages.map(m => <MessageBubble key={m.id} msg={m} />)}
        {loading && (
          <div className="flex gap-3" style={{ animation: 'fadeSlideUp 0.3s ease' }}>
            <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-slate-700 to-blue-900 flex items-center justify-center shadow-md flex-shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm shadow-sm">
              <TypingIndicator />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 pt-3">
        <div className="flex gap-2 mb-2 flex-wrap">
          <select value={jurisdiction} onChange={e => setJurisdiction(e.target.value)}
            className="border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-400">
            {['India','Maharashtra','Karnataka','Delhi','Tamil Nadu','Telangana','Gujarat'].map(j => (
              <option key={j}>{j}</option>
            ))}
          </select>
          <span className="text-xs text-gray-400 self-center">jurisdiction</span>
          <span className="ml-auto text-xs text-gray-400 self-center flex items-center gap-1">
            <Zap className="w-3 h-3 text-yellow-400" />Ensemble RAG active
          </span>
        </div>
        <div className="flex gap-2">
          <textarea rows={2} value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
            placeholder="Describe your legal situation or ask a question... (Enter to send)"
            disabled={loading}
            className="flex-1 border border-gray-200 rounded-2xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none bg-gray-50 focus:bg-white transition-colors placeholder-gray-400"
          />
          <button onClick={send} disabled={loading || !input.trim()}
            className="bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-40 text-white px-4 rounded-2xl self-end transition-all active:scale-95 shadow-md"
            style={{ height: 60 }}>
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </div>
      </div>
    </div>
  )
}
