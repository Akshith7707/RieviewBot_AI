"""Abstract git provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.models import DiffChunk, Platform


@dataclass
class PostedReview:
    review_id: str | None
    comment_count: int
    summary: str


class GitProvider(ABC):
    platform: Platform

    @abstractmethod
    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> list[DiffChunk]:
        """Fetch PR/MR file diffs as structured chunks."""

    @abstractmethod
    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str:
        """Get full file content at ref."""

    @abstractmethod
    async def get_readme_snippet(self, owner: str, repo: str, max_chars: int = 500) -> str:
        """Return README excerpt for context."""

    @abstractmethod
    async def get_pr_head_sha(self, owner: str, repo: str, pr_number: int) -> str:
        """Return latest commit SHA for the PR/MR head."""

    @abstractmethod
    async def post_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_id: str,
        summary: str,
        inline_comments: list[dict],
    ) -> PostedReview:
        """
        Post a batched review with inline comments.

        inline_comments: list of {path, line, body}
        """
