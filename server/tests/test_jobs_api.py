from lan_control_plane_server.db.models import Job

from .helpers import create_host


def test_get_jobs_returns_jobs(authenticated_client, db_session):
    host = create_host(db_session, name="desktop-casa", hostname="desktop-casa")

    job = Job(
        host_id=host.id,
        command="shutdown",
        status="pending",
        requested_by="admin",
    )
    db_session.add(job)
    db_session.commit()

    response = authenticated_client.get("/jobs")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["command"] == "shutdown"
    assert payload[0]["status"] == "pending"
