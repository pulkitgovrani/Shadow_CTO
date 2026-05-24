export default function StreamingResponse({ text, isStreaming, placeholder }) {
  if (!text && !isStreaming) {
    return (
      <div className="text-slate-500 text-sm italic text-center py-8">
        {placeholder || 'Ask a question to see the answer here.'}
      </div>
    )
  }

  return (
    <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-5 min-h-[120px]">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-2 h-2 rounded-full bg-sky-500 animate-pulse" />
        <span className="text-xs text-sky-400 font-medium">
          {isStreaming ? 'Shadow CTO is thinking...' : 'Shadow CTO'}
        </span>
      </div>
      <div
        className={`text-slate-200 text-sm leading-relaxed whitespace-pre-wrap ${isStreaming ? 'streaming' : ''}`}
        style={{ fontFamily: 'inherit' }}
      >
        {text}
      </div>
    </div>
  )
}
