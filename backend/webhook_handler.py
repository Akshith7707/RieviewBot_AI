"""GitHub and GitLab webhook handlers."""

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import BackgroundTasks, HTTPException, Request

from backend.config import get_settings
from backend.models import Platform, WebhookResponse
from backend.db.store import ReviewStore
from backend.review_engine.review_orchestrator import ReviewOrchestrator

logger = logging.getLogger(__name__)


def _verify_github_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    if not secret:
        logger.warning("GITHUB_WEBHOOK_SECRET not set — skipping verification")
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    received = signature[7:]
    return hmac.compare_digest(expected, received)


def _verify_gitlab_token(token: str | None, secret: str) -> bool:
    if not secret:
        logger.warning("GITLAB_WEBHOOK_SECRET not set — skipping verification")
        return True
    return token == secret


def _parse_github_pr_event(payload: dict[str, Any]) -> dict[str, Any] | None:
    if payload.get("action") not in ("opened", "synchronize", "reopened"):
        return None
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})
    return {
        "platform": Platform.GITHUB,
        "owner": repo.get("owner", {}).get("login", ""),
        "repo": repo.get("name", ""),
        "pr_number": pr.get("number"),
        "title": pr.get("title", ""),
        "description": pr.get("body") or "",
        "head_sha": pr.get("head", {}).get("sha", ""),
    }


def _parse_gitlab_mr_event(payload: dict[str, Any]) -> dict[str, Any] | None:
    attrs = payload.get("object_attributes", {})
    state = attrs.get("state")
    action = payload.get("object_kind")
    if action != "merge_request":
        return None
    if attrs.get("action") not in ("open", "update", "reopen") and state not in (
        "opened",
        "reopened",
    ):
        if attrs.get("action") != "update":
            return None

    project = payload.get("project", {})
    path = project.get("path_with_namespace", "")
    parts = path.split("/", 1)
    owner = parts[0] if parts else ""
    repo = parts[1] if len(parts) > 1 else project.get("name", "")

    return {
        "platform": Platform.GITLAB,
        "owner": owner,
        "repo": repo,
        "pr_number": attrs.get("iid") or attrs.get("id"),
        "title": attrs.get("title", ""),
        "description": attrs.get("description") or "",
        "head_sha": attrs.get("last_commit", {}).get("id", "")
        or attrs.get("sha", ""),
    }


async def _enqueue_review(
    store: ReviewStore,
    orchestrator: ReviewOrchestrator,
    job_id: str,
) -> None:
    await orchestrator.run_review(job_id)


class WebhookHandler:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.store = ReviewStore()
        self.orchestrator = ReviewOrchestrator(self.store)

    async def handle_github(
        self, request: Request, background_tasks: BackgroundTasks
    ) -> WebhookResponse:
        payload_bytes = await request.body()
        signature = request.headers.get("X-Hub-Signature-256")
        event = request.headers.get("X-GitHub-Event", "")

        if not _verify_github_signature(
            payload_bytes,
            signature,
            self.settings.github_webhook_secret,
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = json.loads(payload_bytes)
        if event != "pull_request":
            return WebhookResponse(
                accepted=False,
                message=f"Ignored event type: {event}",
            )

        parsed = _parse_github_pr_event(payload)
        if not parsed:
            return WebhookResponse(
                accepted=False,
                message="PR event ignored (not opened/synchronized/reopened)",
            )

        job = await self.store.create_job(
            platform=parsed["platform"],
            owner=parsed["owner"],
            repo=parsed["repo"],
            pr_number=int(parsed["pr_number"]),
            title=parsed["title"],
            description=parsed["description"],
            head_sha=parsed["head_sha"],
        )
        background_tasks.add_task(
            _enqueue_review, self.store, self.orchestrator, job.id
        )
        return WebhookResponse(
            accepted=True,
            job_id=job.id,
            message="Review queued",
        )

    async def handle_gitlab(
        self, request: Request, background_tasks: BackgroundTasks
    ) -> WebhookResponse:
        token = request.headers.get("X-Gitlab-Token")
        if not _verify_gitlab_token(token, self.settings.gitlab_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook token")

        payload = await request.json()
        parsed = _parse_gitlab_mr_event(payload)
        if not parsed:
            return WebhookResponse(
                accepted=False,
                message="MR event ignored",
            )

        job = await self.store.create_job(
            platform=parsed["platform"],
            owner=parsed["owner"],
            repo=parsed["repo"],
            pr_number=int(parsed["pr_number"]),
            title=parsed["title"],
            description=parsed["description"],
            head_sha=parsed["head_sha"],
        )
        background_tasks.add_task(
            _enqueue_review, self.store, self.orchestrator, job.id
        )
        return WebhookResponse(
            accepted=True,
            job_id=job.id,
            message="Review queued",
        )
