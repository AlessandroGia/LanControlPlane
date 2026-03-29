from fastapi import APIRouter, Depends, HTTPException
from lan_control_plane_server.api.deps import require_api_key
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.schemas.agent import AgentRead
from lan_control_plane_server.services.agent_service import AgentService
from lan_control_plane_server.services.host_service import HostService
from lan_control_plane_server.api.deps import get_current_user_from_session
from lan_control_plane_server.db.models import User

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    dependencies=[Depends(get_current_user_from_session)],
)


@router.get("", response_model=list[AgentRead])
async def get_agents() -> list[AgentRead]:
    session = SessionLocal()
    try:
        agent_service = AgentService(session)
        host_service = HostService(session)

        agents = agent_service.get_agents()
        result: list[AgentRead] = []

        for agent in agents:
            host = host_service.get_host_by_id(agent.host_id)
            if host is None:
                continue

            result.append(
                AgentRead(
                    id=agent.id,
                    host_id=agent.host_id,
                    host_name=host.name,
                    version=agent.version,
                    enabled=agent.enabled,
                    last_seen_at=agent.last_seen_at,
                )
            )

        return result
    finally:
        session.close()


@router.get("/{host_name}", response_model=AgentRead)
async def get_agent(host_name: str) -> AgentRead:
    session = SessionLocal()
    try:
        agent_service = AgentService(session)
        host_service = HostService(session)

        agent = agent_service.get_agent_by_host_name(host_name)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")

        host = host_service.get_host_by_id(agent.host_id)
        if host is None:
            raise HTTPException(status_code=404, detail="Host not found for agent")

        return AgentRead(
            id=agent.id,
            host_id=agent.host_id,
            host_name=host.name,
            version=agent.version,
            enabled=agent.enabled,
            last_seen_at=agent.last_seen_at,
        )
    finally:
        session.close()
