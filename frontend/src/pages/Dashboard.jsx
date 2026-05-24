import { useEffect, useState } from 'react'
import { createRepo, getDecisions, getPatterns, getRepos, triggerSync, streamQuery } from '../api'
import DecisionCard from '../components/DecisionCard'
import PatternAlert from '../components/PatternAlert'
import QueryBox from '../components/QueryBox'
import StreamingResponse from '../components/StreamingResponse'

export default function Dashboard() {
  const [repos, setRepos] = useState([])
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [patterns, setPatterns] = useState([])
  const [answer, setAnswer] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [showAddRepo, setShowAddRepo] = useState(false)
  const [newRepoInput, setNewRepoInput] = useState('')
  const [addError, setAddError] = useState('')

  useEffect(() => {
    loadRepos()
  }, [])

  useEffect(() => {
    if (selectedRepo) {
      loadDecisions()
      loadPatterns()
    }
  }, [selectedRepo])

  async function loadRepos() {
    const data = await getRepos()
    setRepos(data)
    if (data.length > 0 && !selectedRepo) setSelectedRepo(data[0])
  }

  async function loadDecisions() {
    const data = await getDecisions(selectedRepo.id)
    setDecisions(data)
  }

  async function loadPatterns() {
    const data = await getPatterns(selectedRepo.id)
    setPatterns(data)
  }

  async function handleSync() {
    if (!selectedRepo || syncing) return
    setSyncing(true)
    await triggerSync(selectedRepo.id)
    setTimeout(async () => {
      await loadDecisions()
      await loadPatterns()
      setSyncing(false)
    }, 3000)
  }

  function handleQuery(question) {
    setAnswer('')
    setIsStreaming(true)
    streamQuery(
      selectedRepo.id,
      question,
      (chunk) => setAnswer((prev) => prev + chunk),
      () => setIsStreaming(false),
    )
  }

  async function handleAddRepo(e) {
    e.preventDefault()
    setAddError('')
    const parts = newRepoInput.trim().split('/')
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
      setAddError('Enter as owner/repo (e.g. facebook/react)')
      return
    }
    try {
      const repo = await createRepo(parts[0], parts[1])
      setRepos((prev) => [...prev, repo])
      setSelectedRepo(repo)
      setShowAddRepo(false)
      setNewRepoInput('')
    } catch (err) {
      setAddError(err.message)
    }
  }

  const highPatterns = patterns.filter((p) => p.severity === 'high')

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🧠</span>
          <div>
            <h1 className="text-lg font-bold text-white">Shadow CTO</h1>
            <p className="text-xs text-slate-500">Engineering memory, powered by Hermes Agent</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Repo selector */}
          <select
            value={selectedRepo?.id || ''}
            onChange={(e) => {
              const repo = repos.find((r) => r.id === Number(e.target.value))
              setSelectedRepo(repo || null)
            }}
            className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none"
          >
            {repos.length === 0 && <option value="">No repos yet</option>}
            {repos.map((r) => (
              <option key={r.id} value={r.id}>
                {r.owner}/{r.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => setShowAddRepo(true)}
            className="text-sm px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-slate-300 transition-colors"
          >
            + Add Repo
          </button>

          {selectedRepo && (
            <button
              onClick={handleSync}
              disabled={syncing}
              className="text-sm px-3 py-2 bg-sky-700 hover:bg-sky-600 disabled:bg-slate-700 disabled:text-slate-500 rounded-lg text-white font-medium transition-colors"
            >
              {syncing ? 'Syncing...' : 'Sync GitHub'}
            </button>
          )}
        </div>
      </header>

      {/* Add repo modal */}
      {showAddRepo && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md">
            <h2 className="text-lg font-bold mb-4">Add GitHub Repository</h2>
            <form onSubmit={handleAddRepo} className="space-y-3">
              <input
                type="text"
                value={newRepoInput}
                onChange={(e) => setNewRepoInput(e.target.value)}
                placeholder="owner/repo-name"
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                autoFocus
              />
              {addError && <p className="text-red-400 text-sm">{addError}</p>}
              <div className="flex gap-2 pt-1">
                <button type="submit" className="flex-1 py-2.5 bg-sky-600 hover:bg-sky-500 rounded-lg text-sm font-semibold text-white transition-colors">
                  Add Repository
                </button>
                <button type="button" onClick={() => setShowAddRepo(false)} className="px-4 py-2.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-slate-300 transition-colors">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {!selectedRepo ? (
        <div className="flex flex-col items-center justify-center h-96 text-center">
          <span className="text-5xl mb-4">🔍</span>
          <h2 className="text-xl font-bold text-slate-300 mb-2">No repository tracked yet</h2>
          <p className="text-slate-500 mb-4">Add a GitHub repo to start building your engineering memory.</p>
          <button onClick={() => setShowAddRepo(true)} className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 rounded-lg text-white font-semibold transition-colors">
            Add Your First Repo
          </button>
        </div>
      ) : (
        <div className="max-w-7xl mx-auto px-6 py-6">
          {/* High severity pattern alerts */}
          {highPatterns.length > 0 && (
            <div className="mb-6 space-y-2">
              {highPatterns.map((p) => <PatternAlert key={p.id} pattern={p} />)}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Q&A */}
            <div className="space-y-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Ask Your Shadow CTO
                </h2>
                <QueryBox onSubmit={handleQuery} disabled={isStreaming} />
              </div>
              <StreamingResponse
                text={answer}
                isStreaming={isStreaming}
                placeholder="Ask why an engineering decision was made, what changed, or what patterns to watch."
              />
            </div>

            {/* Right: Decision timeline */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                  Engineering Decisions ({decisions.length})
                </h2>
                {selectedRepo?.last_sync_at && (
                  <span className="text-xs text-slate-600">
                    Synced {new Date(selectedRepo.last_sync_at).toLocaleDateString()}
                  </span>
                )}
              </div>
              {decisions.length === 0 ? (
                <div className="text-center py-12 text-slate-600">
                  <p className="text-sm">No decisions yet. Sync a repo to get started.</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto scrollbar-hide">
                  {decisions.map((d) => <DecisionCard key={d.id} decision={d} />)}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
