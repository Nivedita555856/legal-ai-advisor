import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

const FAQ_ITEMS = [
  {
    q: 'What types of legal documents can I analyze?',
    a: 'You can analyze any legal document including contracts, NDAs, employment agreements, lease agreements, service agreements, court orders, statutes, consumer protection notices, partnership deeds, and more. Upload PDFs or text files.'
  },
  {
    q: 'How accurate is the AI analysis?',
    a: 'The system uses 5 specialized RAG strategies (Vector, HyDE, Self-RAG, Corrective, Parent-Child), multi-agent reasoning via AutoGen and Crew AI, and MCTS planning for optimal reasoning paths. Accuracy depends on document quality. Always verify high-stakes decisions with a qualified lawyer.'
  },
  {
    q: 'What is MCTS planning?',
    a: 'Monte Carlo Tree Search (MCTS) is an AI planning algorithm that explores thousands of reasoning paths to find the optimal approach for answering your legal query. It assigns reward values to different analysis strategies and selects the best sequence.'
  },
  {
    q: 'How does Corrective RAG work?',
    a: 'Corrective RAG first searches your uploaded documents. If confidence is below a threshold (0.6), it automatically falls back to web search via Tavily to find relevant legal information, then combines both sources for a complete answer.'
  },
  {
    q: 'Is my data secure?',
    a: 'Documents are stored in Supabase (PostgreSQL) and indexed in Pinecone vector database. Embeddings are generated using OpenAI. Legal analysis is performed by Groq Llama 3. All communications are encrypted. We do not share your documents with third parties.'
  },
  {
    q: 'Can I generate legal drafts?',
    a: 'Yes! The Draft Generator can create NDAs, employment agreements, legal notices, demand letters, lease agreements, service agreements, termination letters, and partnership agreements. Generated drafts follow Indian legal conventions but should be reviewed by a lawyer.'
  },
  {
    q: 'What does the Risk Scorecard measure?',
    a: 'The Risk Scorecard scores legal risk from 0-100 across four levels: LOW (0-30), MEDIUM (31-60), HIGH (61-80), and CRITICAL (81-100). It analyzes enforceability, liability exposure, compliance gaps, ambiguous clauses, and missing protective provisions.'
  },
  {
    q: 'How does the Knowledge Graph work?',
    a: 'We use Neo4j Aura to build a graph of legal entities (parties, clauses, obligations) and their relationships. This enables cross-document relationship discovery — e.g., finding all documents involving a specific party or tracking obligation chains.'
  },
]

export default function FAQAccordion() {
  const [open, setOpen] = useState<number | null>(null)

  return (
    <div className="space-y-2">
      {FAQ_ITEMS.map((item, i) => (
        <div key={i} className="border border-gray-200 rounded-xl overflow-hidden">
          <button
            onClick={() => setOpen(open === i ? null : i)}
            className="w-full flex items-center justify-between px-5 py-4 text-left bg-white hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900 text-sm">{item.q}</span>
            {open === i
              ? <ChevronDown className="w-4 h-4 text-blue-500 flex-shrink-0" />
              : <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
            }
          </button>
          {open === i && (
            <div className="px-5 pb-4 pt-0 bg-gray-50 text-sm text-gray-600 leading-relaxed">
              {item.a}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
