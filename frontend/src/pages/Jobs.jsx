import { useEffect, useState } from 'react'
import { getJobs } from '../api'

export default function Jobs() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getJobs()
      .then((data) => { setJobs(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => { setError('Could not reach Hermes scheduler'); setLoading(false) })
  }, [])

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Autonomous Jobs</h1>
        <p className="text-slate-500 text-sm mt-1">
          These cron jobs are registered with Hermes Agent and run autonomously
        </p>
      </div>

      {loading ? (
        <div className="text-slate-500 text-sm">Loading jobs from Hermes...</div>
      ) : error ? (
        <div className="bg-red-950 border border-red-700 rounded-xl p-4 text-red-300 text-sm">
          {error} — Make sure Hermes Agent is running.
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-12 text-slate-600">
          <span className="text-4xl block mb-3">⏰</span>
          <p>No jobs registered. Start the backend to register Hermes cron jobs.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-100 text-sm">{job.name || `Job ${i + 1}`}</span>
                <span className="text-xs bg-emerald-900/50 text-emerald-400 border border-emerald-700 px-2 py-0.5 rounded">
                  {job.active === false ? 'paused' : 'active'}
                </span>
              </div>
              <div className="text-xs text-slate-500 font-mono mb-2">{job.schedule || job.cron}</div>
              {job.prompt && (
                <p className="text-xs text-slate-400 line-clamp-2">{job.prompt}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Built-in APScheduler jobs */}
      <div className="mt-8">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
          APScheduler Jobs (Backend)
        </h2>
        <div className="space-y-3">
          {[
            { name: 'hourly_github_sync', schedule: '0 * * * *', description: 'Fetch new commits, PRs, and issues from GitHub and feed into Hermes memory.' },
            { name: 'daily_pattern_analysis', schedule: '0 2 * * *', description: 'Ask Hermes to review accumulated memory and detect recurring engineering failure patterns.' },
          ].map((job) => (
            <div key={job.name} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-slate-100 text-sm">{job.name}</span>
                <span className="text-xs bg-sky-900/50 text-sky-400 border border-sky-700 px-2 py-0.5 rounded">active</span>
              </div>
              <div className="text-xs text-slate-500 font-mono mb-1">{job.schedule}</div>
              <p className="text-xs text-slate-400">{job.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
