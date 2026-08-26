from functools import lru_cache
from ipaddress import IPv4Address
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    server_host: str = "0.0.0.0"
    server_port: int = Field(default=8000, ge=1, le=65535)
    database_url: str = Field(default="sqlite:////app/server/data/lan_control_plane.db", min_length=1)
    access_token_expire_minutes: int = Field(default=60, ge=5, le=43200)
    session_cookie_secure: bool | None = None
    session_touch_interval_seconds: int = Field(default=300, ge=30, le=3600)
    agent_offline_after_seconds: int = Field(default=60, ge=15, le=3600)
    metrics_retention_days: int = Field(default=30, ge=1, le=3650)

    agent_enrollment_token: str = Field(
        default="change-me-agent-enrollment-token",
        min_length=16,
        max_length=512,
        alias="AGENT_ENROLLMENT_TOKEN",
    )
    wol_helper_base_url: str = Field(default="http://localhost:8099", alias="WOL_HELPER_BASE_URL")
    wol_helper_token: str = Field(
        default="change-me-wol-helper-token",
        min_length=16,
        max_length=512,
        alias="WOL_HELPER_TOKEN",
    )
    wol_broadcast_ip: IPv4Address = Field(default=IPv4Address("255.255.255.255"), alias="WOL_BROADCAST_IP")
    wol_port: int = Field(default=9, ge=1, le=65535, alias="WOL_PORT")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "https://control.giacento.com"],
        alias="CORS_ORIGINS",
    )

    @property
    def cookie_secure(self) -> bool:
        if self.session_cookie_secure is not None:
            return self.session_cookie_secure
        return self.app_env.lower() == "production"

    @model_validator(mode="after")
    def reject_placeholder_production_secrets(self) -> Self:
        if self.app_env.lower() != "production":
            return self
        placeholders = {
            "AGENT_ENROLLMENT_TOKEN": "change-me-agent-enrollment-token",
            "WOL_HELPER_TOKEN": "change-me-wol-helper-token",
        }
        configured = {
            "AGENT_ENROLLMENT_TOKEN": self.agent_enrollment_token,
            "WOL_HELPER_TOKEN": self.wol_helper_token,
        }
        insecure = [name for name, placeholder in placeholders.items() if configured[name] == placeholder]
        if insecure:
            raise ValueError(f"Production secrets must be configured: {', '.join(insecure)}")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
