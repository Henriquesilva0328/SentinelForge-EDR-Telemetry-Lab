from sentinelforge.schemas.normalized import NormalizedPublishedMessage
from sentinelforge.services.detection_service import evaluate_normalized_event


def test_encoded_powershell_generates_high_severity_match():
    """
    Deve disparar a regra forte de PowerShell codificado.
    """
    message = NormalizedPublishedMessage.model_validate(
        {
            "normalization_version": "1.0",
            "normalized_event_id": 10,
            "raw_event_id": 20,
            "event_id": "11111111-1111-1111-1111-111111111111",
            "tenant_id": "lab-acme",
            "category": "process",
            "event_action": "process_start",
            "occurred_at": "2026-04-25T12:00:00Z",
            "agent_id": "agent-001",
            "host_id": "host-001",
            "hostname": "win-lab-01",
            "platform": "windows",
            "sensor_version": "0.1.0",
            "actor_user": None,
            "correlation_key": None,
            "process_name": "powershell.exe",
            "process_pid": 1234,
            "file_path": None,
            "destination_ip": None,
            "destination_port": None,
            "auth_result": None,
            "normalized_payload": {
                "payload": {
                    "process_name": "powershell.exe",
                    "command_line": "powershell.exe -EncodedCommand SQBmACgAJABQAFMAVgBlAHIAcwBpAG8AbgBUAGEAYgBsAGUAKQA=",
                }
            },
        }
    )

    matches = evaluate_normalized_event(message)

    assert len(matches) == 1
    assert matches[0].rule_id == "PROC-PS-ENC-001"
    assert matches[0].severity == "high"


def test_benign_explorer_generates_no_match():
    """
    Evento benigno simples não deve gerar alerta.
    """
    message = NormalizedPublishedMessage.model_validate(
        {
            "normalization_version": "1.0",
            "normalized_event_id": 11,
            "raw_event_id": 21,
            "event_id": "22222222-2222-2222-2222-222222222222",
            "tenant_id": "lab-acme",
            "category": "process",
            "event_action": "process_start",
            "occurred_at": "2026-04-25T12:01:00Z",
            "agent_id": "agent-001",
            "host_id": "host-001",
            "hostname": "win-lab-01",
            "platform": "windows",
            "sensor_version": "0.1.0",
            "actor_user": None,
            "correlation_key": None,
            "process_name": "explorer.exe",
            "process_pid": 2222,
            "file_path": None,
            "destination_ip": None,
            "destination_port": None,
            "auth_result": None,
            "normalized_payload": {
                "payload": {
                    "process_name": "explorer.exe",
                    "command_line": "C:\\Windows\\explorer.exe",
                }
            },
        }
    )

    matches = evaluate_normalized_event(message)

    assert matches == []