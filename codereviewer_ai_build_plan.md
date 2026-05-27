# 🤖 AI Code Reviewer — Full Build Plan
### A CodeRabbit Alternative with Reinforcement Learning + Advanced Features
> Give this entire file to Claude as your prompt. It contains everything needed to build the system.

---

## 🧠 PROJECT OVERVIEW

Build a **self-hosted, AI-powered code review system** called **ReviewBot AI** that:
- Automatically reviews Pull Requests and pushes inline comments to GitHub/GitLab
- Learns from developer feedback via Reinforcement Learning (RLHF-lite)
- Detects security vulnerabilities, performance issues, logic bugs, and style violations
- Generates test suggestions, refactoring ideas, and documentation patches
- Runs 100% free using open-source models and free API tiers

---

## 🆚 HOW IT BEATS CODERABBIT

| Feature | CodeRabbit | ReviewBot AI |
|---|---|---|
| Pricing | Paid ($12/mo+) | Free (self-hosted) |
| Model | Closed, black-box | Open (Mistral/CodeLlama) |
| Learns from feedback | ❌ No | ✅ Yes (RL feedback loop) |
| Security scanning | Basic | Deep (OWASP + SAST) |
| Auto test generation | ❌ No | ✅ Yes |
| Auto doc patching | ❌ No | ✅ Yes |
| Custom rules engine | Limited | ✅ Full DSL support |
| Complexity analysis | ❌ No | ✅ Cyclomatic + Cognitive |
| Review memory | ❌ No | ✅ Remembers past reviews |
| Multi-repo learning | ❌ No | ✅ Cross-repo pattern DB |

---

## 📁 PROJECT STRUCTURE

```
reviewbot-ai/
├── backend/
│   ├── main.py                   # FastAPI entrypoint
│   ├── webhook_handler.py        # GitHub/GitLab webhook receiver
│   ├── review_engine/
│   │   ├── diff_parser.py        # Parse PR diffs into chunks
│   │   ├── context_builder.py    # Build context for LLM
│   │   ├── llm_reviewer.py       # LLM inference logic
│   │   ├── security_scanner.py   # OWASP/SAST rules engine
│   │   ├── complexity_analyzer.py# Cyclomatic + cognitive complexity
│   │   ├── test_generator.py     # Auto test suggestion engine
│   │   ├── doc_patcher.py        # Auto documentation updater
│   │   └── rule_engine.py        # Custom DSL rules evaluator
│   ├── rl/
│   │   ├── feedback_collector.py # Collect thumbs up/down from devs
│   │   ├── reward_model.py       # Train reward model on feedback
│   │   ├── ppo_trainer.py        # PPO fine-tuning loop
│   │   └── feedback_db.py        # SQLite store for feedback
│   ├── memory/
│   │   ├── review_memory.py      # Store past reviews per repo
│   │   ├── pattern_db.py         # Cross-repo bug pattern learning
│   │   └── vector_store.py       # ChromaDB for semantic search
│   ├── integrations/
│   │   ├── github_client.py      # GitHub API v3 + GraphQL
│   │   ├── gitlab_client.py      # GitLab API client
│   │   └── notification.py       # Slack/Discord/Email alerts
│   └── config.py                 # All configuration
├── frontend/
│   ├── dashboard/                # React dashboard (Vite)
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   │   ├── Dashboard.jsx   # Review stats overview
│   │   │   │   ├── PRView.jsx      # Per-PR review viewer
│   │   │   │   ├── FeedbackLog.jsx # RL feedback history
│   │   │   │   ├── RuleEditor.jsx  # Custom rules editor
│   │   │   │   └── Settings.jsx    # Config UI
│   │   │   ├── components/
│   │   │   │   ├── DiffViewer.jsx  # GitHub-style diff viewer
│   │   │   │   ├── CommentCard.jsx # AI comment display
│   │   │   │   ├── FeedbackBtn.jsx # 👍/👎 feedback buttons
│   │   │   │   └── MetricsChart.jsx# Review quality over time
│   │   │   └── App.jsx
│   │   └── package.json
├── models/
│   ├── base_model/               # Downloaded model weights
│   └── finetuned/                # RL fine-tuned checkpoints
├── rules/
│   ├── security.yaml             # OWASP security rules
│   ├── performance.yaml          # Performance anti-patterns
│   ├── style.yaml                # Language-specific style rules
│   └── custom.yaml               # User-defined rules
├── scripts/
│   ├── setup.sh                  # One-shot setup script
│   ├── run_server.sh             # Start backend
│   └── train_rl.sh               # Trigger RL training cycle
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔧 TECH STACK (ALL FREE)

### Backend
| Component | Technology | Why Free |
|---|---|---|
| API Server | FastAPI (Python) | Open source |
| LLM | Groq API (Llama 3.1 70B) | Free tier 14,400 req/day |
| Backup LLM | Hugging Face Inference API | Free tier |
| Local LLM fallback | Ollama + CodeLlama 13B | Runs locally |
| Vector DB | ChromaDB | Open source |
| SQL DB | SQLite → PostgreSQL | Open source |
| Queue | Redis (via Upstash free tier) | Free 10k cmd/day |

### RL Stack
| Component | Technology |
|---|---|
| Feedback collection | Custom SQLite + FastAPI |
| Reward model | TRL (Hugging Face) |
| PPO trainer | TRL PPOTrainer |
| Base model | microsoft/codebert-base or deepseek-coder-1.3b |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 18 + Vite |
| UI Components | shadcn/ui + Tailwind CSS |
| Diff viewer | react-diff-viewer-continued |
| Charts | Recharts |
| State | Zustand |

### DevOps
| Component | Technology |
|---|---|
| Hosting backend | Railway / Render (free tier) |
| Hosting frontend | Vercel / Netlify (free) |
| Secrets | .env file / Railway env vars |
| Webhook tunnel (dev) | ngrok (free) |

---

## 🔑 FREE API KEYS NEEDED

```bash
# .env.example

