
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
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

    agent_id: str = "desktop-casa"
    agent_token: str = "change-me-agent-token"
    server_ws_agent_url: str = "ws://server:8000/ws/agent"
    ws_heartbeat_interval: int = 15
    dry_run: bool = True


@lru_cache
def get_settings() -> AgentSettings:
    _load_agent_env_file()
    return AgentSettings()
