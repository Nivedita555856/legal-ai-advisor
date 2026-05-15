import { useEffect, useState } from 'react'
import { FileText, MessageSquare, BarChart3, Zap, Upload, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import legalApi from '../services/api'
import FAQAccordion from '../components/FAQAccordion'

interface Stats { docs: number; vectorCount: number; healthy: boolean }

export default function Dashboard() {
  const nav = useNavigate()
  const [stats, setStats] = useState<Stats>({ docs: 0, vectorCount: 0, healthy: false })

  useEffect(() => {
    const load = async () => {
      try {
        await legalApi.health()
        const [docsRes, statsRes] = await Promise.allSettled([
          legalApi.listDocuments(),
          legalApi.getDocumentStats(),
        ])
        const docs = docsRes.status === 'fulfilled' ? docsRes.value.data.count : 0
        const vecs = statsRes.status === 'fulfilled'
          ? statsRes.value.data.stats?.total_vector_count ?? 0 : 0
        setStats({ docs, vectorCount: vecs, healthy: true })
      } catch { setStats(s => ({ ...s, healthy: false })) }
    }
    load()
  }, [])

  const quickActions = [
    { icon: Upload, label: 'Upload Document', desc: 'Ingest a contract or statute', path: '/documents', color: 'bg-blue-50 text-blue-600' },
    { icon: MessageSquare, label: 'Ask AI', desc: 'Query your legal documents', path: '/chat', color: 'bg-purple-50 text-purple-600' },
    { icon: BarChart3, label: 'Risk Analysis', desc: 'Deep-dive analysis view', path: '/analysis', color: 'bg-orange-50 text-orange-600' },
    { icon: FileText, label: 'Draft Generator', desc: 'Generate legal documents', path: '/draft', color: 'bg-green-50 text-green-600' },
  ]

  const techPills = [
    'Groq Llama 3 70B', 'Vector RAG', 'HyDE RAG', 'Self-RAG',
    'Corrective RAG', 'Parent-Child RAG', 'AutoGen', 'CrewAI',
    'MCTS Planner', 'LangGraph', 'Pinecone', 'Neo4j', 'Supabase', 'Tavily',
  ]

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="bg-gradient-to-br from-slate-900 to-blue-900 rounded-2xl p-8 text-white">
        <div className="flex items-center gap-2 mb-3">
          <span className={`w-2.5 h-2.5 rounded-full ${stats.healthy ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
          <span className="text-sm text-slate-300">{stats.healthy ? 'All systems operational' : 'Check API connection'}</span>
        </div>
        <h1 className="text-3xl font-bold mb-2">AI Legal Document Advisor</h1>
        <p className="text-slate-300 text-lg mb-6">
          Multi-agent RAG · AutoGen · CrewAI · MCTS · Knowledge Graph
        </p>
        <div className="flex flex-wrap gap-4 text-center">
          <div className="bg-white/10 rounded-xl px-6 py-3">
            <p className="text-2xl font-bold">{stats.docs}</p>
            <p className="text-slate-300 text-sm">Documents</p>
          </div>
          <div className="bg-white/10 rounded-xl px-6 py-3">
            <p className="text-2xl font-bold">{stats.vectorCount.toLocaleString()}</p>
            <p className="text-slate-300 text-sm">Vectors Indexed</p>
          </div>
          <div className="bg-white/10 rounded-xl px-6 py-3">
            <p className="text-2xl font-bold">5</p>
            <p className="text-slate-300 text-sm">RAG Strategies</p>
          </div>
          <div className="bg-white/10 rounded-xl px-6 py-3">
            <p className="text-2xl font-bold">4</p>
            <p className="text-slate-300 text-sm">AI Agents</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map(({ icon: Icon, label, desc, path, color }) => (
            <button
              key={path}
              onClick={() => nav(path)}
              className="card hover:shadow-md transition-all hover:-translate-y-0.5 text-left group"
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <p className="font-semibold text-gray-900 text-sm">{label}</p>
              <p className="text-xs text-gray-500 mt-1">{desc}</p>
              <ArrowRight className="w-3.5 h-3.5 text-gray-400 mt-3 group-hover:text-blue-500 transition-colors" />
            </button>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-yellow-500" />
          <h2 className="font-semibold text-gray-900">Technology Stack</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {techPills.map(t => (
            <span key={t} className="text-xs bg-gray-100 text-gray-700 px-3 py-1 rounded-full border border-gray-200 font-medium">
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* FAQ */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Frequently Asked Questions</h2>
        <FAQAccordion />
      </div>
    </div>
  )
}