# === LLM APIs (pick one or all for fallback chain) ===
GROQ_API_KEY=         # Free at console.groq.com — 14,400 req/day
HF_API_TOKEN=         # Free at huggingface.co — inference API
TOGETHER_API_KEY=     # Free $25 credit at api.together.xyz

# === Git Platforms ===
GITHUB_TOKEN=         # Free — github.com/settings/tokens (needs repo, pull_requests scope)
GITHUB_WEBHOOK_SECRET=# Random string you set

# === Optional Notifications ===
SLACK_WEBHOOK_URL=    # Free Slack app webhook
DISCORD_WEBHOOK_URL=  # Free Discord webhook

# === Storage ===
REDIS_URL=            # Free at upstash.com (10k commands/day)
DATABASE_URL=sqlite:///./reviewbot.db  # Local SQLite (free)
```

---

## 🏗️ PHASE-BY-PHASE BUILD PLAN

---

### PHASE 1 — Core Infrastructure (Days 1–3)

#### 1.1 FastAPI Server + Webhook Handler

```python
# backend/webhook_handler.py
# Build this first — it's the entry point for everything

"""
Implement:
1. POST /webhook/github  — receive GitHub PR events
2. POST /webhook/gitlab  — receive GitLab MR events
3. Verify webhook signature (HMAC-SHA256)
4. Parse event: PR opened, PR updated, PR review_comment
5. Queue review job to Redis
6. Return 200 immediately (async processing)

Webhook payload parsing:
- Extract: repo name, PR number, head SHA, base SHA, author, title, body
- Fetch full diff via GitHub API: GET /repos/{owner}/{repo}/pulls/{pull_number}/files
- Store raw diff in SQLite for later
"""
```

#### 1.2 GitHub API Client

```python
# backend/integrations/github_client.py

"""
Implement these methods:
- get_pr_diff(owner, repo, pr_number) → list of file diffs
- get_pr_files(owner, repo, pr_number) → list of changed files with metadata
- post_review_comment(owner, repo, pr_number, commit_id, path, line, body)
- post_pr_summary(owner, repo, pr_number, body)  
- react_to_comment(owner, repo, comment_id, reaction)  # for feedback
- get_file_content(owner, repo, path, ref)  # get full file for context

Use PyGithub library: pip install PyGithub
Rate limit: 5,000 requests/hour (free authenticated)
"""
```

#### 1.3 Diff Parser

```python
# backend/review_engine/diff_parser.py

