const BASE = '/api'

export async function getRepos() {
  const r = await fetch(`${BASE}/repos`)
  return r.json()
}

export async function createRepo(owner, name) {
  const r = await fetch(`${BASE}/repos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ owner, name }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function triggerSync(repoId) {
  const r = await fetch(`${BASE}/sync/${repoId}`, { method: 'POST' })
  return r.json()
}

export async function getSyncStatus(repoId) {
  const r = await fetch(`${BASE}/sync/${repoId}/status`)
  return r.json()
}

export async function getDecisions(repoId, type = null) {
  const url = type
    ? `${BASE}/decisions/${repoId}?decision_type=${type}`
    : `${BASE}/decisions/${repoId}`
  const r = await fetch(url)
  return r.json()
}

export async function getPatterns(repoId) {
  const r = await fetch(`${BASE}/patterns/${repoId}`)
  return r.json()
}

export async function analyzePatterns(repoId) {
  const r = await fetch(`${BASE}/patterns/analyze/${repoId}`, { method: 'POST' })
  return r.json()
}

export async function getJobs() {
  const r = await fetch(`${BASE}/jobs`)
  return r.json()
}

export function streamQuery(repoId, question, onChunk, onDone) {
  fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_id: repoId, question }),
  }).then(async (response) => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            onDone?.()
            return
          }
          onChunk(data.replace(/\\n/g, '\n'))
        }
      }
    }
    onDone?.()
  }).catch((err) => {
    onChunk(`\n[Error: ${err.message}]`)
    onDone?.()
  })
}
