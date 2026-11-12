"""SQLite-Speicher für Alerts."""

import sqlite3
from datetime import datetime, timedelta, timezone
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
                    acknowledged_by TEXT,
                    resolved_at TEXT
                )
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(alerts)")}
            if "resolved_at" not in columns:
                connection.execute("ALTER TABLE alerts ADD COLUMN resolved_at TEXT")
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

    def is_acknowledged(self, dedup_key: str) -> bool:
        """True, wenn der letzte aktive Alert mit diesem dedup_key acknowledged ist."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT acknowledged FROM alerts WHERE dedup_key = ? "
                "AND resolved_at IS NULL ORDER BY id DESC LIMIT 1",
                (dedup_key,),
            ).fetchone()
        if row is None:
            return False
        return bool(row[0])

    def reset_acknowledged(self, dedup_key: str) -> None:
        """Setzt acknowledged=0 für alle Alerts mit diesem dedup_key."""
        with self._connect() as connection:
            connection.execute(
                "UPDATE alerts SET acknowledged = 0, acknowledged_at = NULL, "
                "acknowledged_by = NULL WHERE dedup_key = ? AND acknowledged = 1",
                (dedup_key,),
            )

    def resolve(self, dedup_key: str) -> None:
        """Setzt resolved_at für alle offenen Alerts mit diesem dedup_key."""
        resolved_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                "UPDATE alerts SET resolved_at = ? WHERE dedup_key = ? AND resolved_at IS NULL",
                (resolved_at, dedup_key),
            )

    def resolve_by_id(self, alert_id: int) -> bool:
        """Setzt resolved_at für einen bestimmten Alert (per ID)."""
        resolved_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE alerts SET resolved_at = ? WHERE id = ? AND resolved_at IS NULL",
                (resolved_at, alert_id),
            )
            return cursor.rowcount > 0

    def is_active(self, dedup_key: str) -> bool:
        """True, wenn der letzte Alert mit diesem dedup_key noch nicht resolved ist."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT resolved_at FROM alerts WHERE dedup_key = ? ORDER BY id DESC LIMIT 1",
                (dedup_key,),
            ).fetchone()
        if row is None:
            return False
        return row[0] is None

    def list_alerts(
        self,
        limit: int = 100,
        only_unacknowledged: bool = False,
        only_active: bool = False,
    ) -> list:
        query = "SELECT * FROM alerts"
        conditions = []
        params: list = []
        if only_unacknowledged:
            conditions.append("acknowledged = 0")
        if only_active:
            conditions.append("resolved_at IS NULL")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def count_by_day(self, days: int = 14) -> list[dict]:
        """Aggregiert die Alerts pro Tag (warning, critical, resolved)."""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    DATE(created_at) AS day,
                    SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END) AS warning,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical,
                    SUM(CASE WHEN resolved_at IS NOT NULL THEN 1 ELSE 0 END) AS resolved
                FROM alerts
                WHERE created_at >= ?
                GROUP BY day
                ORDER BY day
                """,
                (since,),
            ).fetchall()
        return [
            {
                "date": row[0],
                "warning": row[1],
                "critical": row[2],
                "resolved": row[3],
            }
            for row in rows
        ]

    def count_by_status(self) -> dict:
        """Zählt die Alerts nach Status (active critical, active warning, resolved)."""
        with self._connect() as connection:
            active_rows = connection.execute(
                "SELECT severity, COUNT(*) FROM alerts WHERE resolved_at IS NULL GROUP BY severity"
            ).fetchall()
            resolved_row = connection.execute(
                "SELECT COUNT(*) FROM alerts WHERE resolved_at IS NOT NULL"
            ).fetchone()
        result = {"active_critical": 0, "active_warning": 0, "resolved": 0}
        for severity, count in active_rows:
            if severity == "critical":
                result["active_critical"] = count
            elif severity == "warning":
                result["active_warning"] = count
        result["resolved"] = resolved_row[0] if resolved_row else 0
        return result

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