"""
Parse unified diff format into structured chunks.

Output format per chunk:
{
  "file_path": "src/auth/login.py",
  "language": "python",
  "change_type": "modified",  # added/deleted/modified/renamed
  "old_path": "src/auth/login.py",
  "additions": 23,
  "deletions": 5,
  "hunks": [
    {
      "old_start": 45,
      "new_start": 45,
      "context_before": ["line 43 code", "line 44 code"],
      "changes": [
        {"type": "add", "line_no": 46, "content": "+ new code here"},
        {"type": "del", "line_no": 46, "content": "- old code here"},
      ],
      "context_after": ["line 47 code"]
    }
  ]
}

Also implement:
- detect_language(file_path) → language string using file extension map
- chunk_large_diff(diff, max_tokens=3000) → split for LLM context window
- extract_function_signatures(diff) → detect which functions changed
"""
```

---

### PHASE 2 — LLM Review Engine (Days 4–7)

#### 2.1 LLM Client with Fallback Chain

```python
# backend/review_engine/llm_reviewer.py

"""
Build a fallback chain LLM client:

Priority order:
1. Groq (fastest, free 14k req/day) — llama-3.1-70b-versatile
2. Together AI (free $25 credit) — deepseek-coder-33b
3. HuggingFace Inference API — bigcode/starcoder2-15b
4. Ollama local — codellama:13b (if running locally)

For each diff chunk, generate a structured review:
{
  "summary": "Brief description of what this code does",
  "issues": [
    {
      "severity": "critical|high|medium|low|info",
      "category": "security|performance|bug|style|maintainability",
      "line_number": 47,
      "title": "SQL Injection Vulnerability",
      "description": "User input is concatenated directly into SQL query",
      "suggestion": "Use parameterized queries instead: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
      "confidence": 0.92
    }
  ],
  "positive_feedback": ["Good use of type hints", "Well-structured error handling"],
  "refactoring_suggestion": "Consider extracting lines 45-67 into a separate function",
  "complexity_score": 7
}

System prompt to use:
---
You are an expert code reviewer with 15+ years of experience. 
Review the following code diff and provide structured feedback.
Focus on: bugs, security vulnerabilities, performance issues, maintainability.
Be specific, actionable, and kind. Reference exact line numbers.
Respond ONLY in valid JSON matching the schema provided.
Do NOT include markdown formatting or explanations outside JSON.
---
"""
```

#### 2.2 Context Builder

```python
# backend/review_engine/context_builder.py

"""
Build rich context for each review chunk:

1. REPO CONTEXT: Fetch README.md first 500 chars for project understanding
2. FILE CONTEXT: Get full file content (not just diff) for the changed file
3. RELATED FILES: Find imports/dependencies and include their signatures
4. PAST REVIEWS: Query vector store for similar code reviewed before
5. PR DESCRIPTION: Include PR title + body as context
6. STYLE GUIDE: Load repo-specific .reviewbot.yaml if exists

Context template:
---
## Project: {repo_name}
{readme_snippet}

## PR Goal
{pr_title}: {pr_description}

## File Being Reviewed: {file_path} ({language})

## Full File (for context)
{full_file_content}

## Changes (diff)
{diff_hunk}

## Similar Past Issues Found In This Repo
{similar_issues_from_memory}

## Review this diff carefully and return JSON.
---

Token budget management:
- Full file: max 2000 tokens
- Diff: max 1500 tokens  
- Memory/context: max 500 tokens
- Total: keep under 4000 tokens
"""
```

#### 2.3 Comment Poster

```python
# backend/integrations/github_client.py (extend)

"""
Post review as GitHub PR Review (not individual comments):
- Use createReview API to batch all comments in one review
- Attach inline comments to exact line numbers
- Post summary as review body
- Set review state: COMMENT (not approve/request changes — let humans decide)

Comment format to post:
---
{severity_emoji} **{category}** — {title}

{description}

💡 **Suggestion:**
```{language}
{suggestion_code}
```

*Confidence: {confidence}% | [👍 Helpful](#) [👎 Not helpful](#)*
---

Severity emojis:
- critical: 🚨
- high: ⚠️
- medium: 📝
- low: 💡
- info: ℹ️
"""
```

---

### PHASE 3 — Static Analysis & Security (Days 8–10)

#### 3.1 Security Scanner

```python
# backend/review_engine/security_scanner.py

