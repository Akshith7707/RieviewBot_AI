"""SQLite persistence for review jobs and issues."""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from backend.config import get_settings
from backend.models import (
    IssueCategory,
    JobStatus,
    Platform,
    ReviewIssue,
    ReviewJob,
    Severity,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReviewStore:
    def __init__(self, db_path: str | None = None) -> None:
        settings = get_settings()
        self.db_path = db_path or settings.sqlite_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS review_jobs (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    repo TEXT NOT NULL,
                    pr_number INTEGER NOT NULL,
                    title TEXT,
                    description TEXT,
                    head_sha TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    review_summary TEXT,
                    issues_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS review_issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    suggestion TEXT,
                    confidence REAL,
                    source TEXT,
                    FOREIGN KEY (job_id) REFERENCES review_jobs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_status ON review_jobs(status);
                CREATE INDEX IF NOT EXISTS idx_issues_job ON review_issues(job_id);
                """
            )
            await db.commit()
        logger.info("Database initialized at %s", self.db_path)

    async def create_job(
        self,
        platform: Platform,
        owner: str,
        repo: str,
        pr_number: int,
        title: str = "",
        description: str = "",
        head_sha: str = "",
    ) -> ReviewJob:
        job_id = str(uuid.uuid4())
        now = _utcnow()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO review_jobs
                (id, platform, owner, repo, pr_number, title, description,
                 head_sha, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    platform.value,
                    owner,
                    repo,
                    pr_number,
                    title,
                    description,
                    head_sha,
                    JobStatus.PENDING.value,
                    now.isoformat(),
                ),
            )
            await db.commit()
        return ReviewJob(
            id=job_id,
            platform=platform,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            title=title,
            description=description,
            head_sha=head_sha,
            status=JobStatus.PENDING,
            created_at=now,
        )

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: str | None = None,
        review_summary: str | None = None,
        issues_count: int | None = None,
    ) -> None:
        completed_at = _utcnow().isoformat() if status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        ) else None
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE review_jobs
                SET status = ?, error_message = ?, review_summary = ?,
                    issues_count = COALESCE(?, issues_count),
                    completed_at = COALESCE(?, completed_at)
                WHERE id = ?
                """,
                (
                    status.value,
                    error_message,
                    review_summary,
                    issues_count,
                    completed_at,
                    job_id,
                ),
            )
            await db.commit()

    async def save_issues(self, job_id: str, issues: list[ReviewIssue]) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            for issue in issues:
                await db.execute(
                    """
                    INSERT INTO review_issues
                    (job_id, severity, category, file_path, line_number,
                     title, description, suggestion, confidence, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        issue.severity.value,
                        issue.category.value,
                        issue.file_path,
                        issue.line_number,
                        issue.title,
                        issue.description,
                        issue.suggestion,
                        issue.confidence,
                        issue.source,
                    ),
                )
            await db.commit()

    async def get_job(self, job_id: str) -> ReviewJob | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM review_jobs WHERE id = ?", (job_id,)
            ) as cursor:
                row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    async def get_issues(self, job_id: str) -> list[ReviewIssue]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM review_issues WHERE job_id = ? ORDER BY id",
                (job_id,),
            ) as cursor:
                rows = await cursor.fetchall()
        return [self._row_to_issue(r) for r in rows]

    def _row_to_job(self, row: aiosqlite.Row) -> ReviewJob:
        return ReviewJob(
            id=row["id"],
            platform=Platform(row["platform"]),
            owner=row["owner"],
            repo=row["repo"],
            pr_number=row["pr_number"],
            title=row["title"] or "",
            description=row["description"] or "",
            head_sha=row["head_sha"] or "",
            status=JobStatus(row["status"]),
            error_message=row["error_message"],
            review_summary=row["review_summary"],
            issues_count=row["issues_count"] or 0,
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
        )

    def _row_to_issue(self, row: aiosqlite.Row) -> ReviewIssue:
        return ReviewIssue(
            severity=Severity(row["severity"]),
            category=IssueCategory(row["category"]),
            file_path=row["file_path"],
            line_number=row["line_number"],
            title=row["title"],
            description=row["description"] or "",
            suggestion=row["suggestion"] or "",
            confidence=row["confidence"] or 0.8,
            source=row["source"] or "llm",
        )

    async def list_recent_jobs(self, limit: int = 20) -> list[ReviewJob]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM review_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
        return [self._row_to_job(r) for r in rows]
