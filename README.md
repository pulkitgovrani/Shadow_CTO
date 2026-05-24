# Shadow CTO

> "Your team forgot. Hermes didn't."

Shadow CTO is a persistent AI system that watches your GitHub repository and builds institutional memory of **why** engineering decisions were made. Ask it "Why was Redis removed?" and it answers with the actual commit, PR, and reasoning — not a guess.

Built with [Hermes Agent](https://hermes-agent.nousresearch.com/) for the [DEV.to Hermes Agent Challenge](https://dev.to/challenges/hermes-agent-2026-05-15).

---

## What It Does

- **Syncs** commits, PRs, and issues from any public GitHub repository
- **Feeds** each event into Hermes Agent's persistent memory (per-repo session)
- **Extracts** engineering decisions with rationale and classification
- **Answers** natural language questions about why things changed (streamed live)
- **Detects** recurring failure patterns autonomously via daily cron job
- **Schedules** hourly GitHub sync and daily pattern analysis automatically

## How Hermes Is Used

| Feature | Hermes Capability |
|---------|------------------|
| Per-repo persistent memory | One `X-Hermes-Session-Id` per repo, accumulates indefinitely |
| Decision extraction | LLM reasoning over commit/PR context |
| Natural language Q&A | Hermes answers from its own memory |
| Pattern detection | Autonomous daily analysis of accumulated decisions |
| Cron jobs | Registered via Hermes `/api/jobs` endpoint |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Hermes Agent](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart) running locally
- GitHub token (optional, increases API rate limit)

### 1. Start Hermes Agent
```bash
# Follow Hermes install guide, then:
hermes serve
# Hermes API should be available at http://localhost:11434
```

### 2. Backend Setup
```bash
cd shadow-cto/backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set GITHUB_TOKEN for higher rate limits
uvicorn main:app --reload --port 8001
```

### 3. Frontend Setup
```bash
cd shadow-cto/frontend
npm install
npm run dev
# Open http://localhost:5173
```

### 4. Add a Repository
1. Click **+ Add Repo** in the top nav
2. Enter `owner/repo` (e.g. `facebook/react`)
3. Click **Sync GitHub** to fetch history
4. Watch decisions appear and start asking questions

---

## Demo Questions to Ask

- "Why was the authentication system changed?"
- "What technical debt exists in this codebase?"
- "Which decisions got reversed over time?"
- "What performance improvements were made and why?"
- "What should I be worried about before the next release?"

---

## Architecture

```
GitHub API
    │
    ▼
github_service.py ──► ingestion.py ──► Hermes Agent (persistent memory)
                                              │
                                              ▼
                                     decision extraction
                                              │
                                              ▼
                                         SQLite DB
                                              │
                                         FastAPI REST
                                              │
                                         React frontend
```

---

## Cron Jobs

Two jobs run automatically:
- **Hourly**: Sync new GitHub events → feed to Hermes memory
- **Daily 2am**: Ask Hermes to detect recurring failure patterns

Both are registered with Hermes's `/api/jobs` endpoint (visible in the **Autonomous Jobs** tab).

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HERMES_BASE_URL` | `http://localhost:11434` | Hermes API server URL |
| `HERMES_API_KEY` | `hermes` | Hermes API key |
| `GITHUB_TOKEN` | — | GitHub PAT for higher rate limits |
| `DATABASE_URL` | `sqlite+aiosqlite:///./shadow_cto.db` | Database path |
| `BACKEND_URL` | `http://localhost:8001` | This backend's URL (for cron callbacks) |
