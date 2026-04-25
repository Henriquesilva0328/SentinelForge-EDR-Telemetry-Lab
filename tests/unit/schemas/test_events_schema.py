import pytest
from pydantic import ValidationError

from sentinelforge.schemas.events import TelemetryEvent


def test_payload_rejects_excessive_depth():
    """
    Payload com nesting além do limite deve falhar na validação.
    """
    with pytest.raises(ValidationError):
        TelemetryEvent.model_validate(
            {
                "schema_version": "1.0",
                "event_id": "33333333-3333-3333-3333-333333333333",
                "tenant_id": "lab-acme",
                "category": "process",
                "occurred_at": "2026-04-25T12:02:00Z",
                "agent": {
                    "agent_id": "agent-001",
                    "host_id": "host-001",
                    "hostname": "win-lab-01",
                    "platform": "windows",
                    "sensor_version": "0.1.0",
                },
                "payload": {
                    "a": {
                        "b": {
                            "c": {
                                "d": {
                                    "e": {
                                        "f": {
                                            "g": "deep demais"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
            }
        )


def test_occurred_at_requires_timezone():
    """
    Timestamp sem timezone explícito deve ser rejeitado.
    """
    with pytest.raises(ValidationError):
        TelemetryEvent.model_validate(
            {
                "schema_version": "1.0",
                "event_id": "44444444-4444-4444-4444-444444444444",
                "tenant_id": "lab-acme",
                "category": "process",
                "occurred_at": "2026-04-25T12:03:00",
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