from dataclasses import dataclass, field
from datetime import datetime

from .measurement import BatchValidationError, Measurement


@dataclass(frozen=True)
class Batch:
    batch_id: str
    logger_id: str
    sequence: int
    created_at: str
    schema_version: str = "1.0"
    measurements: dict[str, Measurement] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.batch_id:
            raise BatchValidationError("batch_id darf nicht leer sein.")

        if not self.logger_id:
            raise BatchValidationError("logger_id darf nicht leer sein.")

        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool):
            raise BatchValidationError("sequence muss eine Ganzzahl sein.")

        if self.sequence < 0:
            raise BatchValidationError("sequence darf nicht negativ sein.")

        if self.schema_version != "1.0":
            raise BatchValidationError("schema_version muss für Core Batch v1 exakt '1.0' sein.")

        timestamp = datetime.fromisoformat(self.created_at)
        if timestamp.tzinfo is None:
            raise BatchValidationError("created_at muss eine Zeitzoneninformation enthalten.")

    def to_dict(self) -> dict:
        result = {
            "schema_version": self.schema_version,
            "batch_id": self.batch_id,
            "logger_id": self.logger_id,
            "sequence": self.sequence,
            "created_at": self.created_at,
        }

        if self.measurements:
            result["measurements"] = {
                name: measurement.to_dict() for name, measurement in self.measurements.items()
            }

        return result
