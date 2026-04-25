from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from sentinelforge.schemas.events import TelemetryEvent


class ReplayDataset(BaseModel):
    """
    Estrutura declarativa de um dataset de replay.

    Um dataset diz:
    - quem ele é
    - o que ele representa
    - quais regras esperamos ver no final
    - quais eventos devem ser enviados
    """
    model_config = ConfigDict(extra="forbid")

    dataset_name: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=1024)
    expected_rule_ids: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=2048)
    events: list[TelemetryEvent] = Field(min_length=1)


def load_replay_dataset(path: str | Path) -> ReplayDataset:
    """
    Carrega e valida um dataset JSON do disco.

    Isso garante que o replay não rode com arquivo malformado
    ou com contrato de evento quebrado.
    """
    dataset_path = Path(path)

    raw_text = dataset_path.read_text(encoding="utf-8")
    return ReplayDataset.model_validate_json(raw_text)