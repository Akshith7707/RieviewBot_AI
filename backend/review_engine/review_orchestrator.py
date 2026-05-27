"""Orchestrates the full review pipeline."""

import logging
from collections import defaultdict

from backend.integrations.base import GitProvider
from backend.integrations.github_client import GitHubClient
from backend.integrations.gitlab_client import GitLabClient
from backend.models import (
    IssueCategory,
    JobStatus,
    Platform,
    PRContext,
    ReviewIssue,
    Severity,
)
from backend.review_engine.context_builder import ContextBuilder
from backend.review_engine.diff_parser import chunk_large_diff
from backend.review_engine.llm_reviewer import LLMReviewer
from backend.review_engine.security_scanner import SecurityScanner
from backend.config import get_settings
from backend.db.store import ReviewStore

logger = logging.getLogger(__name__)

SEVERITY_EMOJI = {
    Severity.CRITICAL: "🚨",
    Severity.HIGH: "⚠️",
    Severity.MEDIUM: "📝",
    Severity.LOW: "💡",
    Severity.INFO: "ℹ️",
}

SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


def get_git_client(platform: Platform) -> GitProvider:
    if platform == Platform.GITHUB:
        return GitHubClient()
    if platform == Platform.GITLAB:
        return GitLabClient()
    raise ValueError(f"Unsupported platform: {platform}")


def format_issue_comment(issue: ReviewIssue, job_id: str = "", dashboard_url: str = "") -> str:
    emoji = SEVERITY_EMOJI.get(issue.severity, "📝")
    body = (
        f"{emoji} **{issue.category.value}** — {issue.title}\n\n"
        f"{issue.description}\n"
    )
    if issue.suggestion:
        body += f"\n💡 **Suggestion:**\n```\n{issue.suggestion}\n```\n"
    body += f"\n*Confidence: {issue.confidence:.0%} | Source: {issue.source}*"
    if issue.id and dashboard_url:
        body += (
            f"\n\n👍 Rate this finding: {dashboard_url}/jobs/{job_id}"
            f"?issue={issue.id}"
        )
    return body


