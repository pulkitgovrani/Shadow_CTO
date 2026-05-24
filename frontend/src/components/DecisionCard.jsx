const TYPE_COLORS = {
  addition: 'bg-emerald-900/50 text-emerald-300 border-emerald-700',
  removal: 'bg-red-900/50 text-red-300 border-red-700',
  refactor: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
  rollback: 'bg-orange-900/50 text-orange-300 border-orange-700',
  migration: 'bg-purple-900/50 text-purple-300 border-purple-700',
  security: 'bg-blue-900/50 text-blue-300 border-blue-700',
  performance: 'bg-cyan-900/50 text-cyan-300 border-cyan-700',
  config: 'bg-slate-700/50 text-slate-300 border-slate-600',
}

function formatDate(iso) {
  if (!iso) return 'unknown date'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function DecisionCard({ decision, compact = false }) {
  const colorClass = TYPE_COLORS[decision.decision_type] || 'bg-slate-700/50 text-slate-300 border-slate-600'

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 hover:border-slate-600 transition-colors">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${colorClass}`}>
              {decision.decision_type || 'other'}
            </span>
            <span className="text-xs text-slate-500">{formatDate(decision.occurred_at)}</span>
            <span className="text-xs text-slate-600 ml-auto">
              {Math.round((decision.confidence_score || 0.5) * 100)}% confidence
            </span>
          </div>
          <h3 className="font-semibold text-slate-100 text-sm leading-snug">{decision.title}</h3>
          {!compact && decision.rationale && (
            <p className="text-slate-400 text-xs mt-1 leading-relaxed line-clamp-3">
              {decision.rationale}
            </p>
          )}
          {decision.tags && decision.tags.length > 0 && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {decision.tags.slice(0, 4).map((tag) => (
                <span key={tag} className="text-xs bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
