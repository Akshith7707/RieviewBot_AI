"""ReviewBot AI — FastAPI application entrypoint."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import get_settings
from backend.db.store import ReviewStore
from backend.models import (
    DashboardStats,
    FeedbackCreate,
    FeedbackRecord,
    HealthResponse,
    JobDetailResponse,
    ManualReviewRequest,
    WebhookResponse,
)
from backend.review_engine.review_orchestrator import ReviewOrchestrator
from backend.rl.feedback_collector import FeedbackCollector
from backend.webhook_handler import WebhookHandler, _enqueue_review

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

store = ReviewStore()
orchestrator = ReviewOrchestrator(store)
webhook_handler = WebhookHandler()
feedback_collector = FeedbackCollector(store)

FRONTEND_DIST = ROOT / "frontend" / "dist"


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
    description="Self-hosted AI code reviewer — GitHub & GitLab",
    version="0.2.0",
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
        version="0.2.0",
        llm_configured=settings.has_llm_provider(),
        github_configured=bool(settings.github_token),
        gitlab_configured=bool(settings.gitlab_token),
        warnings=settings.validate_startup(),
    )


@app.get("/api/stats", response_model=DashboardStats)
async def dashboard_stats() -> DashboardStats:
    return await store.get_dashboard_stats()


@app.post("/api/feedback", response_model=FeedbackRecord)
async def submit_feedback(body: FeedbackCreate) -> FeedbackRecord:
    job = await store.get_job(body.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    issues = await store.get_issues(body.job_id)
    if not any(i.id == body.issue_id for i in issues):
        raise HTTPException(status_code=404, detail="Issue not found for this job")
    return await feedback_collector.submit(body)


@app.get("/api/feedback")
async def list_feedback(job_id: str | None = None, limit: int = 50):
    records = await store.list_feedback(job_id=job_id, limit=limit)
    return {"feedback": records}


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
    feedback = await store.list_feedback(job_id=job_id, limit=100)
    return JobDetailResponse(job=job, issues=issues, feedback=feedback)


@app.get("/api/reviews")
async def list_reviews(limit: int = 20):
    jobs = await store.list_recent_jobs(limit=limit)
    return {"jobs": jobs}


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/jobs/{job_id}")
    async def serve_job_page(job_id: str):
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
