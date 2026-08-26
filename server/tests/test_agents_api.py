from lan_control_plane_server.db.models import Agent

from .helpers import create_host


def test_get_agents_returns_agents(authenticated_client, db_session):
    host = create_host(db_session, name="desktop-casa", hostname="desktop-casa")

    agent = Agent(
        host_id=host.id,
        token_hash="hashed-token",
        version="0.1.0",
        enabled=True,
    )
    db_session.add(agent)
    db_session.commit()

    response = authenticated_client.get("/agents")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["host_name"] == "desktop-casa"
    assert payload[0]["version"] == "0.1.0"
    assert payload[0]["enabled"] is True


def test_get_agent_by_host_name_returns_agent(authenticated_client, db_session):
    host = create_host(db_session, name="desktop-casa", hostname="desktop-casa")

    agent = Agent(
        host_id=host.id,
        token_hash="hashed-token",
        version="0.1.0",
        enabled=True,
    )
    db_session.add(agent)
    db_session.commit()

    response = authenticated_client.get("/agents/desktop-casa")

    assert response.status_code == 200
    payload = response.json()

    assert payload["host_name"] == "desktop-casa"
    assert payload["version"] == "0.1.0"
