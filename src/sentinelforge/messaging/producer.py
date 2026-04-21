import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

from sentinelforge.core.settings import get_settings

logger = logging.getLogger(__name__)

class KafkaProducerManager:
    """
    Gerencia o ciclo de vida do producer Kafka.

    Nesta fase usamos um singleton simples de processo para o producer.
    O objetivo é evitar criar conexão nova a cada request.
    """

    def __init__(self)  -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        settings = get_settings()

        if not settings.kafka_enabled:
            logger.info("kafka producer disabled by configuration")
            return

        if self._producer is not None:
            return

        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id=settings.kafka_client_id,
            acks="all",
            enable_idempotence=True,
            value_serializer=self._serialize_value,
        )

        await self._producer.start()
        logger.info(
            "kafka producer started",
            extra={
                "bootstrap_servers": settings.kafka_bootstrap_servers,
                "client_id": settings.kafka_client_id,
            },
        )

    async def stop(self) -> None:
        if self._producer is None:
            return

        await self._producer.stop()
        self._producer = None
        logger.info("kafka producer stopped")

    async def send_json(
        self,
        *,
        topic: str,
        key: str,
        value: dict[str, Any],
        headers: list[tuple[str, bytes]] | None = None,
    ):
        if self._producer is None:
            raise RuntimeError("kafka producer is not started")

        return await self._producer.send_and_wait(
            topic=topic,
            key=key.encode("utf-8"),
            value=value,
            headers=headers,
        )

    @staticmethod
    def _serialize_value(value: dict[str, Any]) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")


producer_manager = KafkaProducerManager()


def get_kafka_producer_manager() -> KafkaProducerManager:
    return producer_manager