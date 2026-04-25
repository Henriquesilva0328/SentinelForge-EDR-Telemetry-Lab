import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelforge.models.alert import Alert
from sentinelforge.models.alert_evidence import AlertEvidence
from sentinelforge.observability.metrics import observe_alert_created
from sentinelforge.schemas.normalized import NormalizedPublishedMessage
from sentinelforge.services.detection_service import DetectionMatch

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AlertPersistenceSummary:
    created_count: int
    duplicate_count: int


async def persist_alerts(
    *,
    normalized_message: NormalizedPublishedMessage,
    matches: list[DetectionMatch],
    session: AsyncSession,
) -> AlertPersistenceSummary:
    """
    Persiste alertas e evidências, evitando repetição por
    (rule_id, normalized_event_id).
    """
    created_count = 0
    duplicate_count = 0

    for match in matches:
        existing_alert_id = await session.scalar(
            select(Alert.id).where(
                Alert.rule_id == match.rule_id,
                Alert.normalized_event_id == normalized_message.normalized_event_id,
            )
        )

        if existing_alert_id is not None:
            duplicate_count += 1

            logger.info(
                "alert already exists for normalized event",
                extra={
                    "rule_id": match.rule_id,
                    "normalized_event_id": normalized_message.normalized_event_id,
                    "alert_id": existing_alert_id,
                },
            )
            continue

        alert = Alert(
            normalized_event_id=normalized_message.normalized_event_id,
            raw_event_id=normalized_message.raw_event_id,
            event_id=normalized_message.event_id,
            tenant_id=normalized_message.tenant_id,
            rule_id=match.rule_id,
            rule_name=match.rule_name,
            severity=match.severity,
            title=match.title,
            summary=match.summary,
            status="open",
            agent_id=normalized_message.agent_id,
            host_id=normalized_message.host_id,
            hostname=normalized_message.hostname,
            actor_user=normalized_message.actor_user,
        )
        session.add(alert)
        await session.flush()

        evidence = AlertEvidence(
            alert_id=alert.id,
            evidence_type="rule_match",
            evidence_payload=match.evidence,
        )
        session.add(evidence)

        observe_alert_created(
            rule_id=match.rule_id,
            severity=match.severity,
        )

        created_count += 1

        logger.info(
            "alert persisted",
            extra={
                "alert_id": alert.id,
                "rule_id": match.rule_id,
                "normalized_event_id": normalized_message.normalized_event_id,
                "severity": match.severity,
            },
        )

    await session.commit()

    return AlertPersistenceSummary(
        created_count=created_count,
        duplicate_count=duplicate_count,
    )