class ReviewOrchestrator:
    def __init__(self, store: ReviewStore | None = None) -> None:
        self.store = store or ReviewStore()
        self.scanner = SecurityScanner()
        self.llm = LLMReviewer()
        self.context_builder = ContextBuilder()
        self.settings = get_settings()

    async def run_review(self, job_id: str) -> None:
        job = await self.store.get_job(job_id)
        if not job:
            logger.error("Job not found: %s", job_id)
            return

        await self.store.update_job_status(job_id, JobStatus.RUNNING)

        try:
            client = get_git_client(job.platform)
            head_sha = job.head_sha or await client.get_pr_head_sha(
                job.owner, job.repo, job.pr_number
            )

            chunks = await client.get_pr_diff(job.owner, job.repo, job.pr_number)
            if not chunks:
                await self.store.update_job_status(
                    job_id,
                    JobStatus.COMPLETED,
                    review_summary="No reviewable diff found (empty PR or binary-only changes).",
                    issues_count=0,
                )
                return

            chunks = chunk_large_diff(chunks)
            readme = await client.get_readme_snippet(job.owner, job.repo)

            ctx = PRContext(
                platform=job.platform,
                owner=job.owner,
                repo=job.repo,
                pr_number=job.pr_number,
                title=job.title,
                description=job.description,
                head_sha=head_sha,
                readme_snippet=readme,
            )

            all_issues: list[ReviewIssue] = []
            summaries: list[str] = []
            positives: list[str] = []

            for chunk in chunks:
                base_path = chunk.file_path.split(" (part")[0]
                security_issues = self.scanner.scan_patch(
                    base_path, chunk.language, chunk.patch
                )
                all_issues.extend(security_issues)

                full_file = ""
                if head_sha:
                    full_file = await client.get_file_content(
                        job.owner, job.repo, base_path, head_sha
                    )

                prompt = self.context_builder.build(
                    ctx, chunk, full_file, security_issues
                )
                try:
                    result = await self.llm.review_chunk(prompt, chunk)
                    for issue in result.issues:
                        issue.file_path = base_path
                    all_issues.extend(result.issues)
                    if result.summary:
                        summaries.append(result.summary)
                    positives.extend(result.positive_feedback)
                except Exception as exc:
                    logger.warning(
                        "LLM review failed for %s: %s", chunk.file_path, exc
                    )

            deduped = self._dedupe_issues(all_issues)
            capped = self._cap_issues(deduped)

            await self.store.save_issues(job_id, capped)
            saved_issues = await self.store.get_issues(job_id)
            dashboard_url = self.settings.dashboard_url.rstrip("/")

            review_summary = self._build_summary(
                job, saved_issues, summaries, positives, job_id, dashboard_url
            )
            inline_comments = [
                {
                    "path": issue.file_path,
                    "line": issue.line_number,
                    "body": format_issue_comment(
                        issue, job_id, dashboard_url
                    ),
                }
                for issue in saved_issues
            ]

            await client.post_review(
                job.owner,
                job.repo,
                job.pr_number,
                head_sha,
                review_summary,
                inline_comments,
            )
            await self.store.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                review_summary=review_summary,
                issues_count=len(saved_issues),
            )
            logger.info(
                "Review completed for %s/%s#%s — %d issues",
                job.owner,
                job.repo,
                job.pr_number,
                len(saved_issues),
            )

        except Exception as exc:
            logger.exception("Review failed for job %s", job_id)
            await self.store.update_job_status(
                job_id,
                JobStatus.FAILED,
                error_message=str(exc),
            )

    def _dedupe_issues(self, issues: list[ReviewIssue]) -> list[ReviewIssue]:
        seen: set[tuple] = set()
        unique: list[ReviewIssue] = []
        for issue in sorted(
            issues,
            key=lambda i: (
                SEVERITY_ORDER.get(i.severity, 99),
                -i.confidence,
            ),
        ):
            key = (issue.file_path, issue.line_number, issue.title.lower())
            if key in seen:
                continue
            seen.add(key)
            unique.append(issue)
        return unique

    def _cap_issues(self, issues: list[ReviewIssue]) -> list[ReviewIssue]:
        max_comments = self.settings.max_comments_per_pr
        by_file: dict[str, list[ReviewIssue]] = defaultdict(list)
        for issue in issues:
            by_file[issue.file_path].append(issue)

        capped: list[ReviewIssue] = []
        for file_issues in by_file.values():
            capped.extend(file_issues[:3])
        capped.sort(key=lambda i: SEVERITY_ORDER.get(i.severity, 99))
        return capped[:max_comments]

    def _build_summary(
        self,
        job,
        issues: list[ReviewIssue],
        summaries: list[str],
        positives: list[str],
        job_id: str = "",
        dashboard_url: str = "",
    ) -> str:
        counts: dict[str, int] = defaultdict(int)
        for issue in issues:
            counts[issue.severity.value] += 1

        lines = [
            "## 🤖 ReviewBot AI — Automated Review",
            "",
            f"**Repository:** `{job.owner}/{job.repo}` · **PR/MR:** #{job.pr_number}",
            "",
            "### Summary",
        ]
        if summaries:
            lines.append(summaries[0][:1500])
        else:
            lines.append("Automated review completed.")

        lines.extend(["", "### Issues by severity"])
        if counts:
            for sev in ("critical", "high", "medium", "low", "info"):
                if counts.get(sev):
                    lines.append(f"- **{sev}**: {counts[sev]}")
        else:
            lines.append("No issues found. Nice work!")

        sec_count = sum(1 for i in issues if i.source == "security_scanner")
        llm_count = sum(1 for i in issues if i.source == "llm")
        lines.extend(
            [
                "",
                f"*Pre-scan security rules: {sec_count} · LLM findings: {llm_count}*",
            ]
        )

        if positives:
            lines.extend(["", "### 👍 Positive notes"])
            for p in positives[:5]:
                lines.append(f"- {p}")

        if dashboard_url and job_id:
            lines.extend(
                [
                    "",
                    f"📊 **Live dashboard:** {dashboard_url}/jobs/{job_id}",
                    "Rate findings with 👍/👎 — ReviewBot learns from your feedback (RL).",
                ]
            )
        lines.extend(
            [
                "",
                "---",
                "*ReviewBot AI — OWASP pre-scan + LLM + RL feedback (beats black-box reviewers)*",
            ]
        )
        return "\n".join(lines)
