from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    return AgentSettings()
