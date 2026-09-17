import json
import sqlite3
from pathlib import Path
from typing import Optional, Union

from .model.batch import Batch
from .model.measurement import Measurement


class BatchStore:
    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id TEXT PRIMARY KEY,
                    logger_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    UNIQUE(logger_id, sequence)
                )
                """
            )

    def store(self, batch: Batch) -> str:
        payload = json.dumps(
            batch.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )

        with self._connect() as connection:
            existing = connection.execute(
                "SELECT payload FROM batches WHERE batch_id = ?",
                (batch.batch_id,),
            ).fetchone()

            if existing is not None:
                if existing[0] == payload:
                    return "duplicate"
                return "conflict"

            existing = connection.execute(
                """
                SELECT payload FROM batches
                WHERE logger_id = ? AND sequence = ?
                """,
                (batch.logger_id, batch.sequence),
            ).fetchone()

            if existing is not None:
                return "conflict"

            connection.execute(
                """
                INSERT INTO batches (
                    batch_id,
                    logger_id,
                    sequence,
                    payload
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    batch.batch_id,
                    batch.logger_id,
                    batch.sequence,
                    payload,
                ),
            )

        return "stored"

    def get(self, batch_id: str) -> Optional[Batch]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM batches WHERE batch_id = ?",
                (batch_id,),
            ).fetchone()

        if row is None:
            return None

        data = json.loads(row[0])

        measurements = {
            name: Measurement(**measurement)
            for name, measurement in data.pop("measurements", {}).items()
        }

        return Batch(
            **data,
            measurements=measurements,
        )
