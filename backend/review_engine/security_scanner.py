"""Rule-based OWASP security scanner — runs before LLM."""

import logging
import re
from pathlib import Path

import yaml

from backend.models import IssueCategory, ReviewIssue, Severity

logger = logging.getLogger(__name__)

RULES_PATH = Path(__file__).resolve().parents[2] / "rules" / "security.yaml"

SEVERITY_MAP = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
}

CATEGORY_MAP = {
    "security": IssueCategory.SECURITY,
    "performance": IssueCategory.PERFORMANCE,
    "bug": IssueCategory.BUG,
    "style": IssueCategory.STYLE,
    "maintainability": IssueCategory.MAINTAINABILITY,
}


class SecurityScanner:
    def __init__(self, rules_path: Path | None = None) -> None:
        self._rules_path = rules_path or RULES_PATH
        self._rules: list[dict] = []
        self._load_rules()

    def _load_rules(self) -> None:
        if not self._rules_path.exists():
            logger.warning("Security rules file not found: %s", self._rules_path)
            return
        with open(self._rules_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._rules = data.get("rules", [])
        logger.info("Loaded %d security rules", len(self._rules))

    def scan_file(
        self, file_path: str, language: str, content: str
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        lines = content.splitlines()

        for rule in self._rules:
            rule_langs = rule.get("languages", [])
            if rule_langs and language not in rule_langs and language != "unknown":
                continue

            try:
                pattern = re.compile(rule["pattern"])
            except re.error as exc:
                logger.warning("Invalid regex in rule %s: %s", rule.get("id"), exc)
                continue

            for line_no, line in enumerate(lines, start=1):
                if pattern.search(line):
                    severity = SEVERITY_MAP.get(
                        rule.get("severity", "medium"), Severity.MEDIUM
                    )
                    category = CATEGORY_MAP.get(
                        rule.get("category", "security"), IssueCategory.SECURITY
                    )
                    issues.append(
                        ReviewIssue(
                            severity=severity,
                            category=category,
                            file_path=file_path,
                            line_number=line_no,
                            title=rule.get("name", rule.get("id", "Security Issue")),
                            description=rule.get("message", "Security pattern matched"),
                            suggestion=rule.get("suggestion", ""),
                            confidence=0.95,
                            source="security_scanner",
                        )
                    )
        return issues

    def scan_patch(self, file_path: str, language: str, patch: str) -> list[ReviewIssue]:
        """Scan only added lines in a patch."""
        added_lines: list[tuple[int, str]] = []
        new_line = 0
        for line in patch.splitlines():
            if line.startswith("@@"):
                match = re.search(r"\+(\d+)", line)
                if match:
                    new_line = int(match.group(1)) - 1
                continue
            if line.startswith("+") and not line.startswith("+++"):
                new_line += 1
                added_lines.append((new_line, line[1:]))
            elif line.startswith(" ") or line.startswith("-"):
                if not line.startswith("-"):
                    new_line += 1

        synthetic_content = "\n".join(text for _, text in added_lines)
        if not synthetic_content:
            return []

        raw_issues = self.scan_file(file_path, language, synthetic_content)
        line_map = {text: ln for ln, text in added_lines}

        for issue in raw_issues:
            for text, ln in line_map.items():
                if text in patch:
                    issue.line_number = ln
                    break
        return raw_issues
