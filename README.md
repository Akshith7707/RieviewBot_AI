# ReviewBot AI

Self-hosted AI code reviewer for **GitHub** and **GitLab**. Security rules run before the LLM. Learns from feedback (roadmap).

## Features

- Automatic PR/MR reviews via webhooks
- OWASP-style security pre-scan (no API cost)
- LLM review with fallback: Groq → Together → HuggingFace → Ollama
- Inline comments + summary on the PR
- **React dashboard** — live stats, job detail, issue viewer
- **RL feedback loop** — 👍/👎 per finding (trains future reviews)
- SQLite storage + REST API for job status
- Manual trigger: `POST /api/review`

## 5-minute setup

1. **Clone** and copy env file:
   ```bash
   cp .env.example .env
   ```

2. **Add keys** (minimum):
   - `GROQ_API_KEY` — [console.groq.com](https://console.groq.com)
   - `GITHUB_TOKEN` and/or `GITLAB_TOKEN` — see [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md)

3. **Run server** (Windows):
   ```powershell
   .\scripts\run_server.ps1
   ```
   Or Linux/macOS: `./scripts/run_server.sh`

3b. **Run dashboard** (second terminal):
   ```powershell
   .\scripts\run_dashboard.ps1
   ```
   Open http://localhost:5173 — see every review, rate findings, beat Copilot visibility.

4. **Expose locally** (for webhooks):
   ```bash
   ngrok http 8000
   ```

5. **Configure webhook** on your repo → point to `/webhook/github` or `/webhook/gitlab`

Full guides: **[PROJECT_ROADMAP.md](PROJECT_ROADMAP.md)**

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Server status + config warnings |
| POST | `/webhook/github` | GitHub PR events |
| POST | `/webhook/gitlab` | GitLab MR events |
| POST | `/api/review` | Trigger review manually |
| GET | `/api/reviews/{job_id}` | Job status + issues |
| GET | `/api/stats` | Dashboard metrics |
| POST | `/api/feedback` | 👍/👎 RL feedback |
| GET | `/api/feedback` | Feedback history |
| GET | `/docs` | OpenAPI (Swagger) UI |

## Environment variables

See [`.env.example`](.env.example) — every key includes a **HOW TO GET** comment.

## Development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
export PYTHONPATH=.         # Windows: $env:PYTHONPATH="."
python -m uvicorn backend.main:app --reload
```

## License

MIT (add LICENSE file if you publish)

## Roadmap

See [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) for todos, enhancements, and post-MVP priorities.
# RieviewBot_AI
