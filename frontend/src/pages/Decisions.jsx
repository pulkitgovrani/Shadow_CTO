import { useEffect, useState } from 'react'
import { getDecisions, getRepos } from '../api'
import DecisionCard from '../components/DecisionCard'

const TYPES = ['all', 'addition', 'removal', 'refactor', 'rollback', 'migration', 'security', 'performance', 'config']

export default function Decisions() {
  const [repos, setRepos] = useState([])
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [filterType, setFilterType] = useState('all')

  useEffect(() => {
    getRepos().then((data) => {
      setRepos(data)
      if (data.length > 0) setSelectedRepo(data[0])
    })
  }, [])

  useEffect(() => {
    if (selectedRepo) loadDecisions()
  }, [selectedRepo, filterType])

  async function loadDecisions() {
    const data = await getDecisions(selectedRepo.id, filterType === 'all' ? null : filterType)
    setDecisions(data)
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">All Decisions</h1>
        <select
          value={selectedRepo?.id || ''}
          onChange={(e) => setSelectedRepo(repos.find((r) => r.id === Number(e.target.value)))}
          className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none"
        >
          {repos.map((r) => <option key={r.id} value={r.id}>{r.owner}/{r.name}</option>)}
        </select>
      </div>

      {/* Type filter */}
      <div className="flex gap-2 flex-wrap mb-6">
        {TYPES.map((t) => (
          <button
            key={t}
            onClick={() => setFilterType(t)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              filterType === t
                ? 'bg-sky-600 border-sky-500 text-white'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {decisions.length === 0 ? (
        <div className="text-center py-12 text-slate-600">No decisions found for this filter.</div>
      ) : (
        <div className="space-y-3">
          {decisions.map((d) => <DecisionCard key={d.id} decision={d} />)}
        </div>
      )}
    </div>
  )
}
