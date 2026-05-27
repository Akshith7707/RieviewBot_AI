# ReviewBot AI — Project Roadmap

Your single file to understand **what exists**, **what to do next**, and **how to stand out** vs tools like CodeRabbit.

---

## Status board (MVP)

| Item | Status |
|------|--------|
| FastAPI server + health check | Done |
| GitHub webhook (`POST /webhook/github`) | Done |
| GitLab webhook (`POST /webhook/gitlab`) | Done |
| Webhook signature verification | Done |
| GitHub API client (diff, comments, review) | Done |
| GitLab API client (MR diff, discussions) | Done |
| Diff parser + chunking | Done |
| OWASP security pre-scan (`rules/security.yaml`) | Done |
| LLM review (Groq → Together → HF → Ollama) | Done |
| SQLite job + issue storage | Done |
| Manual review API (`POST /api/review`) | Done |
| `.env.example` with setup hints | Done |
| RL feedback loop (`POST /api/feedback`, feedback log) | Done |
| React dashboard (Vite + live stats) | Done |
| Redis job queue | Not started |
| ChromaDB review memory | Not started |
| Custom rule DSL editor | Not started |
| Docker Compose deploy | Not started |

---

## How it works (plain English)

1. You open or update a **Pull Request** (GitHub) or **Merge Request** (GitLab).
2. The platform sends a **webhook** to your ReviewBot server.
3. ReviewBot **verifies** the webhook is authentic (secret token).
4. It **downloads the diff** from GitHub/GitLab.
5. **Security rules** run first (regex OWASP patterns — free, fast, private).
6. **AI (LLM)** reviews each file chunk with project context (README, full file, PR description).
7. Findings are **deduplicated**, capped (default 15 comments), and posted as one **review** with inline comments + summary.
8. Results are saved in **SQLite** so you can query them via API.

```
PR opened → Webhook → Verify → Fetch diff → Security scan → LLM review → Post comments → SQLite
```

---

## Quick start

```powershell
# Windows
copy .env.example .env
# Edit .env — at minimum set GROQ_API_KEY and GITHUB_TOKEN (or GITLAB_TOKEN)
.\scripts\run_server.ps1
```

```bash
# Linux/macOS
cp .env.example .env
chmod +x scripts/run_server.sh
./scripts/run_server.sh
```

Server: http://localhost:8000  
Docs: http://localhost:8000/docs  
Health: http://localhost:8000/health

---

## API setup walkthrough

### 1. Groq (recommended — primary LLM)

