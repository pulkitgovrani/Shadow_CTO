const SEVERITY_STYLES = {
  high: 'bg-red-950 border-red-700 text-red-300',
  medium: 'bg-orange-950 border-orange-700 text-orange-300',
  low: 'bg-yellow-950 border-yellow-700 text-yellow-300',
}

export default function PatternAlert({ pattern }) {
  const style = SEVERITY_STYLES[pattern.severity] || SEVERITY_STYLES.medium

  return (
    <div className={`border rounded-xl p-4 ${style}`}>
      <div className="flex items-start gap-3">
        <span className="text-xl mt-0.5">
          {pattern.severity === 'high' ? '🔴' : pattern.severity === 'medium' ? '🟡' : '🟢'}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-sm">{pattern.pattern_name}</span>
            <span className="text-xs opacity-70 ml-auto">{pattern.occurrences}× detected</span>
          </div>
          <p className="text-xs opacity-80 leading-relaxed">{pattern.description}</p>
        </div>
      </div>
    </div>
  )
}
