import { useEffect, useState } from 'react'
import { FileText, RefreshCw, Trash2, Calendar, Database } from 'lucide-react'
import toast from 'react-hot-toast'
import DocumentUploader from '../components/DocumentUploader'
import legalApi from '../services/api'
import { Document } from '../types'

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)

  const fetchDocs = async () => {
    setLoading(true)
    try {
      const [docsRes, statsRes] = await Promise.allSettled([
        legalApi.listDocuments(),
        legalApi.getDocumentStats(),
      ])
      if (docsRes.status === 'fulfilled') setDocuments(docsRes.value.data.documents)
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data.stats)
    } catch (err: any) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDocs() }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <button onClick={fetchDocs} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card text-center">
            <p className="text-2xl font-bold text-blue-600">{documents.length}</p>
            <p className="text-sm text-gray-500">Documents</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-purple-600">
              {stats.total_vector_count?.toLocaleString() ?? '—'}
            </p>
            <p className="text-sm text-gray-500">Vectors</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-green-600">
              {documents.reduce((s, d) => s + (d.chunk_count || 0), 0)}
            </p>
            <p className="text-sm text-gray-500">Total Chunks</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-orange-600">1536</p>
            <p className="text-sm text-gray-500">Embedding Dim</p>
          </div>
        </div>
      )}

      {/* Uploader */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-500" />
          Upload & Ingest Documents
        </h2>
        <DocumentUploader onUploadSuccess={fetchDocs} />
      </div>

      {/* Document list */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-500" />
          Ingested Documents ({documents.length})
        </h2>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 mx-auto text-gray-300 mb-3" />
            <p className="text-gray-400">No documents yet. Upload some legal documents to get started.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-2 text-gray-600 font-medium">Name</th>
                  <th className="text-left py-3 px-2 text-gray-600 font-medium">Type</th>
                  <th className="text-left py-3 px-2 text-gray-600 font-medium">Chunks</th>
                  <th className="text-left py-3 px-2 text-gray-600 font-medium">Uploaded</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-2">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                        <span className="font-medium text-gray-900 truncate max-w-xs">{doc.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-2">
                      <span className="uppercase text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                        {doc.file_type || 'unknown'}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-gray-600">{doc.chunk_count ?? '—'}</td>
                    <td className="py-3 px-2 text-gray-500 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
