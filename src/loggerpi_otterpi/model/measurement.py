from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class BatchValidationError(ValueError):
    """Fehler bei der Validierung eines Core-Batch-Datenobjekts."""


@dataclass(frozen=True)
class Measurement:
    value: object
    unit: str
    measured_at: Optional[str]
    validity: str
    source: str
    validity_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.validity == "valid" and self.value is None:
            raise BatchValidationError("Ein gültiges Measurement muss einen Wert enthalten.")

        if self.validity in {"invalid", "unavailable", "unknown"} and self.value is not None:
            raise BatchValidationError(
                f"Ein Measurement mit validity={self.validity!r} darf keinen Wert enthalten."
            )

        if self.validity == "stale" and self.value is None:
            raise BatchValidationError("Ein veraltetes Measurement muss einen Wert enthalten.")

        if self.validity not in {
            "valid",
            "invalid",
            "unavailable",
            "unknown",
            "stale",
        }:
            raise BatchValidationError(f"Unbekannter validity-Wert: {self.validity!r}")

        if self.measured_at is not None:
            timestamp = datetime.fromisoformat(self.measured_at)
            if timestamp.tzinfo is None:
                raise BatchValidationError("measured_at muss eine Zeitzoneninformation enthalten.")

        if self.validity_reason is not None and not isinstance(self.validity_reason, str):
            raise BatchValidationError("validity_reason muss ein String oder None sein.")

    def to_dict(self) -> dict:
        result = {
            "value": self.value,
            "unit": self.unit,
            "measured_at": self.measured_at,
            "validity": self.validity,
            "source": self.source,
        }
        if self.validity_reason is not None:
            result["validity_reason"] = self.validity_reason
        return result
