import { AlertTriangle, CheckCircle, XCircle, Info } from 'lucide-react'
import { RiskScore } from '../types'

function RiskIcon({ level }: { level: string }) {
  if (level === 'LOW') return <CheckCircle className="w-8 h-8 text-green-500" />
  if (level === 'MEDIUM') return <Info className="w-8 h-8 text-yellow-500" />
  if (level === 'HIGH') return <AlertTriangle className="w-8 h-8 text-orange-500" />
  return <XCircle className="w-8 h-8 text-red-600" />
}

function riskColor(level: string) {
  if (level === 'LOW') return 'bg-green-50 border-green-200'
  if (level === 'MEDIUM') return 'bg-yellow-50 border-yellow-200'
  if (level === 'HIGH') return 'bg-orange-50 border-orange-200'
  return 'bg-red-50 border-red-200'
}

function barColor(level: string) {
  if (level === 'LOW') return 'bg-green-500'
  if (level === 'MEDIUM') return 'bg-yellow-500'
  if (level === 'HIGH') return 'bg-orange-500'
  return 'bg-red-600'
}

export default function RiskScorecard({ risk }: { risk: RiskScore }) {
  if (!risk || !risk.level) return null
  const score = risk.score ?? 0

  return (
    <div className={`border rounded-xl p-5 ${riskColor(risk.level)}`}>
      <div className="flex items-center gap-4 mb-4">
        <RiskIcon level={risk.level} />
        <div>
          <h3 className="font-bold text-lg">Risk Assessment</h3>
          <span className={`badge-${risk.level.toLowerCase()}`}>{risk.level} RISK</span>
        </div>
        <div className="ml-auto text-center">
          <p className="text-3xl font-bold">{score}</p>
          <p className="text-xs text-gray-500">/ 100</p>
        </div>
      </div>

      {/* Score bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${barColor(risk.level)}`}
          style={{ width: `${score}%` }}
        />
      </div>

      {risk.recommendation && (
        <div className="bg-white/70 rounded-lg p-3 text-sm text-gray-700">
          <strong>Recommendation:</strong> {risk.recommendation}
        </div>
      )}

      {risk.factors && risk.factors.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-semibold text-gray-600 mb-2">Risk Factors:</p>
          <ul className="space-y-1">
            {risk.factors.map((f, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <AlertTriangle className="w-3.5 h-3.5 text-orange-500 mt-0.5 flex-shrink-0" />
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
