"""Pydantic models for ReviewBot AI."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Platform(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUG = "bug"
    STYLE = "style"
    MAINTAINABILITY = "maintainability"


class ReviewIssue(BaseModel):
    id: int | None = None
    severity: Severity
    category: IssueCategory
    file_path: str
    line_number: int
    title: str
    description: str
    suggestion: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    source: Literal["security_scanner", "llm"] = "llm"


class FeedbackRating(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"


class FeedbackCreate(BaseModel):
    job_id: str
    issue_id: int
    rating: FeedbackRating
    user: str = ""
    comment: str = ""


class FeedbackRecord(BaseModel):
    id: int
    job_id: str
    issue_id: int
    rating: FeedbackRating
    user: str = ""
    comment: str = ""
    created_at: datetime


class DashboardStats(BaseModel):
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    total_issues: int = 0
    issues_by_severity: dict[str, int] = Field(default_factory=dict)
    issues_by_source: dict[str, int] = Field(default_factory=dict)
    feedback_total: int = 0
    feedback_helpful: int = 0
    feedback_not_helpful: int = 0
    helpfulness_percent: float = 0.0
    rl_training_ready: bool = False


class DiffChange(BaseModel):
    type: Literal["add", "del", "context"]
    line_no: int
    content: str


class DiffHunk(BaseModel):
    old_start: int
    new_start: int
    context_before: list[str] = Field(default_factory=list)
    changes: list[DiffChange] = Field(default_factory=list)
    context_after: list[str] = Field(default_factory=list)


class DiffChunk(BaseModel):
    file_path: str
    language: str
    change_type: Literal["added", "deleted", "modified", "renamed"] = "modified"
    old_path: str | None = None
    additions: int = 0
    deletions: int = 0
    hunks: list[DiffHunk] = Field(default_factory=list)
    patch: str = ""


class LLMReviewResult(BaseModel):
    summary: str = ""
    issues: list[ReviewIssue] = Field(default_factory=list)
    positive_feedback: list[str] = Field(default_factory=list)
    refactoring_suggestion: str = ""
    complexity_score: int = 0


class ReviewJobCreate(BaseModel):
    platform: Platform
    owner: str
    repo: str
    pr_number: int
    title: str = ""
    description: str = ""
    head_sha: str = ""
    base_sha: str = ""


class ReviewJob(BaseModel):
    id: str
    platform: Platform
    owner: str
    repo: str
    pr_number: int
    title: str = ""
    description: str = ""
    head_sha: str = ""
    status: JobStatus = JobStatus.PENDING
    error_message: str | None = None
    review_summary: str | None = None
    issues_count: int = 0
    created_at: datetime
    completed_at: datetime | None = None


class ManualReviewRequest(BaseModel):
    platform: Platform
    owner: str
    repo: str
    pr_number: int
    title: str = ""
    description: str = ""
    head_sha: str = ""


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0-mvp"
    llm_configured: bool
    github_configured: bool
    gitlab_configured: bool
    warnings: list[str] = Field(default_factory=list)


class WebhookResponse(BaseModel):
    accepted: bool
    job_id: str | None = None
    message: str = ""


class JobDetailResponse(BaseModel):
    job: ReviewJob
    issues: list[ReviewIssue] = Field(default_factory=list)
    feedback: list[FeedbackRecord] = Field(default_factory=list)


class PRContext(BaseModel):
    platform: Platform
    owner: str
    repo: str
    pr_number: int
    title: str = ""
    description: str = ""
    head_sha: str = ""
    readme_snippet: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)
