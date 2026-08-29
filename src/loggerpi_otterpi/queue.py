import json
from pathlib import Path

from .model.batch import Batch
from .model.measurement import Measurement


class BatchQueue:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def enqueue(self, batch: Batch) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("a", encoding="utf-8") as file:
            json.dump(batch.to_dict(), file, ensure_ascii=False)
            file.write("\n")

    def pending(self) -> list[Batch]:
        if not self.path.exists():
            return []

        batches = []

        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                data = json.loads(line)

                measurements = {
                    name: Measurement(**measurement)
                    for name, measurement in data.pop("measurements", {}).items()
                }

                batches.append(
                    Batch(
                        **data,
                        measurements=measurements,
                    )
                )

        return batches
