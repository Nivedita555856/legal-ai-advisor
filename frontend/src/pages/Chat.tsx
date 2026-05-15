import { useRef } from 'react'
import ChatInterface from '../components/ChatInterface'
import TestQuestions from '../components/TestQuestions'
import { MessageSquare } from 'lucide-react'

export default function Chat() {
  const chatRef = useRef<{ setInput: (q: string) => void } | null>(null)

  const handleSelect = (q: string) => {
    const ta = document.querySelector('textarea') as HTMLTextAreaElement | null
    if (ta) {
      ta.value = q
      ta.dispatchEvent(new Event('input', { bubbles: true }))
      ta.focus()
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
      {/* Main chat */}
      <div className="lg:col-span-3 card flex flex-col" style={{ minHeight: '75vh' }}>
        <div className="flex items-center gap-2 mb-4 pb-4 border-b border-gray-100">
          <MessageSquare className="w-5 h-5 text-blue-500" />
          <h1 className="font-bold text-gray-900">Legal AI Chat</h1>
          <span className="ml-auto text-xs text-gray-400 bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
            Powered by {import.meta.env.VITE_LLM_LABEL || 'Groq Llama 3.3'}
          </span>
        </div>
        <div className="flex-1">
          <ChatInterface />
        </div>
      </div>

      {/* Sidebar */}
      <div className="space-y-4 overflow-y-auto" style={{ maxHeight: '80vh' }}>
        <div className="card">
          <h3 className="font-semibold text-gray-900 text-sm mb-3">Test Questions</h3>
          <p className="text-xs text-gray-400 mb-3">Click any question to load it into the chat</p>
          <TestQuestions onSelect={handleSelect} />
        </div>
      </div>
    </div>
  )
}