"""
Implement rule-based OWASP security scanner that runs BEFORE LLM
(fast, deterministic, no API cost):

Languages to support: Python, JavaScript, TypeScript, Java, Go, Ruby

OWASP Top 10 patterns to detect:

1. SQL Injection:
   - Regex: r'(execute|query)\s*\(\s*["\'].*\+|f["\'].*SELECT'
   - Languages: Python, Java, JS
   
2. XSS:
   - Regex: r'innerHTML\s*=|document\.write\s*\(|\.html\s*\('
   - Context: only in JS/TS files
   
3. Hardcoded Secrets:
   - Regex: r'(password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}'
   - ALL languages
   
4. Path Traversal:
   - Regex: r'open\s*\(\s*.*\+|readFile\s*\(\s*req\.'
   
5. Command Injection:
   - Python: r'os\.system\s*\(|subprocess.*shell=True'
   - JS: r'exec\s*\(\s*`|child_process.*\$\{'
   
6. Insecure Deserialization:
   - Python: r'pickle\.loads|yaml\.load\s*\([^,\)]*\)'
   - JS: r'JSON\.parse\s*\(.*req\.'

7. Weak Cryptography:
   - Regex: r'md5\(|sha1\(|DES\.|RC4\.'

8. Open Redirect:
   - Regex: r'redirect\s*\(\s*request\.|HttpResponseRedirect\s*\(\s*request\.'

Return format:
{
  "vulnerabilities": [
    {
      "cwe": "CWE-89",
      "owasp": "A03:2021",
      "severity": "critical",
      "line_number": 45,
      "matched_text": "cursor.execute('SELECT * FROM users WHERE id = ' + user_id)",
      "rule_id": "SQL_INJECTION_001",
      "title": "SQL Injection via string concatenation",
      "remediation": "Use parameterized queries"
    }
  ]
}
"""
```

#### 3.2 Complexity Analyzer

```python
# backend/review_engine/complexity_analyzer.py

"""
Analyze code complexity using radon (Python) or custom AST walking:

pip install radon lizard

Metrics to compute:
1. Cyclomatic Complexity (CC):
   - Count: if, elif, else, for, while, try, except, with, and, or, ternary
   - Score 1-5: Simple
   - Score 6-10: Moderate (flag)
   - Score 11-15: High (warn)
   - Score 16+: Very High (critical — must refactor)

2. Cognitive Complexity:
   - Like CC but weights nested conditions higher
   - Penalize: nested loops (+2 per nesting level)

3. Lines of Code per function:
   - >50 lines: warn
   - >100 lines: flag for splitting

4. Parameter count:
   - >5 params: suggest using a config object/dataclass

5. Return paths:
   - >4 return statements: flag complexity

Output:
{
  "functions": [
    {
      "name": "process_user_data",
      "line_start": 45,
      "line_end": 112,
      "cyclomatic_complexity": 14,
      "cognitive_complexity": 22,
      "loc": 67,
      "param_count": 7,
      "issues": ["too_complex", "too_long", "too_many_params"]
    }
  ],
  "file_complexity": "high",
  "refactor_priority": "urgent"
}
"""
```

#### 3.3 Custom Rules Engine (DSL)

```yaml
# rules/custom.yaml — User-defined rules

rules:
  - id: NO_PRINT_STATEMENTS
    name: "No print() in production code"
    severity: low
    languages: [python]
    pattern: "^\\s*print\\("
    message: "Remove debug print statement. Use logging module instead."
    suggestion: "import logging\nlogger = logging.getLogger(__name__)\nlogger.info('message')"

  - id: ASYNC_IN_SYNC_CONTEXT
    name: "Await used outside async function"
    severity: high
    languages: [python, javascript, typescript]
    pattern: "(?<!async def .*)\\bawait\\b"
    message: "await used outside async function"

  - id: TODO_COMMENTS
    name: "Unresolved TODO"
    severity: info
    languages: all
    pattern: "#\\s*TODO|//\\s*TODO"
    message: "Unresolved TODO comment — create a ticket or resolve"

  - id: LARGE_FUNCTION
    name: "Function too large"
    type: ast_rule  # uses AST, not regex
    severity: medium
    languages: [python, javascript]
    max_lines: 50
    message: "Function exceeds {max_lines} lines. Consider splitting."
