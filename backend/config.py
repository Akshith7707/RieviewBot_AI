"""Application configuration loaded from environment variables."""

from functools import lru_cache
import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM providers (at least one recommended)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    together_api_key: str = ""
    together_model: str = "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
    hf_api_token: str = ""
    hf_model: str = "bigcode/starcoder2-15b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "codellama"

    # GitHub
    github_token: str = ""
    github_webhook_secret: str = ""

    # GitLab
    gitlab_token: str = ""
    gitlab_url: str = "https://gitlab.com"
    gitlab_webhook_secret: str = ""

    # Storage
    database_url: str = "sqlite+aiosqlite:///./data/reviewbot.db"

    # Review limits
    max_comments_per_pr: int = Field(default=15, alias="MAX_COMMENTS_PER_PR")
    llm_timeout_seconds: int = 30

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    dashboard_url: str = "http://localhost:5173"

    # Optional (post-MVP)
    redis_url: str = ""
    slack_webhook_url: str = ""
    discord_webhook_url: str = ""

    @property
    def sqlite_path(self) -> str:
        """Extract filesystem path from database_url."""
        url = self.database_url
        if url.startswith("sqlite+aiosqlite:///"):
            return url.replace("sqlite+aiosqlite:///", "")
        if url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "")
        return "./data/reviewbot.db"

    def has_llm_provider(self) -> bool:
        return bool(
            self.groq_api_key
            or self.together_api_key
            or self.hf_api_token
            or self.ollama_base_url
        )

    def validate_startup(self) -> list[str]:
        warnings: list[str] = []
        if not self.has_llm_provider():
            warnings.append(
                "No LLM API key configured. Set GROQ_API_KEY (recommended) or fallbacks."
            )
        if not self.github_token and not self.gitlab_token:
            warnings.append(
                "No GITHUB_TOKEN or GITLAB_TOKEN set. Git API calls will fail."
            )
        return warnings


@lru_cache
def get_settings() -> Settings:
    return Settings()
