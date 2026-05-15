import { useState } from 'react'
import { Star, Phone, Building2, Loader2 } from 'lucide-react'
import { Lawyer } from '../types'
import legalApi from '../services/api'

const CITIES = ['Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Hyderabad']
const AREAS = ['Contract Law', 'Employment Law', 'Property Law', 'Data Privacy Law', 'IP Law', 'Corporate Law']

export default function LawyerSelector({ initialLawyers = [] }: { initialLawyers?: Lawyer[] }) {
  const [lawyers, setLawyers] = useState<Lawyer[]>(initialLawyers)
  const [city, setCity] = useState('Bangalore')
  const [area, setArea] = useState('')
  const [loading, setLoading] = useState(false)

  const search = async () => {
    setLoading(true)
    try {
      const { data } = await legalApi.findLawyers(city, area || undefined)
      setLawyers(data.lawyers)
    } catch {
      setLawyers([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <select
          value={city}
          onChange={e => setCity(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {CITIES.map(c => <option key={c}>{c}</option>)}
        </select>
        <select
          value={area}
          onChange={e => setArea(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Practice Areas</option>
          {AREAS.map(a => <option key={a}>{a}</option>)}
        </select>
        <button onClick={search} disabled={loading} className="btn-primary text-sm flex items-center gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
          Find Lawyers
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {lawyers.map((l, i) => (
          <div key={i} className="card hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-semibold text-gray-900">{l.name}</h4>
                <p className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                  <Building2 className="w-3 h-3" /> {l.firm}
                </p>
              </div>
              <div className="flex items-center gap-1 text-yellow-500">
                <Star className="w-4 h-4 fill-current" />
                <span className="text-sm font-medium text-gray-700">{l.rating}</span>
              </div>
            </div>
            <div className="flex flex-wrap gap-1 mb-3">
              {l.practice_areas.slice(0, 2).map(pa => (
                <span key={pa} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">{pa}</span>
              ))}
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{l.experience}y experience</span>
              <a
                href={`mailto:${l.contact}`}
                className="flex items-center gap-1 text-blue-600 hover:underline"
              >
                <Phone className="w-3 h-3" /> Contact
              </a>
            </div>
          </div>
        ))}
      </div>

      {lawyers.length === 0 && !loading && (
        <p className="text-center text-gray-400 py-8">No lawyers found. Try searching above.</p>
      )}
    </div>
  )
}
