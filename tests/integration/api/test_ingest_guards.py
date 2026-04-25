from dataclasses import dataclass

from sentinelforge.db.session import get_db_session
from sentinelforge.main import app


@dataclass(slots=True)
class _FakePersistenceResult:
    """
    Resultado fake do service de ingestão.
    """
    decision: str
    raw_event_id: int


async def _fake_db_session():
    """
    Dependency override para o banco.

    Não queremos banco real nesses testes de integração da API.
    """
    yield object()


async def test_ingest_rejects_invalid_content_type(async_client):
    """
    Content-Type inválido deve retornar 415.
    """
    response = await async_client.post(
        "/api/v1/events",
        headers={"Authorization": "Bearer sentinel-ingest-dev-token"},
        content="nao sou json",
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "content-type must be application/json"


async def test_ingest_rejects_invalid_bearer_token(async_client):
    """
    Token inválido deve retornar 401.
    """
    response = await async_client.post(
        "/api/v1/events",
        headers={"Authorization": "Bearer token-errado"},
        json={
            "schema_version": "1.0",
            "event_id": "55555555-5555-5555-5555-555555555555",
            "tenant_id": "lab-acme",
            "category": "process",
            "occurred_at": "2026-04-25T12:20:00Z",
            "agent": {
                "agent_id": "agent-001",
                "host_id": "host-001",
                "hostname": "win-lab-01",
                "platform": "windows",
                "sensor_version": "0.1.0",
            },
            "payload": {
                "process_name": "powershell.exe"
            },
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid bearer token"


async def test_ingest_returns_accepted_response_with_mocked_services(async_client, monkeypatch):
    """
    Fluxo feliz da API deve responder 202 quando os serviços
    de persistência e publicação são simulados com sucesso.
    """
    app.dependency_overrides[get_db_session] = _fake_db_session

    async def fake_accept_event(**kwargs):
        return _FakePersistenceResult(
            decision="accepted",
            raw_event_id=999,
        )

    async def fake_publish_raw_ingested_event(**kwargs):
        return None

    monkeypatch.setattr(
        "sentinelforge.api.v1.endpoints.ingest.accept_event",
        fake_accept_event,
    )
    monkeypatch.setattr(
        "sentinelforge.api.v1.endpoints.ingest.publish_raw_ingested_event",
        fake_publish_raw_ingested_event,
    )

    response = await async_client.post(
        "/api/v1/events",
        headers={"Authorization": "Bearer sentinel-ingest-dev-token"},
        json={
            "schema_version": "1.0",
            "event_id": "66666666-6666-6666-6666-666666666666",
            "tenant_id": "lab-acme",
            "category": "process",
            "occurred_at": "2026-04-25T12:21:00Z",
            "agent": {
                "agent_id": "agent-001",
                "host_id": "host-001",
                "hostname": "win-lab-01",
                "platform": "windows",
                "sensor_version": "0.1.0",
            },
            "payload": {
                "process_name": "powershell.exe",
                "pid": 1234,
            },
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    assert response.json()["decision"] == "accepted"
    assert response.json()["event_id"] == "66666666-6666-6666-6666-666666666666"