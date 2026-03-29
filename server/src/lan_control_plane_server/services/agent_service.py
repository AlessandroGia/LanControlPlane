import hashlib

from lan_control_plane_server.db.models import Agent, Host
from lan_control_plane_server.repositories.agent_repository import AgentRepository
from lan_control_plane_server.repositories.host_repository import HostRepository
from sqlalchemy.orm import Session
from datetime import datetime, UTC


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AgentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.agent_repository = AgentRepository(session)
        self.host_repository = HostRepository(session)

    def register_or_update_agent(
        self,
        *,
        host: Host,
        token: str,
        version: str,
    ) -> Agent:
        token_hash = hash_token(token)

        existing = self.agent_repository.get_by_host_id(host.id)
        if existing is None:
            return self.agent_repository.create_for_host(
                host_id=host.id,
                token_hash=token_hash,
                version=version,
            )

        if not existing.enabled:
            raise PermissionError("Agent is disabled")

        return self.agent_repository.update_registration(
            existing,
            token_hash=token_hash,
            version=version,
        )

    def touch_agent_last_seen(self, *, host: Host) -> Agent | None:
        agent = self.agent_repository.get_by_host_id(host.id)
        if agent is None:
            return None

        agent.last_seen_at = datetime.now(UTC)
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
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
