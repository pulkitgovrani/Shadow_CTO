import { useState } from 'react'

const SUGGESTED = [
  'Why was the authentication system changed?',
  'What technical debt exists?',
  'What caused the most rollbacks?',
  'Which components have changed the most?',
  'What performance improvements were made?',
]

export default function QueryBox({ onSubmit, disabled }) {
  const [question, setQuestion] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!question.trim() || disabled) return
    onSubmit(question.trim())
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask your Shadow CTO anything about this codebase..."
          disabled={disabled}
          className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || !question.trim()}
          className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 disabled:text-slate-500 rounded-lg text-sm font-semibold transition-colors text-white"
        >
          {disabled ? 'Thinking...' : 'Ask'}
        </button>
      </form>
      <div className="flex gap-2 flex-wrap mt-2">
        {SUGGESTED.map((q) => (
          <button
            key={q}
            onClick={() => { setQuestion(q); onSubmit(q) }}
            disabled={disabled}
            className="text-xs text-slate-400 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-full px-3 py-1 transition-colors disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
