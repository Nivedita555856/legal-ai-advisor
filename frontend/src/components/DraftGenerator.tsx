import { useState } from 'react'
import { PenTool, Copy, Download, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import legalApi from '../services/api'

const DOC_TYPES = [
  { value: 'notice', label: 'Legal Notice' },
  { value: 'nda', label: 'NDA' },
  { value: 'employment', label: 'Employment Agreement' },
  { value: 'demand_letter', label: 'Demand Letter' },
  { value: 'lease', label: 'Lease Agreement' },
  { value: 'service', label: 'Service Agreement' },
  { value: 'termination', label: 'Termination Letter' },
  { value: 'partnership', label: 'Partnership Agreement' },
]

export default function DraftGenerator() {
  const [scenario, setScenario] = useState('')
  const [docType, setDocType] = useState('notice')
  const [parties, setParties] = useState('Party A and Party B')
  const [jurisdiction, setJurisdiction] = useState('India')
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)

  const generate = async () => {
    if (!scenario.trim()) { toast.error('Please describe the scenario'); return }
    setLoading(true)
    try {
      const { data } = await legalApi.generateDraft(scenario, docType, parties, jurisdiction)
      setDraft(data.draft)
      toast.success('Draft generated!')
    } catch (err: any) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const copyDraft = () => { navigator.clipboard.writeText(draft); toast.success('Copied!') }

  const downloadDraft = () => {
    const blob = new Blob([draft], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url
    a.download = `${docType}_draft.txt`; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
          <select
            value={docType}
            onChange={e => setDocType(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {DOC_TYPES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Jurisdiction</label>
          <select
            value={jurisdiction}
            onChange={e => setJurisdiction(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {['India', 'Maharashtra', 'Karnataka', 'Delhi', 'Tamil Nadu'].map(j => <option key={j}>{j}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Parties Involved</label>
        <input
          type="text"
          value={parties}
          onChange={e => setParties(e.target.value)}
          placeholder="e.g. ABC Pvt Ltd (Employer) and John Doe (Employee)"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Scenario / Brief</label>
        <textarea
          rows={4}
          value={scenario}
          onChange={e => setScenario(e.target.value)}
          placeholder="Describe the legal situation, e.g. 'Employee terminated without notice after 3 years of service. Company failed to pay final settlement...'"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />
      </div>

      <button onClick={generate} disabled={loading} className="btn-primary flex items-center gap-2">
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <PenTool className="w-4 h-4" />}
        {loading ? 'Generating...' : 'Generate Draft'}
      </button>

      {draft && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">Generated Draft</h3>
            <div className="flex gap-2">
              <button onClick={copyDraft} className="btn-secondary text-xs flex items-center gap-1">
                <Copy className="w-3.5 h-3.5" /> Copy
              </button>
              <button onClick={downloadDraft} className="btn-secondary text-xs flex items-center gap-1">
                <Download className="w-3.5 h-3.5" /> Download
              </button>
            </div>
          </div>
          <pre className="bg-gray-50 border border-gray-200 rounded-xl p-5 text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed max-h-96 overflow-y-auto">
            {draft}
          </pre>
        </div>
      )}
    </div>
  )
}
