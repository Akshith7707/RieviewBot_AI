"""Build rich context for LLM review chunks."""

from backend.models import DiffChunk, PRContext, ReviewIssue
from backend.review_engine.diff_parser import chunk_to_text


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20] + "\n... [truncated]"


class ContextBuilder:
    MAX_FILE_CHARS = 8000
    MAX_DIFF_CHARS = 6000
    MAX_MEMORY_CHARS = 2000

    def build(
        self,
        ctx: PRContext,
        chunk: DiffChunk,
        full_file: str = "",
        security_issues: list[ReviewIssue] | None = None,
    ) -> str:
        security_issues = security_issues or []
        security_block = ""
        if security_issues:
            lines = ["## Pre-scan Security Findings (deterministic)"]
            for issue in security_issues[:10]:
                lines.append(
                    f"- [{issue.severity.value}] {issue.title} "
                    f"at line {issue.line_number}: {issue.description}"
                )
            security_block = "\n".join(lines)

        readme = _truncate(ctx.readme_snippet, 500) if ctx.readme_snippet else ""
        file_content = _truncate(full_file, self.MAX_FILE_CHARS) if full_file else ""
        diff_text = _truncate(chunk_to_text(chunk), self.MAX_DIFF_CHARS)

        parts = [
            f"## Project: {ctx.owner}/{ctx.repo}",
        ]
        if readme:
            parts.extend(["", "## README excerpt", readme])
        parts.extend(
            [
                "",
                "## PR Goal",
                f"**{ctx.title or 'Untitled PR'}**",
                ctx.description or "(no description)",
                "",
                f"## File: {chunk.file_path} ({chunk.language})",
            ]
        )
        if file_content:
            parts.extend(["", "## Full file (context)", "```", file_content, "```"])
        parts.extend(["", "## Diff to review", "```diff", diff_text, "```"])
        if security_block:
            parts.extend(["", security_block])
        parts.extend(
            [
                "",
                "Review the diff carefully. Return ONLY valid JSON matching the schema.",
            ]
        )
        return "\n".join(parts)
