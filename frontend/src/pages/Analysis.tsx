import { useState } from 'react'
import { Search, Loader2, BarChart3, AlertTriangle, GitBranch, BookOpen } from 'lucide-react'
import toast from 'react-hot-toast'
import legalApi from '../services/api'
import RiskScorecard from '../components/RiskScorecard'
import LawyerSelector from '../components/LawyerSelector'
import { QueryResult } from '../types'

export default function Analysis() {
  const [query, setQuery] = useState('')
  const [jurisdiction, setJurisdiction] = useState('India')
  const [result, setResult] = useState<QueryResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'answer' | 'risk' | 'mcts' | 'lawyers'>('answer')

  const analyze = async () => {
    if (!query.trim()) { toast.error('Enter a query'); return }
    setLoading(true)
    try {
      const { data } = await legalApi.query(query, jurisdiction)
      setResult(data)
      setActiveTab('answer')
    } catch (err: any) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'answer', label: 'Answer', icon: BookOpen },
    { id: 'risk', label: 'Risk', icon: AlertTriangle },
    { id: 'mcts', label: 'MCTS Path', icon: GitBranch },
    { id: 'lawyers', label: 'Lawyers', icon: BarChart3 },
  ] as const

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Deep Analysis</h1>

      {/* Query form */}
      <div className="card">
        <div className="flex gap-3 mb-3">
          <textarea
            rows={3}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Ask a complex legal question for full multi-agent analysis..."
            className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>
        <div className="flex items-center gap-3">
          <select
            value={jurisdiction}
            onChange={e => setJurisdiction(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {['India', 'Maharashtra', 'Karnataka', 'Delhi', 'Tamil Nadu'].map(j => (
              <option key={j}>{j}</option>
            ))}
          </select>
          <button onClick={analyze} disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {loading ? 'Analyzing...' : 'Full Analysis'}
          </button>
          {loading && (
            <span className="text-xs text-gray-500 animate-pulse">
              Running 9-step pipeline (RAG → AutoGen → Crew AI → MCTS → Risk → Synthesis)...
            </span>
          )}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Meta */}
          <div className="flex flex-wrap gap-2">
            <span className="text-xs bg-purple-100 text-purple-700 px-2.5 py-1 rounded-full">
              RAG: {result.rag_strategy || 'auto'}
            </span>
            <span className={`text-xs px-2.5 py-1 rounded-full ${
              result.risk_score?.level === 'LOW' ? 'bg-green-100 text-green-700' :
              result.risk_score?.level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-700' :
              result.risk_score?.level === 'HIGH' ? 'bg-orange-100 text-orange-700' :
              'bg-red-100 text-red-700'
            }`}>
              Risk: {result.risk_score?.level || 'N/A'} ({result.risk_score?.score ?? '?'}/100)
            </span>
            <span className="text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full">
              Contradictions: {result.contradictions?.length ?? 0}
            </span>
            {result.needs_human_review && (
              <span className="text-xs bg-red-100 text-red-700 px-2.5 py-1 rounded-full flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Human Review Required
              </span>
            )}
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200 gap-1">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" /> {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="card">
            {activeTab === 'answer' && (
              <div className="prose max-w-none text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                {result.answer}
                {result.draft && (
                  <div className="mt-6 pt-6 border-t border-gray-200">
                    <h3 className="font-semibold mb-2">Generated Draft</h3>
                    <pre className="bg-gray-50 rounded-xl p-4 text-xs font-mono whitespace-pre-wrap max-h-64 overflow-y-auto">
                      {result.draft}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'risk' && (
              <div className="space-y-4">
                <RiskScorecard risk={result.risk_score} />
                {result.contradictions?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-orange-500" />
                      Contradictions Detected ({result.contradictions.length})
                    </h3>
                    <div className="space-y-2">
                      {result.contradictions.map((c, i) => (
                        <div key={i} className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-sm">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`badge-${c.severity?.toLowerCase()}`}>{c.severity}</span>
                            <span className="text-gray-600 text-xs">Clause {c.clause_a} vs Clause {c.clause_b}</span>
                          </div>
                          <p className="text-gray-700">{c.explanation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'mcts' && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">MCTS Optimal Reasoning Path</h3>
                {result.mcts_path?.length > 0 ? (
                  <div className="space-y-2">
                    {result.mcts_path.map((step, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                        <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs flex items-center justify-center font-bold flex-shrink-0">
                          {i + 1}
                        </span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900 capitalize">
                            {step.action.replace(/_/g, ' ')}
                          </p>
                          <div className="flex gap-3 mt-1">
                            <div className="w-32 bg-gray-200 rounded-full h-1.5">
                              <div
                                className="bg-blue-500 h-1.5 rounded-full"
                                style={{ width: `${(step.value * 100).toFixed(0)}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-500">
                              value: {step.value.toFixed(3)} · visits: {step.visits}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400 text-sm">MCTS path not available for this query.</p>
                )}
              </div>
            )}

            {activeTab === 'lawyers' && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Suggested Lawyers</h3>
                <LawyerSelector initialLawyers={result.lawyers || []} />
              </div>
            )}
          </div>
        </div>
      )}

      {!result && !loading && (
        <div className="text-center py-16">
          <BarChart3 className="w-16 h-16 mx-auto text-gray-200 mb-4" />
          <p className="text-gray-400">Enter a query above to run a full multi-agent legal analysis.</p>
          <p className="text-gray-300 text-sm mt-1">Results will include risk scoring, MCTS path, contradictions, and lawyer suggestions.</p>
        </div>
      )}
    </div>
  )
}
