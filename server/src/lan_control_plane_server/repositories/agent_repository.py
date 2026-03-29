from datetime import UTC, datetime

from lan_control_plane_server.db.models import Agent
from sqlalchemy import select
from sqlalchemy.orm import Session


class AgentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_host_id(self, host_id: str) -> Agent | None:
        statement = select(Agent).where(Agent.host_id == host_id)
        return self.session.scalar(statement)

    def get_all(self) -> list[Agent]:
        statement = select(Agent).order_by(Agent.last_seen_at.desc())
        return list(self.session.scalars(statement).all())

    def create_for_host(
        self,
        *,
        host_id: str,
        token_hash: str,
        version: str,
    ) -> Agent:
        agent = Agent(
            host_id=host_id,
            token_hash=token_hash,
            version=version,
            enabled=True,
            last_seen_at=datetime.now(UTC),
        )
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent

    def update_registration(
        self,
        agent: Agent,
        *,
        token_hash: str,
        version: str,
    ) -> Agent:
        agent.token_hash = token_hash
        agent.version = version
        agent.last_seen_at = datetime.now(UTC)
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent

    def touch_last_seen(self, agent: Agent) -> Agent:
        agent.last_seen_at = datetime.now(UTC)
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent
