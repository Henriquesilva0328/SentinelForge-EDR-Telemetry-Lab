import pytest
from httpx import ASGITransport, AsyncClient

from sentinelforge.main import app


class _FakeProducerManager:
    """
    Fake simples do producer Kafka.

    Nos testes de API não queremos depender de Kafka real.
    Então neutralizamos startup/shutdown do producer.
    """

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None


@pytest.fixture(autouse=True)
def patch_app_lifespan_dependencies(monkeypatch):
    """
    Evita que o lifespan da aplicação tente falar com Kafka real.

    Isso mantém os testes de API rápidos, determinísticos
    e independentes da infraestrutura externa.
    """
    monkeypatch.setattr(
        "sentinelforge.main.get_kafka_producer_manager",
        lambda: _FakeProducerManager(),
    )


@pytest.fixture
async def async_client():
    """
    Cliente HTTP assíncrono acoplado diretamente ao app ASGI.

    Isso permite testar a API sem subir Uvicorn de verdade.
    """
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client