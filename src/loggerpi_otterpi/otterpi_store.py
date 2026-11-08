import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Union

from model.batch import Batch
from model.measurement import Measurement


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
                    received_at TEXT,
                    UNIQUE(logger_id, sequence)
                )
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(batches)")}
            if "received_at" not in columns:
                connection.execute("ALTER TABLE batches ADD COLUMN received_at TEXT")

    def store(self, batch: Batch) -> str:
        payload = json.dumps(
            batch.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )
        received_at = datetime.now(timezone.utc).isoformat()

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
                    payload,
                    received_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    batch.batch_id,
                    batch.logger_id,
                    batch.sequence,
                    payload,
                    received_at,
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

    def latest(self) -> Optional[Batch]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM batches ORDER BY rowid DESC LIMIT 1"
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

    def latest_received_at(self) -> Optional[str]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT received_at, payload FROM batches ORDER BY rowid DESC LIMIT 1"
            ).fetchone()

        if row is None:
            return None

        received_at, payload = row
        if received_at:
            return received_at

        # Fallback für bestehende Zeilen ohne received_at
        data = json.loads(payload)
        return data.get("created_at")

    def recent(self, hours: int = 24) -> list:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM batches ORDER BY rowid DESC LIMIT 1000"
            ).fetchall()
        batches = []
        for (payload,) in rows:
            data = json.loads(payload)
            if data.get("created_at", "") >= cutoff:
                measurements = {
                    name: Measurement(**measurement)
                    for name, measurement in data.pop("measurements", {}).items()
                }
                batches.append(Batch(**data, measurements=measurements))
        batches.reverse()
        return batches