```

```python
# backend/review_engine/rule_engine.py

"""
Load and evaluate all YAML rule files.
Support two rule types:
1. pattern rules: regex match on changed lines
2. ast_rules: use AST analysis for structural checks

Also allow per-repo config via .reviewbot.yaml in repo root:
---
extends: default
ignore_rules: [TODO_COMMENTS]
custom_rules:
  - id: MY_RULE
    ...
severity_threshold: medium  # only report medium and above
max_comments_per_pr: 20     # don't spam
---
"""
```

---

### PHASE 4 — Extra Features Not In CodeRabbit (Days 11–15)

#### 4.1 Auto Test Generator

```python
# backend/review_engine/test_generator.py

"""
For each changed function, auto-generate test stubs.

Process:
1. Extract function signature + docstring + body from diff
2. Detect testing framework in repo (pytest, jest, vitest, go test, etc.)
3. Prompt LLM to generate tests covering:
   - Happy path
   - Edge cases (empty input, None, 0, max int, etc.)
   - Error cases (exceptions, invalid types)
   - Boundary conditions

Prompt template:
---
Given this function:
{function_code}

Generate {framework} tests that cover:
1. Normal usage (at least 2 cases)
2. Edge cases: empty/null inputs, boundary values
3. Error cases: what should raise exceptions
4. Any business logic edge cases you can infer

Return only the test code, ready to paste into a test file.
Test file convention for this repo: {test_convention}
---

Post as a separate PR comment:
"📋 **Suggested Tests for `{function_name}`**
Here are test cases to consider adding:
```python
{test_code}
```"
"""
```

#### 4.2 Auto Documentation Patcher

```python
# backend/review_engine/doc_patcher.py

"""
Detect when code changes but docs don't.

Checks:
1. Function has no docstring → suggest one
2. Docstring exists but params changed → suggest update
3. README mentions functionality that was modified → flag for doc update
4. API endpoint changed → flag OpenAPI spec update needed

For missing docstrings, generate them:
- Python: Google style or NumPy style (detect from existing code)
- JS/TS: JSDoc format
- Go: GoDoc format
- Java: Javadoc format

Example output comment:
"📖 **Documentation Missing**
`process_payment()` has no docstring. Here's a suggested one:
```python
def process_payment(amount: float, currency: str, method: PaymentMethod) -> PaymentResult:
    '''
    Process a payment transaction.
    
    Args:
        amount: Payment amount in the given currency
        currency: ISO 4217 currency code (e.g., 'USD', 'EUR')
        method: Payment method to use
        
    Returns:
        PaymentResult with transaction ID and status
        
    Raises:
        PaymentError: If the payment provider rejects the transaction
        ValueError: If amount is negative or currency is invalid
    '''
```"
"""
```

#### 4.3 Review Memory System

```python
# backend/memory/review_memory.py
# backend/memory/vector_store.py

"""
Use ChromaDB (free, local) as vector store.
pip install chromadb sentence-transformers

On every review:
1. Embed the code chunk using sentence-transformers (free, local)
   Model: 'microsoft/codebert-base' for code similarity
2. Store in ChromaDB with metadata: {repo, file, pr_number, issues_found, severity}

On new review:
1. Query ChromaDB for similar code (top-5 nearest neighbors)
2. If similar code had known issues before, BOOST confidence of same issue
3. Include in LLM context: "Similar code at path X had Y issue in PR #Z"

Cross-repo learning:
- Share embeddings across repos (same ChromaDB instance)
- Tag with language + pattern type for cross-repo queries
- "This pattern caused a bug in 3 other repos"

Also store:
- Per-repo review history in SQLite
- Which suggestions were accepted (from feedback loop)
- Which issues were later confirmed as real bugs (closed with fix commit)
"""
```

#### 4.4 PR Summary Generator

```python
# backend/review_engine/summarizer.py

