from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

from .model.batch import Batch
from .model.measurement import Measurement


class SequenceStore:
    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)

    def next(self) -> int:
        current = int(self.path.read_text()) if self.path.exists() else -1
        sequence = current + 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(str(sequence))
        return sequence


def create_batch(
    logger_id: str,
    sequence_store: SequenceStore,
    measurements: Optional[dict[str, Measurement]] = None,
    system: Optional[dict] = None,
    memory: Optional[dict] = None,
) -> Batch:
    return Batch(
        batch_id=str(uuid4()),
        logger_id=logger_id,
        sequence=sequence_store.next(),
        created_at=datetime.now(timezone.utc).isoformat(),
        measurements=measurements or {},
        system=system,
        memory=memory,
    )
