import os
from functools import lru_cache
from pathlib import Path
from typing import Self

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_agent_env_file() -> Path | None:
    candidates: list[Path] = []

    explicit_env_file = os.getenv("AGENT_ENV_FILE")
    if explicit_env_file:
        candidates.append(Path(explicit_env_file))

    candidates.extend(
        [
            Path.cwd() / "agent.env",
            Path.cwd() / ".env",
            Path(__file__).resolve().parents[3] / "agent.env",
            Path(__file__).resolve().parents[3] / ".env",
        ]
    )

    for candidate in candidates:
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return candidate

    return None


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    agent_id: str = Field(default="desktop-casa", min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    agent_token: str = Field(default="change-me-agent-token", min_length=16, max_length=512)
    agent_enrollment_token: str | None = Field(default=None, min_length=16, max_length=512)
    server_ws_agent_url: str = "ws://server:8000/ws/agent"
    ws_heartbeat_interval: int = Field(default=15, ge=5, le=300)
    dry_run: bool = True

    @model_validator(mode="after")
    def reject_placeholder_live_credential(self) -> Self:
        if not self.dry_run and self.agent_token == "change-me-agent-token":
            raise ValueError("AGENT_TOKEN must be configured when DRY_RUN is false")
        return self


@lru_cache
def get_settings() -> AgentSettings:
    _load_agent_env_file()
    return AgentSettings()
