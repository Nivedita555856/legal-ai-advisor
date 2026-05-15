import DraftGeneratorComponent from '../components/DraftGenerator'
import LawyerSelector from '../components/LawyerSelector'
import { PenTool, Users } from 'lucide-react'

export default function Draft() {
  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Draft Generator</h1>

      <div className="card">
        <div className="flex items-center gap-2 mb-6">
          <PenTool className="w-5 h-5 text-green-500" />
          <h2 className="font-semibold text-gray-900">Generate Legal Document</h2>
        </div>
        <DraftGeneratorComponent />
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-6">
          <Users className="w-5 h-5 text-blue-500" />
          <h2 className="font-semibold text-gray-900">Find a Lawyer to Review Your Draft</h2>
          <p className="text-sm text-gray-500 ml-2">— AI drafts should always be reviewed by a qualified legal professional</p>
        </div>
        <LawyerSelector />
      </div>
    </div>
  )
}
