from lan_control_plane_server.core.config import Settings


def test_legacy_agent_token_is_accepted_as_enrollment_fallback(monkeypatch) -> None:
    monkeypatch.delenv("AGENT_ENROLLMENT_TOKEN", raising=False)
    monkeypatch.setenv("AGENT_TOKEN", "legacy-agent-token-123456789")

    settings = Settings(_env_file=None)

    assert settings.agent_enrollment_token == "legacy-agent-token-123456789"


def test_new_enrollment_token_takes_precedence(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_ENROLLMENT_TOKEN", "new-enrollment-token-123456789")
    monkeypatch.setenv("AGENT_TOKEN", "legacy-agent-token-123456789")

    settings = Settings(_env_file=None)

    assert settings.agent_enrollment_token == "new-enrollment-token-123456789"