"""
Generate a human-readable PR summary as the first review comment:

---
## 🤖 ReviewBot AI Summary

**What this PR does:**
{auto_generated_summary_of_changes}

**Risk Assessment:** 🟡 Medium
- 2 high severity issues found
- 5 medium severity issues found  
- Core auth logic modified (high-risk area)

**Files Changed:** 7 files (+234 / -89 lines)
| File | Risk | Issues |
|------|------|--------|
| src/auth/login.py | 🔴 High | SQL injection risk |
| src/utils/helpers.py | 🟢 Low | Style only |

**Recommended Review Order:**
1. `src/auth/login.py` — security critical
2. `src/api/routes.py` — business logic change
3. Others — low risk

**Auto-generated tests:** See comments on `login.py` and `payment.py`
---
"""
```

#### 4.5 PR Walkthrough (NEW — CodeRabbit doesn't do this well)

```python
# backend/review_engine/walkthrough.py

"""
Generate a step-by-step explanation of HOW to review this PR:

"To understand this PR, start by reading X which sets up the data model.
Then look at Y which adds the new endpoint. Finally check Z which updates
the frontend to use the new API."

This creates a narrative review path — very useful for large PRs.
Uses topological sort of imports to find natural review order.
"""
```

---

### PHASE 5 — Reinforcement Learning System (Days 16–22)

#### 5.1 Feedback Collection

```python
# backend/rl/feedback_collector.py

"""
Collect developer feedback on AI comments via:

1. GitHub Reaction API:
   - 👍 (+1) = Helpful comment
   - 👎 (-1) = Unhelpful comment
   - Monitor reaction events via webhook

2. Comment resolution:
   - If dev resolves a thread without action = probably false positive
   - If dev resolves a thread AFTER making a fix = true positive

3. PR merge signal:
   - If PR merged without fixing a "critical" issue = false positive
   - If PR author pushed a fix commit for flagged code = true positive

4. Dashboard feedback UI:
   - Show each AI comment with 👍/👎 buttons
   - Dropdown: "Why unhelpful? Too noisy / Wrong / Not actionable / Already knew"

Store all feedback in SQLite:
CREATE TABLE feedback (
  id INTEGER PRIMARY KEY,
  repo TEXT,
  pr_number INTEGER,
  comment_id TEXT,
  code_chunk TEXT,          -- the diff that was reviewed
  ai_comment TEXT,          -- what the AI said
  issue_type TEXT,          -- security/performance/bug/style
  feedback_type TEXT,       -- helpful/unhelpful/false_positive/true_positive
  feedback_reason TEXT,     -- why unhelpful
  reward FLOAT,             -- computed reward score
  timestamp DATETIME
);
"""
```

#### 5.2 Reward Model

```python
# backend/rl/reward_model.py

"""
Train a small reward model on collected feedback.
Use: TRL (Transformer Reinforcement Learning) library

Base model: microsoft/codebert-base (free, runs locally)
Fine-tune as: binary classifier (helpful=1, unhelpful=0)

Training data format:
{
  "chosen": "Here the AI comment that got 👍 or led to a fix",
  "rejected": "Here the AI comment that got 👎 or was ignored"
}

Use preference pairs for reward modeling (DPO or reward model training):

from trl import RewardTrainer, RewardConfig
from transformers import AutoModelForSequenceClassification

# Train reward model
reward_model = AutoModelForSequenceClassification.from_pretrained(
    "microsoft/codebert-base", num_labels=1
)

# Input: [code_chunk + ai_comment] → scalar reward

Trigger training:
- Automatically when feedback_db has >50 new samples
- Or manually via: python scripts/train_rl.sh

Save checkpoint to: models/reward_model/
"""
```

#### 5.3 PPO Fine-tuning Loop

```python
# backend/rl/ppo_trainer.py

"""
Use PPO to fine-tune the review generation model.

IMPORTANT: Since we're using API-based LLMs (Groq/Together) as primary,
apply RL in two ways:

WAY 1 — Prompt optimization via RL (no model weights needed):
- Treat system prompt as the "policy"
- Use feedback to find which prompt variations get more 👍
- A/B test different prompt phrasings
- Store winning prompt variants
- This is "prompt RL" and works with ANY API LLM

WAY 2 — Local model fine-tuning (when using Ollama/local model):
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

config = PPOConfig(
    model_name="deepseek-ai/deepseek-coder-1.3b-instruct",
    learning_rate=1e-5,
    batch_size=16,
    mini_batch_size=4,
    gradient_accumulation_steps=4,
)

ppo_trainer = PPOTrainer(
    config=config,
    model=model,
    ref_model=ref_model,
    tokenizer=tokenizer,
    reward_model=reward_model,
    dataset=feedback_dataset,
)

# Training loop
for epoch in range(num_epochs):
    for batch in dataloader:
        query_tensors = batch["input_ids"]
        response_tensors = ppo_trainer.generate(query_tensors)
        rewards = reward_model(query_tensors, response_tensors)
        ppo_trainer.step(query_tensors, response_tensors, rewards)

Save fine-tuned model to: models/finetuned/v{version}/
"""
```

#### 5.4 RL Feedback Loop Architecture

```
Developer opens PR
       ↓
