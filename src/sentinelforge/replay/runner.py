import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import select

from sentinelforge.core.settings import get_settings
from sentinelforge.db.session import SessionFactory
from sentinelforge.models.alert import Alert
from sentinelforge.schemas.events import TelemetryEvent
from sentinelforge.schemas.replay import ReplayDataset, load_replay_dataset


async def main() -> None:
    """
    Runner principal do replay.

    Fluxo:
    1. carrega dataset
    2. opcionalmente reescreve event_ids
    3. envia eventos para a API
    4. espera o pipeline assíncrono estabilizar
    5. consulta alertas gerados
    6. calcula benchmark
    7. salva relatório JSON
    """
    args = _parse_args()
    settings = get_settings()

    dataset = load_replay_dataset(args.dataset)
    replay_events = _prepare_events(
        dataset=dataset,
        preserve_event_ids=args.preserve_event_ids,
    )

    started_at = datetime.now(timezone.utc)

    send_results = await _send_events(
        dataset=dataset,
        events=replay_events,
        base_url=args.base_url,
        token=settings.ingest_shared_token.get_secret_value(),
    )

    # Espera o pipeline assíncrono terminar as etapas
    # de Kafka, normalização e detecção.
    await asyncio.sleep(settings.replay_settle_seconds)

    observed_alerts = await _load_alerts_for_events(
        event_ids=[str(event.event_id) for event in replay_events]
    )

    report = _build_report(
        dataset=dataset,
        events=replay_events,
        send_results=send_results,
        observed_alerts=observed_alerts,
        started_at=started_at,
    )

    report_path = _write_report(
        dataset_name=dataset.dataset_name,
        report=report,
        output_dir=Path(settings.replay_output_dir),
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nreport_saved_at={report_path}")


def _parse_args() -> argparse.Namespace:
    """
    Lê os argumentos de linha de comando do runner.
    """
    parser = argparse.ArgumentParser(
        description="Replay de dataset e benchmark do SentinelForge."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Caminho do arquivo JSON do dataset.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="URL base da API de ingestão.",
    )
    parser.add_argument(
        "--preserve-event-ids",
        action="store_true",
        help="Mantém os event_ids do dataset em vez de gerar novos UUIDs.",
    )
    return parser.parse_args()


def _prepare_events(
    *,
    dataset: ReplayDataset,
    preserve_event_ids: bool,
) -> list[TelemetryEvent]:
    """
    Gera a lista final de eventos a enviar.

    Por padrão trocamos os event_ids por novos UUIDs, porque
    replays repetidos com IDs fixos virariam duplicados e
    estragariam o benchmark.
    """
    if preserve_event_ids:
        return dataset.events

    prepared_events: list[TelemetryEvent] = []

    for event in dataset.events:
        prepared_events.append(
            event.model_copy(update={"event_id": uuid4()})
        )

    return prepared_events


async def _send_events(
    *,
    dataset: ReplayDataset,
    events: list[TelemetryEvent],
    base_url: str,
    token: str,
) -> list[dict]:
    """
    Envia os eventos do dataset para a API de ingestão.

    Guardamos as respostas individuais porque isso ajuda
    a auditar accepted/duplicate e falhas HTTP.
    """
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=20.0) as client:
        for event in events:
            response = await client.post(
                f"{base_url}/api/v1/events",
                headers={"Authorization": f"Bearer {token}"},
                json=event.model_dump(mode="json"),
            )

            results.append(
                {
                    "event_id": str(event.event_id),
                    "http_status": response.status_code,
                    "response": response.json(),
                    "dataset_name": dataset.dataset_name,
                }
            )

    return results


async def _load_alerts_for_events(*, event_ids: list[str]) -> list[dict]:
    """
    Busca no banco os alertas gerados pelos event_ids do replay.

    Isso nos permite medir:
    - quais regras dispararam
    - quantos alertas surgiram
    - se houve ruído
    """
    async with SessionFactory() as session:
        rows = await session.execute(
            select(Alert).where(Alert.event_id.in_(event_ids))
        )
        alerts = rows.scalars().all()

    return [
        {
            "alert_id": alert.id,
            "alert_uid": str(alert.alert_uid),
            "event_id": str(alert.event_id),
            "rule_id": alert.rule_id,
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "title": alert.title,
            "hostname": alert.hostname,
            "created_at": alert.created_at.isoformat(),
        }
        for alert in alerts
    ]


def _build_report(
    *,
    dataset: ReplayDataset,
    events: list[TelemetryEvent],
    send_results: list[dict],
    observed_alerts: list[dict],
    started_at: datetime,
) -> dict:
    """
    Monta o relatório final do benchmark.

    O foco é responder:
    - enviamos quantos eventos?
    - quantos foram aceitos?
    - quais regras esperávamos?
    - quais regras observamos?
    - houve falsos positivos?
    - houve falsos negativos?
    """
    expected_rule_ids = sorted(set(dataset.expected_rule_ids))
    observed_rule_ids = sorted({alert["rule_id"] for alert in observed_alerts})

    false_positives = sorted(set(observed_rule_ids) - set(expected_rule_ids))
    false_negatives = sorted(set(expected_rule_ids) - set(observed_rule_ids))

    accepted_count = sum(
        1 for result in send_results
        if result["response"].get("decision") == "accepted"
    )
    duplicate_count = sum(
        1 for result in send_results
        if result["response"].get("decision") == "duplicate"
    )

    return {
        "dataset_name": dataset.dataset_name,
        "description": dataset.description,
        "notes": dataset.notes,
        "started_at": started_at.isoformat(),
        "events_sent": len(events),
        "accepted_count": accepted_count,
        "duplicate_count": duplicate_count,
        "expected_rule_ids": expected_rule_ids,
        "observed_rule_ids": observed_rule_ids,
        "false_positive_rule_ids": false_positives,
        "false_negative_rule_ids": false_negatives,
        "alerts_total": len(observed_alerts),
        "passed": not false_positives and not false_negatives,
        "sent_events": [
            {
                "event_id": str(event.event_id),
                "tenant_id": event.tenant_id,
                "category": event.category.value,
                "occurred_at": event.occurred_at.isoformat(),
            }
            for event in events
        ],
        "api_results": send_results,
        "observed_alerts": observed_alerts,
    }


def _write_report(
    *,
    dataset_name: str,
    report: dict,
    output_dir: Path,
) -> Path:
    """
    Salva o relatório do replay em disco.

    Isso facilita guardar evidência do benchmark e anexar
    no portfólio depois.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{dataset_name}_{timestamp}.json"
    path = output_dir / filename

    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return path


if __name__ == "__main__":
    asyncio.run(main())