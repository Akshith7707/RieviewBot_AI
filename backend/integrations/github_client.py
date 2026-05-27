"""GitHub API client via PyGithub."""

import asyncio
import logging
from functools import partial

from github import Auth, Github, GithubException

from backend.config import get_settings
from backend.integrations.base import GitProvider, PostedReview
from backend.models import DiffChunk, Platform
from backend.review_engine.diff_parser import parse_github_file_diffs

logger = logging.getLogger(__name__)


class GitHubClient(GitProvider):
    platform = Platform.GITHUB

    def __init__(self, token: str | None = None) -> None:
        settings = get_settings()
        self._token = token or settings.github_token
        if not self._token:
            raise ValueError("GITHUB_TOKEN is not configured")
        self._github = Github(auth=Auth.Token(self._token))

    def _run(self, fn, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, partial(fn, *args, **kwargs))

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> list[DiffChunk]:
        def _fetch():
            repository = self._github.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            files = pr.get_files()
            file_dicts = [
                {
                    "filename": f.filename,
                    "previous_filename": getattr(f, "previous_filename", None),
                    "status": f.status,
                    "patch": f.patch or "",
                    "additions": f.additions,
                    "deletions": f.deletions,
                }
                for f in files
            ]
            return parse_github_file_diffs(file_dicts)

        return await self._run(_fetch)

    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str:
        def _fetch():
            repository = self._github.get_repo(f"{owner}/{repo}")
            try:
                content = repository.get_contents(path, ref=ref)
                if isinstance(content, list):
                    return ""
                return content.decoded_content.decode("utf-8", errors="replace")
            except GithubException as exc:
                logger.warning("Could not fetch %s@%s: %s", path, ref, exc)
                return ""

        return await self._run(_fetch)

    async def get_readme_snippet(self, owner: str, repo: str, max_chars: int = 500) -> str:
        for path in ("README.md", "README.rst", "README"):
            content = await self.get_file_content(owner, repo, path, "HEAD")
            if content:
                return content[:max_chars]
        return ""

    async def get_pr_head_sha(self, owner: str, repo: str, pr_number: int) -> str:
        def _fetch():
            repository = self._github.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            return pr.head.sha

        return await self._run(_fetch)

    async def post_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_id: str,
        summary: str,
        inline_comments: list[dict],
    ) -> PostedReview:
        def _post():
            repository = self._github.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)

            comments_payload = []
            for c in inline_comments:
                line = c.get("line")
                if not line:
                    continue
                comments_payload.append(
                    {
                        "path": c["path"],
                        "line": int(line),
                        "body": c["body"],
                    }
                )

            review = pr.create_review(
                commit=commit_id,
                body=summary,
                event="COMMENT",
                comments=comments_payload,
            )
            return PostedReview(
                review_id=str(review.id),
                comment_count=len(comments_payload),
                summary=summary,
            )

        return await self._run(_post)
