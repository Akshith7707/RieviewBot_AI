"""SQLite persistence for review jobs and issues."""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from backend.config import get_settings
from backend.models import (
    DashboardStats,
    FeedbackCreate,
    FeedbackRating,
    FeedbackRecord,
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

                CREATE TABLE IF NOT EXISTS review_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    issue_id INTEGER NOT NULL,
                    rating TEXT NOT NULL,
                    user_name TEXT,
                    comment TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES review_jobs(id),
                    FOREIGN KEY (issue_id) REFERENCES review_issues(id)
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_status ON review_jobs(status);
                CREATE INDEX IF NOT EXISTS idx_issues_job ON review_issues(job_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_job ON review_feedback(job_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_issue ON review_feedback(issue_id);
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
            id=row["id"],
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

    async def save_feedback(self, data: FeedbackCreate) -> FeedbackRecord:
        now = _utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO review_feedback
                (job_id, issue_id, rating, user_name, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data.job_id,
                    data.issue_id,
                    data.rating.value,
                    data.user,
                    data.comment,
                    now,
                ),
            )
            await db.commit()
            feedback_id = cursor.lastrowid
        return FeedbackRecord(
            id=feedback_id or 0,
            job_id=data.job_id,
            issue_id=data.issue_id,
            rating=data.rating,
            user=data.user,
            comment=data.comment,
            created_at=datetime.fromisoformat(now),
        )

    async def list_feedback(
        self, job_id: str | None = None, limit: int = 50
    ) -> list[FeedbackRecord]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if job_id:
                query = (
                    "SELECT * FROM review_feedback WHERE job_id = ? "
                    "ORDER BY created_at DESC LIMIT ?"
                )
                params: tuple = (job_id, limit)
            else:
                query = (
                    "SELECT * FROM review_feedback ORDER BY created_at DESC LIMIT ?"
                )
                params = (limit,)
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
        return [self._row_to_feedback(r) for r in rows]

    def _row_to_feedback(self, row: aiosqlite.Row) -> FeedbackRecord:
        return FeedbackRecord(
            id=row["id"],
            job_id=row["job_id"],
            issue_id=row["issue_id"],
            rating=FeedbackRating(row["rating"]),
            user=row["user_name"] or "",
            comment=row["comment"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    async def get_feedback_stats(self) -> dict[str, int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT rating, COUNT(*) as c FROM review_feedback GROUP BY rating"
            ) as cursor:
                rows = await cursor.fetchall()
        stats = {"total": 0, "helpful": 0, "not_helpful": 0}
        for rating, count in rows:
            stats["total"] += count
            if rating == FeedbackRating.HELPFUL.value:
                stats["helpful"] = count
            else:
                stats["not_helpful"] = count
        return stats

    async def get_issue_feedback_stats(self, issue_id: int) -> dict[str, int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT rating, COUNT(*) FROM review_feedback "
                "WHERE issue_id = ? GROUP BY rating",
                (issue_id,),
            ) as cursor:
                rows = await cursor.fetchall()
        stats = {"total": 0, "helpful": 0, "not_helpful": 0}
        for rating, count in rows:
            stats["total"] += count
            if rating == FeedbackRating.HELPFUL.value:
                stats["helpful"] = count
            else:
                stats["not_helpful"] = count
        return stats

    async def get_dashboard_stats(self) -> DashboardStats:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM review_jobs") as c:
                total_jobs = (await c.fetchone())[0]
            async with db.execute(
                "SELECT COUNT(*) FROM review_jobs WHERE status = 'completed'"
            ) as c:
                completed = (await c.fetchone())[0]
            async with db.execute(
                "SELECT COUNT(*) FROM review_jobs WHERE status = 'failed'"
            ) as c:
                failed = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM review_issues") as c:
                total_issues = (await c.fetchone())[0]
            async with db.execute(
                "SELECT severity, COUNT(*) FROM review_issues GROUP BY severity"
            ) as c:
                sev_rows = await c.fetchall()
            async with db.execute(
                "SELECT source, COUNT(*) FROM review_issues GROUP BY source"
            ) as c:
                src_rows = await c.fetchall()

        fb = await self.get_feedback_stats()
        helpful_pct = (
            (fb["helpful"] / fb["total"] * 100) if fb["total"] > 0 else 0.0
        )
        return DashboardStats(
            total_jobs=total_jobs,
            completed_jobs=completed,
            failed_jobs=failed,
            total_issues=total_issues,
            issues_by_severity={s: n for s, n in sev_rows},
            issues_by_source={s or "unknown": n for s, n in src_rows},
            feedback_total=fb["total"],
            feedback_helpful=fb["helpful"],
            feedback_not_helpful=fb["not_helpful"],
            helpfulness_percent=round(helpful_pct, 1),
            rl_training_ready=fb["total"] >= 50,
        )
