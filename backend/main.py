"""ReviewBot AI — FastAPI application entrypoint."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on path when running as script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import get_settings
from backend.db.store import ReviewStore
from backend.models import (
    HealthResponse,
    JobDetailResponse,
    ManualReviewRequest,
    WebhookResponse,
)
from backend.review_engine.review_orchestrator import ReviewOrchestrator
from backend.webhook_handler import WebhookHandler, _enqueue_review

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

store = ReviewStore()
orchestrator = ReviewOrchestrator(store)
webhook_handler = WebhookHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.getLogger().setLevel(settings.log_level.upper())
    await store.init()
    for warning in settings.validate_startup():
        logger.warning(warning)
    yield


app = FastAPI(
    title="ReviewBot AI",
    description="Self-hosted AI code reviewer — GitHub & GitLab MVP",
    version="0.1.0-mvp",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        llm_configured=settings.has_llm_provider(),
        github_configured=bool(settings.github_token),
        gitlab_configured=bool(settings.gitlab_token),
        warnings=settings.validate_startup(),
    )


@app.post("/webhook/github", response_model=WebhookResponse)
async def github_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> WebhookResponse:
    return await webhook_handler.handle_github(request, background_tasks)


@app.post("/webhook/gitlab", response_model=WebhookResponse)
async def gitlab_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> WebhookResponse:
    return await webhook_handler.handle_gitlab(request, background_tasks)


@app.post("/api/review", response_model=WebhookResponse)
async def manual_review(
    body: ManualReviewRequest,
    background_tasks: BackgroundTasks,
) -> WebhookResponse:
    """Trigger a review manually (useful for testing without webhooks)."""
    job = await store.create_job(
        platform=body.platform,
        owner=body.owner,
        repo=body.repo,
        pr_number=body.pr_number,
        title=body.title,
        description=body.description,
        head_sha=body.head_sha,
    )
    background_tasks.add_task(_enqueue_review, store, orchestrator, job.id)
    return WebhookResponse(
        accepted=True,
        job_id=job.id,
        message="Review queued via API",
    )


@app.get("/api/reviews/{job_id}", response_model=JobDetailResponse)
async def get_review(job_id: str) -> JobDetailResponse:
    job = await store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    issues = await store.get_issues(job_id)
    return JobDetailResponse(job=job, issues=issues)


@app.get("/api/reviews")
async def list_reviews(limit: int = 20):
    jobs = await store.list_recent_jobs(limit=limit)
    return {"jobs": jobs}


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
