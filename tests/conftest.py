import pytest
from httpx import ASGITransport, AsyncClient


class _FakeProducerManager:
    """
    Fake simples do producer Kafka.

    Nos testes de API não queremos depender de Kafka real.
    Então neutralizamos startup e shutdown do producer.
    """

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None


@pytest.fixture(autouse=True)
def patch_app_lifespan_dependencies(monkeypatch):
    """
    Evita que o lifespan da aplicação tente falar com Kafka real.

    O patch é aplicado antes de importarmos a aplicação dentro
    da fixture do client, reduzindo efeitos colaterais no import.
    """
    monkeypatch.setattr(
        "sentinelforge.main.get_kafka_producer_manager",
        lambda: _FakeProducerManager(),
    )


@pytest.fixture
async def async_client():
    """
    Cliente HTTP assíncrono acoplado diretamente ao app ASGI.

    Importamos o app dentro da fixture para evitar side effects
    globais em tempo de import do conftest.
    """
    from sentinelforge.main import app

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client