ReviewBot posts AI comments
       ↓
Developer reacts 👍/👎 OR fixes code OR ignores
       ↓
Webhook captures reaction → feedback_collector.py
       ↓
Compute reward: +1 (helpful), -0.5 (ignored), -1 (false positive)
       ↓
Store in feedback_db.sqlite
       ↓
Every N=50 samples → trigger reward_model training
       ↓
Every M=200 samples → trigger PPO fine-tuning (or prompt optimization)
       ↓
Updated model/prompt deployed automatically
       ↓
Next reviews are better → more 👍 → virtuous cycle
```

---

### PHASE 6 — Dashboard Frontend (Days 23–27)

#### 6.1 Dashboard Page

```jsx
// frontend/src/pages/Dashboard.jsx

/*
Build a clean dark-theme dashboard showing:

HEADER:
- ReviewBot AI logo
- Connected repos count
- Today's reviews count

METRICS ROW (4 cards):
- Total PRs Reviewed (all time)
- Issues Found (this week)
- Issues Fixed (from feedback loop)
- Model Accuracy % (from RL feedback)

CHARTS ROW:
- Line chart: Reviews per day (last 30 days)
- Pie chart: Issue categories (security/performance/bug/style)
- Bar chart: Issues by severity (critical/high/medium/low)
- Line chart: Model helpfulness score over time (RL progress)

RECENT REVIEWS TABLE:
- PR title, repo, author, date, issues found, status
- Click → go to PRView page

REPOS LIST:
- Connected repos with toggle to enable/disable
*/
```

#### 6.2 PR Detail View

```jsx
// frontend/src/pages/PRView.jsx

/*
Show a single PR review in detail:

LEFT PANEL: File tree with risk indicators
RIGHT PANEL: Diff viewer with inline AI comments

Each AI comment shows:
- Severity badge (color coded)
- Category tag
- Description
- Code suggestion with syntax highlight
- 👍 Helpful / 👎 Not Helpful buttons (POST to /api/feedback)
- Status: Open / Resolved / False Positive
- Confidence percentage

Use: react-diff-viewer-continued for diff display
Use: react-syntax-highlighter for code blocks
*/
```

#### 6.3 Rule Editor

```jsx
// frontend/src/pages/RuleEditor.jsx

/*
Visual editor for custom rules:
- YAML editor with Monaco Editor (like VS Code)
- Live preview: paste code, see which rules trigger
- Rule library: browse community-shared rules
- Import/export rules as YAML
- Per-language filter
- Severity assignment UI
*/
```

---

### PHASE 7 — Deployment (Days 28–30)

#### 7.1 Docker Setup

```yaml
# docker-compose.yml

version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - DATABASE_URL=sqlite:///./data/reviewbot.db
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./rules:/app/rules
    
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

#### 7.2 One-Shot Setup Script

```bash
# scripts/setup.sh

#!/bin/bash
echo "🤖 Setting up ReviewBot AI..."

# 1. Copy env file
cp .env.example .env
echo "⚠️  Fill in .env with your API keys"

# 2. Install Python deps
pip install fastapi uvicorn PyGithub chromadb sentence-transformers \
  trl transformers torch radon pyyaml redis httpx

# 3. Install frontend deps
cd frontend && npm install && cd ..

# 4. Initialize DB
python -c "from backend.rl.feedback_db import init_db; init_db()"

# 5. Set up GitHub webhook
echo "📌 Set GitHub webhook to: https://your-domain.com/webhook/github"
echo "   Events: Pull requests, Pull request review comments"
echo "   Content type: application/json"

echo "✅ Setup complete! Run: ./scripts/run_server.sh"
```

---

## 🔒 SECURITY & PRIVACY