| Step | Action |
|------|--------|
| 1 | Go to [console.groq.com](https://console.groq.com) |
| 2 | Sign up / log in |
| 3 | **API Keys** → Create API Key |
| 4 | Copy key into `.env` → `GROQ_API_KEY=gsk_...` |

Free tier: ~14,400 requests/day. Fast inference.

### 2. GitHub

| Step | Action |
|------|--------|
| 1 | [github.com/settings/tokens](https://github.com/settings/tokens) |
| 2 | **Generate new token (classic)** or fine-grained token |
| 3 | Scopes: `repo`, `pull_requests` (read + write) |
| 4 | Copy → `GITHUB_TOKEN=ghp_...` |
| 5 | Generate random secret: `openssl rand -hex 32` (or any password generator) |
| 6 | Set `GITHUB_WEBHOOK_SECRET=` to that value |

### 3. GitLab

| Step | Action |
|------|--------|
| 1 | GitLab → **Preferences** → **Access Tokens** |
| 2 | Scopes: `api`, `read_repository`, `write_repository` |
| 3 | Copy → `GITLAB_TOKEN=glpat-...` |
| 4 | Set `GITLAB_WEBHOOK_SECRET=` (same idea as GitHub) |
| 5 | Self-hosted? Set `GITLAB_URL=https://your.gitlab.instance` |

### 4. Optional LLM fallbacks

| Provider | Get key | Env variable |
|----------|---------|--------------|
| Together AI | [api.together.xyz](https://api.together.xyz) | `TOGETHER_API_KEY` |
| Hugging Face | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) | `HF_API_TOKEN` |
| Ollama (local) | [ollama.com](https://ollama.com) → `ollama pull codellama` | `OLLAMA_BASE_URL` (no key) |

Fallback order: **Groq → Together → HuggingFace → Ollama**

### 5. Optional (post-MVP)

| Service | Purpose | Env |
|---------|---------|-----|
| Upstash | Redis queue for high traffic | `REDIS_URL` |
| Slack | Review notifications | `SLACK_WEBHOOK_URL` |
| Discord | Review notifications | `DISCORD_WEBHOOK_URL` |

---

## Webhook setup

### Local development (ngrok)

```bash
ngrok http 8000
```

Use the HTTPS URL ngrok gives you, e.g. `https://abc123.ngrok.io/webhook/github`

### GitHub repository webhook

1. Repo → **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL:** `https://YOUR_DOMAIN/webhook/github`
3. **Content type:** `application/json`
4. **Secret:** same as `GITHUB_WEBHOOK_SECRET` in `.env`
5. **Events:** Pull requests only
6. Save

### GitLab project webhook

1. Project → **Settings** → **Webhooks**
2. **URL:** `https://YOUR_DOMAIN/webhook/gitlab`
3. **Secret token:** same as `GITLAB_WEBHOOK_SECRET`
4. Trigger: **Merge request events**
5. Save

---

## Manual test (no webhook)

```bash
curl -X POST http://localhost:8000/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "github",
    "owner": "YOUR_USER",
    "repo": "YOUR_REPO",
    "pr_number": 1,
    "title": "Test PR",
    "description": "Testing ReviewBot"
  }'
```

Response includes `job_id`. Check status:

```bash
curl http://localhost:8000/api/reviews/JOB_ID_HERE
```

---

## Post-MVP backlog (prioritized)

### P1 — High impact

- [ ] **RL feedback loop** — 👍/👎 on comments; store in SQLite; fine-tune reward model (TRL)
- [ ] **Redis queue** (Upstash) — survive webhook bursts; retry failed reviews
- [ ] **Reaction webhook** — GitHub `issue_comment` / reaction events for feedback

### P2 — Differentiators

- [ ] **Complexity analyzer** — radon (Python), lizard (multi-lang)
- [ ] **Custom YAML rule engine** — team policies beyond security
- [ ] **ChromaDB review memory** — “we flagged this pattern before in this repo”
- [ ] **`.reviewbot.yaml`** per repo — ignore rules, severity threshold

### P3 — Product polish

- [ ] **React dashboard** — stats, PR viewer, feedback log, rule editor
- [ ] **Auto test suggestions** — generate test stubs for changed functions
- [ ] **Doc patcher** — suggest README/docstring updates
- [ ] **PR walkthrough** — narrative summary of changes

### P4 — Ops

- [ ] **Docker Compose** — backend + redis + optional frontend
- [ ] **Deploy guides** — Railway, Render, Fly.io
- [ ] **Slack/Discord notifications** — alert on critical findings

---

## Enhancement ideas (make it stand out)

| Idea | Why it matters |
|------|----------------|
| **Security-first pipeline** | OWASP scan before LLM = faster, cheaper, no data sent for obvious bugs |
| **Open model chain** | Not locked to OpenAI; Groq + local Ollama for sensitive code |
| **Dual platform day one** | GitHub + GitLab in MVP — many competitors pick one |
| **Per-developer RL preferences** | Learn who wants terse vs verbose reviews |
| **Confirmed bug pattern DB** | When dev fixes your suggestion, embed pattern in ChromaDB; warn earlier next time |
| **Review quality KPIs** | True/false positive rate, latency, coverage % — show in dashboard |
| **Private mode** | Env flag: `LLM_PROVIDER=ollama` only — zero external API calls |

---

## vs CodeRabbit

| | CodeRabbit | ReviewBot AI |
|---|------------|--------------|
| Cost | Paid SaaS | Self-hosted, free API tiers |
| Model | Closed | Open (Groq, Ollama, etc.) |
| Learns from feedback | Limited | Planned (RL — P1 backlog) |
| Security pre-scan | Basic | OWASP YAML rules before LLM |
| Data control | Their cloud | Your server / Ollama local |
| Custom rules | Limited | Planned full DSL |

---

## Project layout

```
code_rabbit/
├── backend/           # FastAPI app
├── rules/             # security.yaml (expandable)
├── scripts/           # run_server.ps1 / .sh
├── data/              # SQLite (auto-created)
├── .env.example       # copy to .env
├── PROJECT_ROADMAP.md # this file
└── README.md          # quick reference
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No LLM API key` warning | Set `GROQ_API_KEY` in `.env` |
| 401 on webhook | `GITHUB_WEBHOOK_SECRET` / `GITLAB_WEBHOOK_SECRET` must match portal |
| Empty review | PR may have only binary files; check diff via GitHub UI |
| LLM JSON parse errors | Check logs; fallback providers tried automatically |
| GitLab inline comments fail | Ensure token has `api` scope; MR must be open |

---

*Last updated: MVP v0.1.0 — see `codereviewer_ai_build_plan.md` for full original vision.*
