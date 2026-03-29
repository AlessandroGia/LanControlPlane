from lan_control_plane_server.db.models import Agent

from .helpers import create_host

API_KEY_HEADER = {"X-API-Key": "dev-rest-api-key"}


def test_get_agents_returns_agents(client, db_session):
    host = create_host(db_session, name="desktop-casa", hostname="desktop-casa")

    agent = Agent(
        host_id=host.id,
        token_hash="hashed-token",
        version="0.1.0",
        enabled=True,
    )
    db_session.add(agent)
    db_session.commit()

    response = client.get("/agents", headers=API_KEY_HEADER)

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["host_name"] == "desktop-casa"
    assert payload[0]["version"] == "0.1.0"
    assert payload[0]["enabled"] is True


def test_get_agent_by_host_name_returns_agent(client, db_session):
    host = create_host(db_session, name="desktop-casa", hostname="desktop-casa")

    agent = Agent(
        host_id=host.id,
        token_hash="hashed-token",
        version="0.1.0",
        enabled=True,
    )
    db_session.add(agent)
    db_session.commit()

    response = client.get("/agents/desktop-casa", headers=API_KEY_HEADER)

    assert response.status_code == 200
    payload = response.json()

    assert payload["host_name"] == "desktop-casa"
    assert payload["version"] == "0.1.0"