```
- All code diffs sent to Groq/Together API — check their data retention policies
- For sensitive repos: use local Ollama only (zero data leaves your machine)
- GitHub token: use fine-grained personal access token with minimal scopes
- Webhook secrets: always verify HMAC-SHA256 signatures
- Dashboard: add basic auth or SSO before exposing publicly
- Never log full code content in production logs
```

---

## 📊 ADVANCED RL FEATURES

### Personalized Learning Per Developer

```python
"""
Track feedback per developer (GitHub username):
- Some devs prefer verbose comments, others prefer terse
- Some care about style, others only care about bugs
- Learn per-developer preferences and adjust verbosity/focus

Store in: developer_preferences table
Update after every 10 feedbacks from that dev
"""
```

### Pattern Propagation

```python
"""
When a bug pattern is confirmed (dev fixed it based on our suggestion):
1. Extract the code pattern as an embedding
2. Store in "confirmed_bugs" collection in ChromaDB
3. On future PRs, scan for similar patterns FIRST (before LLM call)
4. Pre-generate a high-confidence warning if pattern matches
5. This creates a snowballing bug pattern database specific to your codebase
"""
```

### Review Quality Metrics

```python
"""
Track these KPIs over time (show in dashboard):
- True Positive Rate: (fixed bugs / total flagged)
- False Positive Rate: (ignored/rejected / total flagged)
- Severity Accuracy: (did our severity match actual impact?)
- Model Drift: is accuracy declining? (trigger re-training)
- Coverage: % of changed lines reviewed
- Latency: time from PR open to review posted
"""
```

---

## 🚀 IMPLEMENTATION ORDER FOR CLAUDE

When giving this to Claude, ask it to build in this order:

```
Step 1: "Build Phase 1 — FastAPI server, webhook handler, GitHub client, diff parser"
Step 2: "Build Phase 2 — LLM reviewer with Groq, context builder, comment poster"
Step 3: "Build Phase 3 — Security scanner, complexity analyzer, rule engine"
Step 4: "Build Phase 4.1 — Test generator"
Step 4: "Build Phase 4.2-4.5 — Doc patcher, review memory, PR summary, walkthrough"
Step 5: "Build Phase 5 — Full RL system: feedback collector, reward model, PPO trainer"
Step 6: "Build Phase 6 — React dashboard with all pages"
Step 7: "Build Phase 7 — Docker, setup script, deployment config"
```

Tell Claude at each step:
> "Use the plan in this file. Build only this phase. Follow the exact file structure defined. Use the free APIs listed. Write complete, production-ready code with error handling."

---

## 📋 FULL PROMPT TO GIVE CLAUDE

```
You are building ReviewBot AI — a self-hosted, open-source alternative to CodeRabbit
with reinforcement learning. 

Use the exact project structure, tech stack, and implementation details from this plan.

Key requirements:
1. Use ONLY free APIs: Groq (primary LLM), ChromaDB (vector store), SQLite (database)
2. All Python code must use FastAPI + async/await
3. Frontend must be React 18 + Vite + Tailwind CSS + shadcn/ui
4. Implement the RL feedback loop EXACTLY as described in Phase 5
5. Every module must have error handling, logging, and docstrings
6. Use PyGithub for GitHub API calls
7. Webhook signature verification is mandatory (security)
8. The diff parser must output the exact JSON schema defined
9. LLM calls must have a 3-level fallback chain (Groq → Together → HuggingFace)
10. ChromaDB embeddings use sentence-transformers locally (no API cost)

Start with Phase [X] as instructed. Write complete, runnable code.
Do not use placeholder comments — implement everything fully.
```

---

## 💡 TIPS FOR BEST RESULTS

1. **Give one phase at a time** — don't give Claude all phases at once
2. **Always include this full .md** — as context even for later phases
3. **Test each phase** before moving on
4. **For RL training**: you need at least 50 feedback samples before first training cycle
5. **Use ngrok** for local testing of webhooks: `ngrok http 8000`
6. **Start with a test repo** — create a dummy GitHub repo and open test PRs
7. **Groq is the fastest** — use it as primary, add Together/HF as fallback
8. **Run Ollama locally** if you want truly offline/private operation

---

*Built with 💻 | Powered by open-source | Learns from your team*
