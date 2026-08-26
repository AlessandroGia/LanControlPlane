import hashlib
from datetime import UTC, datetime
from hmac import compare_digest

from sqlalchemy.orm import Session

from lan_control_plane_server.core.config import get_settings
from lan_control_plane_server.db.models import Agent, Host
from lan_control_plane_server.repositories.agent_repository import AgentRepository
from lan_control_plane_server.repositories.host_repository import HostRepository


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AgentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.agent_repository = AgentRepository(session)
        self.host_repository = HostRepository(session)

    def authorize_connection(
        self,
        *,
        host_name: str,
        token: str,
        enrollment_token: str | None,
    ) -> None:
        host = self.host_repository.get_by_name(host_name)
        existing = self.agent_repository.get_by_host_id(host.id) if host is not None else None
        if existing is None:
            expected_enrollment_token = get_settings().agent_enrollment_token
            if enrollment_token is None or not compare_digest(enrollment_token, expected_enrollment_token):
                raise PermissionError("Invalid agent enrollment credentials")
            if self.agent_repository.get_by_token_hash(hash_token(token)) is not None:
                raise PermissionError("Agent credential is already assigned to another host")
            return

        if not existing.enabled:
            raise PermissionError("Agent is disabled")

        if not compare_digest(existing.token_hash, hash_token(token)):
            raise PermissionError("Invalid agent credentials")

    def register_or_update_agent(
        self,
        *,
        host: Host,
        token: str,
        version: str,
    ) -> Agent:
        existing = self.agent_repository.get_by_host_id(host.id)
        if existing is None:
            return self.agent_repository.create_for_host(
                host_id=host.id,
                token_hash=hash_token(token),
                version=version,
            )

        if not existing.enabled:
            raise PermissionError("Agent is disabled")

        return self.agent_repository.update_registration(
            existing,
            version=version,
        )

    def touch_agent_last_seen(self, *, host: Host) -> Agent | None:
        agent = self.agent_repository.get_by_host_id(host.id)
        if agent is None:
            return None

        agent.last_seen_at = datetime.now(UTC)
        self.session.add(agent)
        self.session.flush()
        return agent

    def get_agent_for_host(self, *, host: Host) -> Agent | None:
        return self.agent_repository.get_by_host_id(host.id)

    def get_agents(self) -> list[Agent]:
        return self.agent_repository.get_all()

    def get_agent_by_host_name(self, host_name: str) -> Agent | None:
        host = self.host_repository.get_by_name(host_name)
        if host is None:
            return None
        return self.agent_repository.get_by_host_id(host.id)
