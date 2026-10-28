"""Archiviert alte Batches aus der SQLite-Datenbank als JSON Lines + gzip.

Exportiert Batches älter als 12 Monate (Standard) in eine komprimierte
JSON-Lines-Datei. Nach erfolgreichem Export werden die Batches aus der
Live-Datenbank gelöscht.

Verwendung:
    # Normaler Lauf (Batches > 12 Monate)
    python3 archive_batches.py

    # Force-Modus (alle Batches, z.B. für Test)
    python3 archive_batches.py --force

    # Mit Ausgabepfad (für Tests) - löscht NICHT die DB
    python3 archive_batches.py --output /tmp/test.json.gz --force

    # Mit Datumsbereich
    python3 archive_batches.py --year 2025 --month 10

    # Dry-Run (zeigt nur an, was passieren würde)
    python3 archive_batches.py --dry-run
"""

import argparse
import gzip
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)

# Standard-Pfade
DEFAULT_DATABASE = "/var/lib/loggerpi-otterpi/batches.sqlite3"
DEFAULT_ARCHIVE_DIR = "/var/lib/loggerpi-otterpi/archive"

# Standard-Retention: 12 Monate
RETENTION_DAYS = 365

# Batch-Größe für effizientes Verarbeiten
BATCH_SIZE = 1000


def _parse_args() -> argparse.Namespace:
    """Parst die Kommandozeilen-Argumente."""
    parser = argparse.ArgumentParser(
        description="Archive old batches from SQLite to JSON Lines + gzip."
    )
    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE,
        help=f"SQLite database path (default: {DEFAULT_DATABASE})",
    )
    parser.add_argument(
        "--archive-dir",
        default=DEFAULT_ARCHIVE_DIR,
        help=f"Archive directory (default: {DEFAULT_ARCHIVE_DIR})",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Specific output file path (for tests). If set, database is NOT deleted.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Archive all batches regardless of age (for tests).",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Archive only batches from this year (e.g. 2025).",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=None,
        help="Archive only batches from this month (1-12). Requires --year.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be archived without actually doing it.",
    )
    parser.add_argument(
        "--no-delete",
        action="store_true",
        help="Do not delete batches from database after successful export.",
    )
    return parser.parse_args()


