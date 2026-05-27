"""Parse PR/MR diffs into structured chunks for the review engine."""

import re
from pathlib import Path

from backend.models import DiffChange, DiffChunk, DiffHunk

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".rs": "rust",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sql": "sql",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".sh": "shell",
    ".bash": "shell",
    ".ps1": "powershell",
    ".html": "html",
    ".css": "css",
    ".vue": "vue",
    ".dart": "dart",
}

STATUS_MAP = {
    "added": "added",
    "removed": "deleted",
    "deleted": "deleted",
    "modified": "modified",
    "renamed": "renamed",
}


def detect_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    return LANGUAGE_MAP.get(ext, "unknown")


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def parse_unified_patch(file_path: str, patch: str, status: str = "modified") -> DiffChunk:
    """Parse a unified diff patch string into a DiffChunk."""
    hunks: list[DiffHunk] = []
    current_hunk: DiffHunk | None = None
    old_start = new_start = 0
    additions = deletions = 0

    hunk_header = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    for line in patch.splitlines():
        header_match = hunk_header.match(line)
        if header_match:
            if current_hunk:
                hunks.append(current_hunk)
            old_start = int(header_match.group(1))
            new_start = int(header_match.group(2))
            current_hunk = DiffHunk(old_start=old_start, new_start=new_start)
            continue

        if current_hunk is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            line_no = new_start + sum(
                1 for c in current_hunk.changes if c.type in ("add", "context")
            )
            current_hunk.changes.append(
                DiffChange(type="add", line_no=line_no, content=line[1:])
            )
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            line_no = old_start
            current_hunk.changes.append(
                DiffChange(type="del", line_no=line_no, content=line[1:])
            )
            deletions += 1
        elif line.startswith(" "):
            current_hunk.changes.append(
                DiffChange(type="context", line_no=new_start, content=line[1:])
            )

    if current_hunk:
        hunks.append(current_hunk)

    change_type = STATUS_MAP.get(status, "modified")
    return DiffChunk(
        file_path=file_path,
        language=detect_language(file_path),
        change_type=change_type,  # type: ignore[arg-type]
        old_path=file_path,
        additions=additions,
        deletions=deletions,
        hunks=hunks,
        patch=patch,
    )


def parse_github_file_diffs(files: list[dict]) -> list[DiffChunk]:
    chunks: list[DiffChunk] = []
    for f in files:
        patch = f.get("patch") or ""
        if not patch:
            continue
        path = f.get("filename", "")
        status = f.get("status", "modified")
        chunk = parse_unified_patch(path, patch, status)
        chunk.additions = f.get("additions", chunk.additions)
        chunk.deletions = f.get("deletions", chunk.deletions)
        old_path = f.get("previous_filename")
        if old_path:
            chunk.old_path = old_path
        chunks.append(chunk)
    return chunks


def parse_gitlab_mr_diffs(changes: list[dict]) -> list[DiffChunk]:
    chunks: list[DiffChunk] = []
    for change in changes:
        path = change.get("new_path") or change.get("old_path", "")
        diff = change.get("diff") or ""
        if not diff or not path:
            continue
        deleted = change.get("deleted_file", False)
        new_file = change.get("new_file", False)
        if new_file:
            status = "added"
        elif deleted:
            status = "deleted"
        elif change.get("renamed_file"):
            status = "renamed"
        else:
            status = "modified"
        chunk = parse_unified_patch(path, diff, status)
        chunk.old_path = change.get("old_path")
        chunks.append(chunk)
    return chunks


def chunk_to_text(chunk: DiffChunk) -> str:
    """Render chunk as text for LLM consumption."""
    lines = [f"File: {chunk.file_path} ({chunk.language})", f"Change: {chunk.change_type}"]
    if chunk.patch:
        lines.append(chunk.patch)
    else:
        for hunk in chunk.hunks:
            lines.append(f"@@ -{hunk.old_start} +{hunk.new_start} @@")
            for change in hunk.changes:
                prefix = {"add": "+", "del": "-", "context": " "}.get(change.type, " ")
                lines.append(f"{prefix}{change.content}")
    return "\n".join(lines)


def chunk_large_diff(chunks: list[DiffChunk], max_tokens: int = 3000) -> list[DiffChunk]:
    """Split oversized chunks by returning multiple sub-chunks with truncated patches."""
    result: list[DiffChunk] = []
    for chunk in chunks:
        text = chunk_to_text(chunk)
        if _estimate_tokens(text) <= max_tokens:
            result.append(chunk)
            continue
        lines = chunk.patch.splitlines() if chunk.patch else []
        batch: list[str] = []
        batch_tokens = 0
        part = 1
        for line in lines:
            line_tokens = _estimate_tokens(line)
            if batch_tokens + line_tokens > max_tokens and batch:
                sub_patch = "\n".join(batch)
                result.append(
                    DiffChunk(
                        file_path=f"{chunk.file_path} (part {part})",
                        language=chunk.language,
                        change_type=chunk.change_type,
                        old_path=chunk.old_path,
                        patch=sub_patch,
                        hunks=[],
                    )
                )
                part += 1
                batch = []
                batch_tokens = 0
            batch.append(line)
            batch_tokens += line_tokens
        if batch:
            sub_patch = "\n".join(batch)
            result.append(
                DiffChunk(
                    file_path=f"{chunk.file_path} (part {part})" if part > 1 else chunk.file_path,
                    language=chunk.language,
                    change_type=chunk.change_type,
                    old_path=chunk.old_path,
                    patch=sub_patch,
                    hunks=[],
                )
            )
    return result


def extract_function_signatures(chunk: DiffChunk) -> list[str]:
    """Detect function/class signatures touched in the diff."""
    patterns = [
        re.compile(r"^[+\-]?\s*def\s+(\w+)\s*\(", re.MULTILINE),
        re.compile(r"^[+\-]?\s*class\s+(\w+)", re.MULTILINE),
        re.compile(r"^[+\-]?\s*(?:async\s+)?function\s+(\w+)", re.MULTILINE),
        re.compile(r"^[+\-]?\s*(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(", re.MULTILINE),
    ]
    text = chunk.patch or chunk_to_text(chunk)
    found: list[str] = []
    for pat in patterns:
        found.extend(pat.findall(text))
    return list(dict.fromkeys(found))
