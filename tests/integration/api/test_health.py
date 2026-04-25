async def test_health_endpoint_returns_ok(async_client):
    """
    Healthcheck deve responder 200 e status ok.
    """
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"