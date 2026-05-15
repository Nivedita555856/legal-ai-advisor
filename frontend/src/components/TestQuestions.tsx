import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface Question { text: string }
interface Category { label: string; color: string; questions: Question[] }

const CATEGORIES: Category[] = [
  {
    label: 'Rental & Housing',
    color: 'border-blue-200 bg-blue-50 text-blue-700',
    questions: [
      { text: 'My landlord is refusing to return my security deposit after I vacated. What can I do?' },
      { text: 'My landlord cut off electricity to force me to leave. Is this legal?' },
      { text: 'I have been paying rent via UPI for 2 years but have no written agreement. Am I a trespasser?' },
      { text: 'My landlord wants to evict me without giving any notice. What are my rights?' },
      { text: 'What is the legal notice period a landlord must give before eviction?' },
      { text: 'Can a landlord increase rent arbitrarily mid-tenancy?' },
    ],
  },
  {
    label: 'Employment & NDA',
    color: 'border-green-200 bg-green-50 text-green-700',
    questions: [
      { text: 'My employment contract says I cannot join any competitor for 2 years after leaving. Is this enforceable?' },
      { text: 'My employer terminated me without serving the 90-day notice period. What are my legal options?' },
      { text: 'My employer is withholding my experience letter after I resigned. What can I do?' },
      { text: 'I was not paid my final month salary after resignation. What should I do?' },
      { text: 'What is the notice period in the employment contract? Can I leave before serving it?' },
      { text: 'My employer is asking me to sign an NDA that prevents me from working in my industry. Is this valid?' },
      { text: 'Am I entitled to gratuity after 4 years and 8 months of service?' },
    ],
  },
  {
    label: 'Consumer Rights',
    color: 'border-orange-200 bg-orange-50 text-orange-700',
    questions: [
      { text: 'I bought a defective product on Amazon and the seller is refusing a refund. Can I sue Amazon?' },
      { text: 'A company used fake countdown timers and false scarcity claims to make me buy. Is this illegal?' },
      { text: 'What is the 21-day rule for consumer complaints in India?' },
      { text: 'My bank transaction was unauthorized. Within how many days must I report it for zero liability?' },
      { text: 'A hotel charged a hidden service fee not mentioned at booking. What are my rights?' },
      { text: 'A food delivery app canceled my order and is refusing to refund. How do I escalate?' },
    ],
  },
  {
    label: 'Cyber Fraud & IT Act',
    color: 'border-red-200 bg-red-50 text-red-700',
    questions: [
      { text: 'Someone used my Aadhaar number to open a bank account. What legal action can I take?' },
      { text: 'I lost money to a UPI scam. What should I do and which sections of IT Act apply?' },
      { text: 'A fake website impersonated my company and defrauded customers. What is the legal remedy?' },
      { text: 'Someone hacked my Instagram account. What action can I take under the IT Act?' },
      { text: 'Are WhatsApp screenshots admissible as evidence in Indian courts?' },
      { text: 'I received a fake job offer and paid a registration fee. How do I get justice?' },
    ],
  },
  {
    label: 'DPDP Act 2023',
    color: 'border-purple-200 bg-purple-50 text-purple-700',
    questions: [
      { text: 'Can I demand Zomato to delete all my personal data permanently?' },
      { text: 'A company leaked my personal data without informing me. What penalty do they face?' },
      { text: 'My employer shared my salary details with third parties without consent. What does DPDP say?' },
      { text: 'Can a company deny me their service because I refused to share my location data?' },
      { text: 'What is the right to be forgotten under the DPDP Act 2023?' },
    ],
  },
  {
    label: 'Marital & Family Law',
    color: 'border-pink-200 bg-pink-50 text-pink-700',
    questions: [
      { text: 'My husband is abusive but I do not want a divorce. Can I still get protection under the law?' },
      { text: 'My in-laws threw me out of the matrimonial home. What are my legal rights?' },
      { text: 'I am earning but my income is less than my pre-marriage lifestyle. Can I claim maintenance?' },
      { text: 'What are the grounds for divorce under the Hindu Marriage Act?' },
      { text: 'My father died without a will. Do I have equal rights to ancestral property as my brother?' },
      { text: 'Triple talaq was pronounced against me. What legal action can I take?' },
    ],
  },
  {
    label: 'Constitutional Rights',
    color: 'border-yellow-200 bg-yellow-50 text-yellow-700',
    questions: [
      { text: 'What is Article 21 and how does it protect a tenant from being evicted without process?' },
      { text: 'My employer is using Article 19(1)(g) to justify a non-compete. Is that correct?' },
      { text: 'A government office is treating me unequally. Which constitutional article protects me?' },
      { text: 'What is the right to speedy trial and how does it relate to arbitration in India?' },
      { text: 'Can my right to shelter under Article 21 be used against an illegal eviction?' },
    ],
  },
  {
    label: 'Arbitration',
    color: 'border-slate-200 bg-slate-50 text-slate-700',
    questions: [
      { text: 'My contract says disputes must be arbitrated in Mumbai but I live in Delhi. Can I challenge this?' },
      { text: 'How long does arbitration take in India? Is there a time limit?' },
      { text: 'The other party refuses to participate in arbitration despite an arbitration clause. What can I do?' },
      { text: 'Can I challenge an arbitral award in court? On what grounds?' },
      { text: 'What is the difference between domestic and international commercial arbitration in India?' },
    ],
  },
  {
    label: 'Draft Generation',
    color: 'border-teal-200 bg-teal-50 text-teal-700',
    questions: [
      { text: 'Draft a legal notice to my employer for wrongful termination and unpaid dues' },
      { text: 'Generate a demand letter to recover security deposit from landlord' },
      { text: 'Draft a cease and desist letter for breach of NDA confidentiality' },
      { text: 'Draft a consumer complaint notice to Amazon for a defective product' },
      { text: 'Generate a legal notice for cyber fraud under IT Act Section 66C' },
      { text: 'Draft a maintenance application for a wife under Section 125 CrPC' },
    ],
  },
]

export default function TestQuestions({ onSelect }: { onSelect: (q: string) => void }) {
  const [openCategory, setOpenCategory] = useState<number | null>(0)

  return (
    <div className="space-y-1.5">
      {CATEGORIES.map((cat, ci) => (
        <div key={ci} className={`border rounded-xl overflow-hidden ${cat.color.split(' ')[0]}`}>
          <button
            onClick={() => setOpenCategory(openCategory === ci ? null : ci)}
            className="w-full flex items-center justify-between px-3 py-2.5 bg-white hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold px-1.5 py-0.5 rounded-full ${cat.color}`}>
                {cat.questions.length}
              </span>
              <span className="font-medium text-gray-800 text-xs">{cat.label}</span>
            </div>
            {openCategory === ci
              ? <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
              : <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
            }
          </button>

          {openCategory === ci && (
            <div className="border-t border-gray-100 divide-y divide-gray-50">
              {cat.questions.map((q, qi) => (
                <button
                  key={qi}
                  onClick={() => onSelect(q.text)}
                  className="w-full text-left px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 hover:text-blue-700 transition-colors"
                >
                  {q.text}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
