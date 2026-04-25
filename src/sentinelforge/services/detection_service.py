from dataclasses import dataclass
from typing import Literal

from sentinelforge.schemas.events import EventCategory
from sentinelforge.schemas.normalized import NormalizedPublishedMessage


@dataclass(slots=True)
class DetectionMatch:
    rule_id: str
    rule_name: str
    severity: Literal["low", "medium", "high", "critical"]
    title: str
    summary: str
    evidence: dict


def evaluate_normalized_event(
    message: NormalizedPublishedMessage,
) -> list[DetectionMatch]:
    """
    Avalia um evento normalizado contra um conjunto inicial de regras.

    Nesta fase, as regras ainda são simples, mas já mostram:
    - separação entre evento e detecção
    - severidade
    - evidência estruturada
    """
    matches: list[DetectionMatch] = []

    if _matches_encoded_powershell(message):
        command_line = _extract_command_line(message)

        matches.append(
            DetectionMatch(
                rule_id="PROC-PS-ENC-001",
                rule_name="Encoded PowerShell Command",
                severity="high",
                title="Encoded PowerShell command execution detected",
                summary="PowerShell executed with encoded command indicators on host "
                f"{message.hostname}.",
                evidence={
                    "event_action": message.event_action,
                    "process_name": message.process_name,
                    "command_line": command_line,
                    "raw_event_id": message.raw_event_id,
                    "normalized_event_id": message.normalized_event_id,
                },
            )
        )
        return matches

    if _matches_powershell_execution(message):
        matches.append(
            DetectionMatch(
                rule_id="PROC-PS-001",
                rule_name="PowerShell Execution",
                severity="medium",
                title="PowerShell execution detected",
                summary=f"PowerShell process execution observed on host {message.hostname}.",
                evidence={
                    "event_action": message.event_action,
                    "process_name": message.process_name,
                    "process_pid": message.process_pid,
                    "raw_event_id": message.raw_event_id,
                    "normalized_event_id": message.normalized_event_id,
                },
            )
        )

    return matches


def _matches_powershell_execution(message: NormalizedPublishedMessage) -> bool:
    return (
        message.category == EventCategory.PROCESS
        and (message.process_name or "").lower() == "powershell.exe"
    )


def _matches_encoded_powershell(message: NormalizedPublishedMessage) -> bool:
    if not _matches_powershell_execution(message):
        return False

    command_line = (_extract_command_line(message) or "").lower()

    return (
        "-enc" in command_line
        or " -e " in command_line
        or "encodedcommand" in command_line
    )


def _extract_command_line(message: NormalizedPublishedMessage) -> str | None:
    payload = message.normalized_payload.get("payload", {})
    if not isinstance(payload, dict):
        return None

    value = payload.get("command_line") or payload.get("cmdline")
    if value is None:
        return None

    return str(value)