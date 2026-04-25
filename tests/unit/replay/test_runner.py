from datetime import datetime, timezone
from uuid import UUID

from sentinelforge.replay.runner import _build_report, _prepare_events
from sentinelforge.schemas.events import TelemetryEvent
from sentinelforge.schemas.replay import ReplayDataset


def test_prepare_events_rewrites_ids_when_not_preserving():
    """
    Replay normal deve gerar novos UUIDs para não cair em duplicidade.
    """
    dataset = ReplayDataset(
        dataset_name="sample",
        description="dataset de teste",
        expected_rule_ids=["PROC-PS-ENC-001"],
        notes=None,
        events=[
            TelemetryEvent.model_validate(
                {
                    "schema_version": "1.0",
                    "event_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "tenant_id": "lab-acme",
                    "category": "process",
                    "occurred_at": "2026-04-25T12:10:00Z",
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
                }
            )
        ],
    )

    prepared = _prepare_events(
        dataset=dataset,
        preserve_event_ids=False,
    )

    assert len(prepared) == 1
    assert isinstance(prepared[0].event_id, UUID)
    assert str(prepared[0].event_id) != "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_build_report_marks_false_negative_when_expected_rule_missing():
    """
    Se esperávamos uma regra e nenhuma apareceu, isso deve sair como falso negativo.
    """
    dataset = ReplayDataset(
        dataset_name="sample",
        description="dataset de teste",
        expected_rule_ids=["PROC-PS-ENC-001"],
        notes=None,
        events=[
            TelemetryEvent.model_validate(
                {
                    "schema_version": "1.0",
                    "event_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                    "tenant_id": "lab-acme",
                    "category": "process",
                    "occurred_at": "2026-04-25T12:11:00Z",
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
                }
            )
        ],
    )

    report = _build_report(
        dataset=dataset,
        events=dataset.events,
        send_results=[
            {
                "event_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "http_status": 202,
                "response": {"status": "accepted", "decision": "accepted"},
                "dataset_name": "sample",
            }
        ],
        observed_alerts=[],
        started_at=datetime.now(timezone.utc),
    )

    assert report["passed"] is False
    assert report["false_negative_rule_ids"] == ["PROC-PS-ENC-001"]
    assert report["false_positive_rule_ids"] == []