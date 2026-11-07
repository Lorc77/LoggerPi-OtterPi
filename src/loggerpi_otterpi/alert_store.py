"""SQLite-Speicher für Alerts."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

from notifier import Alert


class AlertStore:
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
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    sensor TEXT NOT NULL,
                    rule TEXT NOT NULL,
                    value REAL,
                    threshold REAL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    dedup_key TEXT NOT NULL,
                    acknowledged INTEGER NOT NULL DEFAULT 0,
                    acknowledged_at TEXT,
                    acknowledged_by TEXT
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_dedup_key ON alerts(dedup_key, created_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged)"
            )

    def store(self, alert: Alert) -> int:
        if alert.rule is None or alert.dedup_key is None:
            raise ValueError("Alert must have 'rule' and 'dedup_key' set.")
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO alerts (
                    created_at, sensor, rule, value, threshold,
                    severity, message, dedup_key
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    alert.sensor,
                    alert.rule,
                    alert.value,
                    alert.threshold,
                    alert.severity,
                    alert.message,
                    alert.dedup_key,
                ),
            )
            return cursor.lastrowid

    def recent_dedup_keys(self, dedup_key: str, since: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM alerts WHERE dedup_key = ? AND created_at >= ? LIMIT 1",
                (dedup_key, since),
            ).fetchone()
        return row is not None

    def list_alerts(
        self,
        limit: int = 100,
        only_unacknowledged: bool = False,
    ) -> list:
        query = "SELECT * FROM alerts"
        params: list = []
        if only_unacknowledged:
            query += " WHERE acknowledged = 0"
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def acknowledge(self, alert_id: int, by: str) -> bool:
        acknowledged_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE alerts
                SET acknowledged = 1, acknowledged_at = ?, acknowledged_by = ?
                WHERE id = ? AND acknowledged = 0
                """,
                (acknowledged_at, by, alert_id),
            )
            return cursor.rowcount > 0
