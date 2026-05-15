import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import legalApi from '../services/api'

interface UploadedFile { name: string; status: 'uploading' | 'success' | 'error'; doc_id?: string; chunks?: number }

export default function DocumentUploader({ onUploadSuccess }: { onUploadSuccess?: () => void }) {
  const [files, setFiles] = useState<UploadedFile[]>([])

  const onDrop = useCallback(async (accepted: File[]) => {
    for (const file of accepted) {
      setFiles(prev => [...prev, { name: file.name, status: 'uploading' }])
      try {
        const { data } = await legalApi.uploadDocument(file)
        setFiles(prev => prev.map(f => f.name === file.name
          ? { ...f, status: 'success', doc_id: data.doc_id, chunks: data.chunks }
          : f
        ))
        toast.success(`Ingested: ${file.name} (${data.chunks} chunks)`)
        onUploadSuccess?.()
      } catch (err: any) {
        setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: 'error' } : f))
        toast.error(`Failed: ${file.name} — ${err.message}`)
      }
    }
  }, [onUploadSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'text/markdown': ['.md'] },
    maxSize: 10 * 1024 * 1024,
  })

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-10 h-10 mx-auto mb-3 text-gray-400" />
        <p className="text-gray-600 font-medium">
          {isDragActive ? 'Drop files here...' : 'Drag & drop legal documents'}
        </p>
        <p className="text-gray-400 text-sm mt-1">PDF, TXT, MD — max 10 MB</p>
        <button className="btn-primary mt-4 text-sm">Browse Files</button>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((f, i) => (
            <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{f.name}</p>
                {f.chunks && <p className="text-xs text-gray-500">{f.chunks} chunks indexed</p>}
              </div>
              {f.status === 'uploading' && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
              {f.status === 'success' && <CheckCircle className="w-5 h-5 text-green-500" />}
              {f.status === 'error' && <XCircle className="w-5 h-5 text-red-500" />}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
