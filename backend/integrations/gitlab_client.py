"""GitLab API client via python-gitlab."""

import asyncio
import logging
from functools import partial

import gitlab

from backend.config import get_settings
from backend.integrations.base import GitProvider, PostedReview
from backend.models import DiffChunk, Platform
from backend.review_engine.diff_parser import parse_gitlab_mr_diffs

logger = logging.getLogger(__name__)


class GitLabClient(GitProvider):
    platform = Platform.GITLAB

    def __init__(self, token: str | None = None, gitlab_url: str | None = None) -> None:
        settings = get_settings()
        self._token = token or settings.gitlab_token
        self._url = gitlab_url or settings.gitlab_url
        if not self._token:
            raise ValueError("GITLAB_TOKEN is not configured")
        self._gl = gitlab.Gitlab(self._url, private_token=self._token)

    def _run(self, fn, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, partial(fn, *args, **kwargs))

    def _project_path(self, owner: str, repo: str) -> str:
        return f"{owner}/{repo}"

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> list[DiffChunk]:
        def _fetch():
            project = self._gl.projects.get(self._project_path(owner, repo))
            mr = project.mergerequests.get(pr_number)
            changes = mr.changes()
            return parse_gitlab_mr_diffs(changes.get("changes", []))

        return await self._run(_fetch)

    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str:
        def _fetch():
            project = self._gl.projects.get(self._project_path(owner, repo))
            try:
                f = project.files.get(file_path=path, ref=ref)
                return f.decode().decode("utf-8", errors="replace")
            except gitlab.exceptions.GitlabGetError as exc:
                logger.warning("Could not fetch %s@%s: %s", path, ref, exc)
                return ""

        return await self._run(_fetch)

    async def get_readme_snippet(self, owner: str, repo: str, max_chars: int = 500) -> str:
        for path in ("README.md", "README.rst", "README"):
            content = await self.get_file_content(owner, repo, path, "main")
            if content:
                return content[:max_chars]
            content = await self.get_file_content(owner, repo, path, "master")
            if content:
                return content[:max_chars]
        return ""

    async def get_pr_head_sha(self, owner: str, repo: str, pr_number: int) -> str:
        def _fetch():
            project = self._gl.projects.get(self._project_path(owner, repo))
            mr = project.mergerequests.get(pr_number)
            return mr.sha

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
            project = self._gl.projects.get(self._project_path(owner, repo))
            mr = project.mergerequests.get(pr_number)
            posted = 0

            for c in inline_comments:
                line = c.get("line")
                if not line:
                    continue
                try:
                    mr.discussions.create(
                        {
                            "body": c["body"],
                            "position": {
                                "base_sha": mr.diff_refs["base_sha"],
                                "start_sha": mr.diff_refs["start_sha"],
                                "head_sha": commit_id or mr.diff_refs["head_sha"],
                                "position_type": "text",
                                "new_path": c["path"],
                                "new_line": int(line),
                            },
                        }
                    )
                    posted += 1
                except gitlab.exceptions.GitlabCreateError as exc:
                    logger.warning(
                        "Failed inline comment on %s:%s — %s",
                        c.get("path"),
                        line,
                        exc,
                    )

            mr.notes.create({"body": summary})
            return PostedReview(
                review_id=str(mr.iid),
                comment_count=posted,
                summary=summary,
            )

        return await self._run(_post)