def _connect_database(db_path: str) -> sqlite3.Connection:
    """Öffnet die SQLite-Datenbank."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _get_cutoff_date(force: bool) -> str:
    """Berechnet das Cutoff-Datum für den Batch-Export."""
    if force:
        # Alles archivieren (für Tests)
        return "1970-01-01T00:00:00"

    # Batches älter als 12 Monate
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    return cutoff.strftime("%Y-%m-%dT%H:%M:%S")


def _get_batches_to_archive(
    conn: sqlite3.Connection,
    cutoff_date: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> list[tuple[str, str]]:
    """Findet Batches, die archiviert werden sollen.

    Gibt eine Liste von (batch_id, payload) zurück.
    Filtert in Python, da `created_at` im JSON-Payload gespeichert ist.
    """
    # Monat validieren
    if month is not None and (month < 1 or month > 12):
        raise ValueError(f"Month must be 1-12, got {month}")

    rows = conn.execute("SELECT batch_id, payload FROM batches").fetchall()

    # Force-Modus erkennen (cutoff = 1970)
    force_mode = cutoff_date == "1970-01-01T00:00:00"

    result = []
    cutoff_naive = datetime.strptime(cutoff_date, "%Y-%m-%dT%H:%M:%S")

    for batch_id, payload in rows:
        try:
            data = json.loads(payload)
            created_at = data.get("created_at", "")

            if not created_at:
                continue

            # created_at kann Zeitzonen-Suffix haben (z.B. +00:00)
            created_str = created_at[:19]  # YYYY-MM-DDTHH:MM:SS
            created_dt = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%S")

            # Jahr/Monat-Filter
            if year is not None:
                if created_dt.year != year:
                    continue

                if month is not None and created_dt.month != month:
                    continue

            # Cutoff-Filter (nur wenn kein Jahr/Monat angegeben)
            elif not force_mode and created_dt >= cutoff_naive:
                continue

            result.append((batch_id, payload))

        except (json.JSONDecodeError, ValueError):
            LOGGER.warning("Skipping invalid batch %s", batch_id)
            continue

    return result


def _archive_batches(
    conn: sqlite3.Connection,
    batches: list[tuple[str, str]],
    output_path: Path,
) -> int:
    """Schreibt Batches als JSON Lines + gzip in die Datei.

    Gibt die Anzahl der archivierten Batches zurück.
    """
    if not batches:
        LOGGER.info("No batches to archive.")
        return 0

    # Sicherstellen, dass das Verzeichnis existiert
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Nicht überschreiben
    if output_path.exists():
        LOGGER.error("Archive file already exists: %s", output_path)
        return 0

    count = 0
    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        for batch_id, payload in batches:
            try:
                # Payload ist bereits JSON-String → direkt schreiben
                f.write(payload)
                f.write("\n")
                count += 1
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                LOGGER.warning(
                    "Skipping batch %s: %s",
                    batch_id,
                    exc,
                )

    LOGGER.info("Archived %d batches to %s", count, output_path)
    return count


def _delete_batches(
    conn: sqlite3.Connection,
    batch_ids: list[str],
) -> int:
    """Löscht Batches aus der Datenbank.

    Gibt die Anzahl der gelöschten Batches zurück.
    """
    if not batch_ids:
        return 0

    deleted = 0
    with conn:
        for i in range(0, len(batch_ids), BATCH_SIZE):
            chunk = batch_ids[i : i + BATCH_SIZE]
            placeholders = ",".join("?" for _ in chunk)
            cursor = conn.execute(
                f"DELETE FROM batches WHERE batch_id IN ({placeholders})",
                chunk,
            )
            deleted += cursor.rowcount

    LOGGER.info("Deleted %d batches from database", deleted)
    return deleted


def _get_archive_filename(year: Optional[int], month: Optional[int]) -> str:
    """Erzeugt den Archiv-Dateinamen."""
    now = datetime.now(timezone.utc)

    if year is not None and month is not None:
        return f"loggerpi-otterpi_batches_{year:04d}-{month:02d}.json.gz"

    return f"loggerpi-otterpi_batches_{now.strftime('%Y-%m')}.json.gz"


def main() -> None:
    """Hauptfunktion für die Archivierung."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    args = _parse_args()

    # Parameter validieren
    if args.month is not None and args.year is None:
        LOGGER.error("--month requires --year to be set.")
        return

    # Verbindung zur Datenbank herstellen
    if not os.path.exists(args.database):
        LOGGER.error("Database not found: %s", args.database)
        return

    conn = _connect_database(args.database)

    try:
        # Cutoff-Datum bestimmen
        cutoff_date = _get_cutoff_date(args.force)

        # Batches finden
        batches = _get_batches_to_archive(
            conn,
            cutoff_date,
            year=args.year,
            month=args.month,
        )

        if not batches:
            LOGGER.info("No batches to archive.")
            return

        # Ausgabepfad bestimmen
        if args.output:
            output_path = Path(args.output)
        else:
            archive_dir = Path(args.archive_dir)
            archive_dir.mkdir(parents=True, exist_ok=True)
            filename = _get_archive_filename(args.year, args.month)
            output_path = archive_dir / filename

        # Dry-Run: Nur anzeigen
        if args.dry_run:
            LOGGER.info(
                "Dry run: Would archive %d batches to %s",
                len(batches),
                output_path,
            )
            return

        # Batches archivieren
        archived_count = _archive_batches(conn, batches, output_path)

        if archived_count == 0:
            LOGGER.info("Nothing was archived.")
            return

        # Löschen NUR wenn:
        # - Export erfolgreich war (archived_count > 0)
        # - NICHT im Output-Modus (für Tests)
        # - NICHT wenn --no-delete gesetzt ist
        if not args.output and not args.no_delete:
            batch_ids = [batch_id for batch_id, _ in batches]
            deleted_count = _delete_batches(conn, batch_ids)

            LOGGER.info(
                "Archived %d and deleted %d batches.",
                archived_count,
                deleted_count,
            )
        else:
            LOGGER.info(
                "Archived %d batches. Database NOT deleted (--output or --no-delete).",
                archived_count,
            )

    finally:
        conn.close()


if __name__ == "__main__":
    main()
