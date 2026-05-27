"""LLM reviewer with Groq → Together → HuggingFace → Ollama fallback chain."""

import json
import logging
import re
from typing import Any

import httpx

from backend.config import Settings, get_settings
from backend.models import (
    DiffChunk,
    IssueCategory,
    LLMReviewResult,
    ReviewIssue,
    Severity,
)
from backend.review_engine.context_builder import ContextBuilder

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert code reviewer with 15+ years of experience.
Review the following code diff and provide structured feedback.
Focus on: bugs, security vulnerabilities, performance issues, maintainability.
Be specific, actionable, and kind. Reference exact line numbers from the NEW file.
Respond ONLY in valid JSON matching this schema (no markdown):
{
  "summary": "string",
  "issues": [
    {
      "severity": "critical|high|medium|low|info",
      "category": "security|performance|bug|style|maintainability",
      "line_number": 0,
      "title": "string",
      "description": "string",
      "suggestion": "string",
      "confidence": 0.0
    }
  ],
  "positive_feedback": ["string"],
  "refactoring_suggestion": "string",
  "complexity_score": 0
}
"""

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


class LLMReviewer:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.context_builder = ContextBuilder()
        self.timeout = self.settings.llm_timeout_seconds

    async def review_chunk(
        self,
        prompt_context: str,
        chunk: DiffChunk,
    ) -> LLMReviewResult:
        user_prompt = f"{prompt_context}\n\nFile path for issues: {chunk.file_path}"
        raw = await self._call_with_fallback(user_prompt)
        return self._parse_response(raw, chunk.file_path)

    async def _call_with_fallback(self, user_prompt: str) -> str:
        providers = [
            self._call_groq,
            self._call_together,
            self._call_huggingface,
            self._call_ollama,
        ]
        errors: list[str] = []
        for provider in providers:
            try:
                result = await provider(user_prompt)
                if result:
                    return result
            except Exception as exc:
                msg = f"{provider.__name__}: {exc}"
                logger.warning(msg)
                errors.append(msg)
        raise RuntimeError(
            "All LLM providers failed. " + "; ".join(errors)
        )

    async def _call_groq(self, user_prompt: str) -> str:
        if not self.settings.groq_api_key:
            return ""
        return await self._openai_compatible(
            base_url="https://api.groq.com/openai/v1/chat/completions",
            api_key=self.settings.groq_api_key,
            model=self.settings.groq_model,
            user_prompt=user_prompt,
        )

    async def _call_together(self, user_prompt: str) -> str:
        if not self.settings.together_api_key:
            return ""
        return await self._openai_compatible(
            base_url="https://api.together.xyz/v1/chat/completions",
            api_key=self.settings.together_api_key,
            model=self.settings.together_model,
            user_prompt=user_prompt,
        )

    async def _call_huggingface(self, user_prompt: str) -> str:
        if not self.settings.hf_api_token:
            return ""
        return await self._openai_compatible(
            base_url="https://api-inference.huggingface.co/models",
            api_key=self.settings.hf_api_token,
            model=self.settings.hf_model,
            user_prompt=user_prompt,
            use_full_url=False,
        )

    async def _call_ollama(self, user_prompt: str) -> str:
        base = self.settings.ollama_base_url.rstrip("/")
        url = f"{base}/api/chat"
        payload = {
            "model": self.settings.ollama_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def _openai_compatible(
        self,
        base_url: str,
        api_key: str,
        model: str,
        user_prompt: str,
        use_full_url: bool = True,
    ) -> str:
        url = (
            f"{base_url.rstrip('/')}/chat/completions"
            if use_full_url
            else f"{base_url.rstrip('/')}/v1/chat/completions"
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _parse_response(self, raw: str, file_path: str) -> LLMReviewResult:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                logger.error("Failed to parse LLM JSON: %s", raw[:500])
                return LLMReviewResult(
                    summary="AI review could not be parsed. Please check logs.",
                    issues=[],
                )
            data = json.loads(match.group())

        issues: list[ReviewIssue] = []
        for item in data.get("issues", []):
            try:
                severity = SEVERITY_MAP.get(
                    str(item.get("severity", "medium")).lower(), Severity.MEDIUM
                )
                category = CATEGORY_MAP.get(
                    str(item.get("category", "bug")).lower(), IssueCategory.BUG
                )
                issues.append(
                    ReviewIssue(
                        severity=severity,
                        category=category,
                        file_path=file_path,
                        line_number=int(item.get("line_number", 1)),
                        title=str(item.get("title", "Issue")),
                        description=str(item.get("description", "")),
                        suggestion=str(item.get("suggestion", "")),
                        confidence=float(item.get("confidence", 0.75)),
                        source="llm",
                    )
                )
            except (TypeError, ValueError) as exc:
                logger.warning("Skipping malformed issue: %s", exc)

        return LLMReviewResult(
            summary=str(data.get("summary", "")),
            issues=issues,
            positive_feedback=list(data.get("positive_feedback", [])),
            refactoring_suggestion=str(data.get("refactoring_suggestion", "")),
            complexity_score=int(data.get("complexity_score", 0)),
        )
