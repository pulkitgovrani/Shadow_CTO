import { useEffect, useState } from 'react'
import { analyzePatterns, getPatterns, getRepos } from '../api'
import PatternAlert from '../components/PatternAlert'

export default function Patterns() {
  const [repos, setRepos] = useState([])
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [patterns, setPatterns] = useState([])
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    getRepos().then((data) => {
      setRepos(data)
      if (data.length > 0) setSelectedRepo(data[0])
    })
  }, [])

  useEffect(() => {
    if (selectedRepo) loadPatterns()
  }, [selectedRepo])

  async function loadPatterns() {
    const data = await getPatterns(selectedRepo.id)
    setPatterns(data)
  }

  async function handleAnalyze() {
    if (!selectedRepo || analyzing) return
    setAnalyzing(true)
    await analyzePatterns(selectedRepo.id)
    setTimeout(async () => {
      await loadPatterns()
      setAnalyzing(false)
    }, 5000)
  }

  const bySeverity = (sev) => patterns.filter((p) => p.severity === sev)

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Failure Patterns</h1>
          <p className="text-slate-500 text-sm mt-1">
            Hermes autonomously detects recurring engineering problems
          </p>
        </div>
        <div className="flex gap-3">
          <select
            value={selectedRepo?.id || ''}
            onChange={(e) => setSelectedRepo(repos.find((r) => r.id === Number(e.target.value)))}
            className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none"
          >
            {repos.map((r) => <option key={r.id} value={r.id}>{r.owner}/{r.name}</option>)}
          </select>
          <button
            onClick={handleAnalyze}
            disabled={analyzing || !selectedRepo}
            className="px-4 py-2 bg-sky-700 hover:bg-sky-600 disabled:bg-slate-700 disabled:text-slate-500 rounded-lg text-sm font-semibold text-white transition-colors"
          >
            {analyzing ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      </div>

      {patterns.length === 0 ? (
        <div className="text-center py-16 text-slate-600">
          <span className="text-4xl block mb-3">🔍</span>
          <p>No patterns detected yet. Run an analysis after syncing your repo.</p>
        </div>
      ) : (
        <div className="space-y-8">
          {['high', 'medium', 'low'].map((sev) => {
            const ps = bySeverity(sev)
            if (ps.length === 0) return null
            return (
              <div key={sev}>
                <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                  {sev} severity ({ps.length})
                </h2>
                <div className="space-y-3">
                  {ps.map((p) => <PatternAlert key={p.id} pattern={p} />)}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
