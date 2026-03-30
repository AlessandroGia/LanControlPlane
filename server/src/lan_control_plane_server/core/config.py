from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    database_url: str = "sqlite:////app/data/lan_control_plane.db"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    ws_heartbeat_interval: int = 15

    rest_api_key: str = Field(default="dev-rest-api-key", alias="REST_API_KEY")
    client_token: str = Field(default="dev-client-token", alias="CLIENT_TOKEN")
    agent_token: str = Field(default="change-me-agent-token", alias="AGENT_TOKEN")
    wol_helper_base_url: str = Field(default="http://localhost:8099", alias="WOL_HELPER_BASE_URL")
    wol_broadcast_ip: str = Field(default="255.255.255", alias="WOL_BROADCAST_IP")
    wol_port: int = Field(default=9, alias="WOL_PORT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
