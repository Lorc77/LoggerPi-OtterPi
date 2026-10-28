"""Tests für die Batch-Archivierung."""

import gzip
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from archive_batches import (
    _archive_batches,
    _connect_database,
    _delete_batches,
    _get_archive_filename,
    _get_batches_to_archive,
    _get_cutoff_date,
    main,
)


def _create_test_database(
    db_path: Path,
    num_batches: int = 5,
    days_old: int = 0,
    start_sequence: int = 0,
) -> None:
    """Erstellt eine Test-Datenbank mit Batches."""
    conn = _connect_database(str(db_path))
    try:
        with conn:
            conn.execute(
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

            for i in range(num_batches):
                created_at = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
                sequence = start_sequence + i
                batch_id = f"batch-{sequence:03d}"
                payload = json.dumps(
                    {
                        "schema_version": "1.0",
                        "batch_id": batch_id,
                        "logger_id": "loggerpi-001",
                        "sequence": sequence,
                        "created_at": created_at,
                        "measurements": {
                            "temperature": {
                                "value": 20.0 + i,
                                "unit": "celsius",
                                "measured_at": created_at,
                                "validity": "valid",
                                "source": "test",
                            }
                        },
                    }
                )

                conn.execute(
                    """
                    INSERT INTO batches (batch_id, logger_id, sequence, payload)
                    VALUES (?, ?, ?, ?)
                    """,
                    (batch_id, "loggerpi-001", sequence, payload),
                )
    finally:
        conn.close()


def _count_batches(db_path: Path) -> int:
    """Zählt die Batches in der Datenbank."""
    conn = _connect_database(str(db_path))
    try:
        return conn.execute("SELECT COUNT(*) FROM batches").fetchone()[0]
    finally:
        conn.close()


def _read_archive_file(file_path: Path) -> list[dict]:
    """Liest eine Archiv-Datei und gibt die Batches als Liste zurück."""
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines if line.strip()]


class TestGetCutoffDate:
    """Testet die Cutoff-Datum-Berechnung."""

    def test_force_returns_epoch(self):
        """Force-Modus: Alles archivieren."""
        assert _get_cutoff_date(force=True) == "1970-01-01T00:00:00"

    def test_normal_returns_12_months_back(self):
        """Normaler Modus: 12 Monate zurück."""
        cutoff = _get_cutoff_date(force=False)
        cutoff_dt = datetime.strptime(cutoff, "%Y-%m-%dT%H:%M:%S")

        expected = datetime.now(timezone.utc) - timedelta(days=365)

        # Nur Datum vergleichen (Zeit kann minimal abweichen)
        assert cutoff_dt.date() == expected.date()


class TestGetBatchesToArchive:
    """Testet die Batch-Auswahl."""

    def test_force_returns_all_batches(self, tmp_path):
        """Force-Modus: Alle Batches werden ausgewählt."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=5)

        conn = _connect_database(str(db_path))
        try:
            cutoff = _get_cutoff_date(force=True)
            batches = _get_batches_to_archive(conn, cutoff)

            assert len(batches) == 5
        finally:
            conn.close()

    def test_cutoff_filters_old_batches(self, tmp_path):
        """Batches älter als Cutoff werden ausgewählt."""
        db_path = tmp_path / "test.db"
        # 3 alte Batches (400 Tage) + 2 neue (0 Tage)
        _create_test_database(db_path, num_batches=3, days_old=400, start_sequence=0)
        _create_test_database(db_path, num_batches=2, days_old=0, start_sequence=3)

        conn = _connect_database(str(db_path))
        try:
            cutoff = _get_cutoff_date(force=False)
            batches = _get_batches_to_archive(conn, cutoff)

            assert len(batches) == 3  # Nur die alten
        finally:
            conn.close()

    def test_year_month_filter(self, tmp_path):
        """Filter nach Jahr und Monat."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=3)

        conn = _connect_database(str(db_path))
        try:
            now = datetime.now(timezone.utc)
            batches = _get_batches_to_archive(
                conn,
                "1970-01-01T00:00:00",
                year=now.year,
                month=now.month,
            )

            assert len(batches) == 3
        finally:
            conn.close()

    def test_invalid_month_raises(self, tmp_path):
        """Ungültiger Monat wirft ValueError."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path)

        conn = _connect_database(str(db_path))
        try:
            try:
                _get_batches_to_archive(
                    conn,
                    "1970-01-01T00:00:00",
                    year=2025,
                    month=13,
                )
                assert False, "Should have raised ValueError"
            except ValueError as exc:
                assert "Month must be 1-12" in str(exc)
        finally:
            conn.close()


class TestArchiveBatches:
    """Testet das Schreiben der Archiv-Datei."""

    def test_archive_creates_gzip_file(self, tmp_path):
        """Archiv-Datei wird als gzip erstellt."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=3)

        conn = _connect_database(str(db_path))
        try:
            cutoff = _get_cutoff_date(force=True)
            batches = _get_batches_to_archive(conn, cutoff)

            output_path = tmp_path / "archive.json.gz"
            count = _archive_batches(conn, batches, output_path)

            assert count == 3
            assert output_path.exists()

            # Datei lesen
            archived = _read_archive_file(output_path)
            assert len(archived) == 3
            assert archived[0]["batch_id"] == "batch-000"
        finally:
            conn.close()

    def test_archive_does_not_overwrite_existing(self, tmp_path):
        """Bestehende Archiv-Datei wird nicht überschrieben."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=3)

        output_path = tmp_path / "archive.json.gz"
        output_path.write_text("existing content", encoding="utf-8")

        conn = _connect_database(str(db_path))
        try:
            cutoff = _get_cutoff_date(force=True)
            batches = _get_batches_to_archive(conn, cutoff)

            count = _archive_batches(conn, batches, output_path)

            assert count == 0
            assert output_path.read_text(encoding="utf-8") == "existing content"
        finally:
            conn.close()

    def test_archive_empty_batches(self, tmp_path):
        """Keine Batches → keine Datei."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=0)

        conn = _connect_database(str(db_path))
        try:
            cutoff = _get_cutoff_date(force=True)
            batches = _get_batches_to_archive(conn, cutoff)

            output_path = tmp_path / "archive.json.gz"
            count = _archive_batches(conn, batches, output_path)

            assert count == 0
            assert not output_path.exists()
        finally:
            conn.close()


class TestDeleteBatches:
    """Testet das Löschen von Batches."""

    def test_delete_specific_batches(self, tmp_path):
        """Gezielte Batches werden gelöscht."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=5)

        conn = _connect_database(str(db_path))
        try:
            deleted = _delete_batches(conn, ["batch-000", "batch-001"])

            assert deleted == 2
            assert _count_batches(db_path) == 3
        finally:
            conn.close()

    def test_delete_nonexistent_batches(self, tmp_path):
        """Nicht existierende Batches → 0 gelöscht."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=3)

        conn = _connect_database(str(db_path))
        try:
            deleted = _delete_batches(conn, ["nonexistent"])

            assert deleted == 0
            assert _count_batches(db_path) == 3
        finally:
            conn.close()


class TestGetArchiveFilename:
    """Testet die Dateinamen-Erzeugung."""

    def test_with_year_month(self):
        """Mit Jahr und Monat."""
        filename = _get_archive_filename(2025, 10)
        assert filename == "loggerpi-otterpi_batches_2025-10.json.gz"

    def test_without_year_month(self):
        """Ohne Jahr und Monat (aktuelles Datum)."""
        now = datetime.now(timezone.utc)
        filename = _get_archive_filename(None, None)
        assert filename == f"loggerpi-otterpi_batches_{now.strftime('%Y-%m')}.json.gz"


class TestMain:
    """Testet die main()-Funktion."""

    def test_main_archives_and_deletes(self, tmp_path, monkeypatch):
        """Normaler Lauf: Archiviert und löscht."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=5, days_old=400)

        archive_dir = tmp_path / "archive"
        output_path = archive_dir / "loggerpi-otterpi_batches_TEST.json.gz"

        monkeypatch.setattr(
            "archive_batches.DEFAULT_DATABASE",
            str(db_path),
        )
        monkeypatch.setattr(
            "archive_batches.DEFAULT_ARCHIVE_DIR",
            str(archive_dir),
        )
        monkeypatch.setattr(
            "sys.argv",
            [
                "archive_batches.py",
                "--force",
                "--output",
                str(output_path),
                "--no-delete",
            ],
        )

        main()

        # Datei existiert
        assert output_path.exists()

        # DB wurde NICHT gelöscht (--no-delete)
        assert _count_batches(db_path) == 5

    def test_main_without_output_deletes(self, tmp_path, monkeypatch):
        """Ohne --output wird gelöscht."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=5, days_old=400)

        archive_dir = tmp_path / "archive"

        monkeypatch.setattr(
            "archive_batches.DEFAULT_DATABASE",
            str(db_path),
        )
        monkeypatch.setattr(
            "archive_batches.DEFAULT_ARCHIVE_DIR",
            str(archive_dir),
        )
        monkeypatch.setattr(
            "sys.argv",
            [
                "archive_batches.py",
                "--force",
            ],
        )

        main()

        # Datei existiert
        files = list(archive_dir.glob("*.json.gz"))
        assert len(files) == 1

        # DB wurde gelöscht
        assert _count_batches(db_path) == 0

    def test_main_dry_run_no_changes(self, tmp_path, monkeypatch):
        """Dry-Run: Keine Datei, keine Löschung."""
        db_path = tmp_path / "test.db"
        _create_test_database(db_path, num_batches=5, days_old=400)

        archive_dir = tmp_path / "archive"

        monkeypatch.setattr(
            "archive_batches.DEFAULT_DATABASE",
            str(db_path),
        )
        monkeypatch.setattr(
            "archive_batches.DEFAULT_ARCHIVE_DIR",
            str(archive_dir),
        )
        monkeypatch.setattr(
            "sys.argv",
            [
                "archive_batches.py",
                "--force",
                "--dry-run",
            ],
        )

        main()

        # Keine Datei erstellt
        assert not list(archive_dir.glob("*.json.gz"))

        # DB unverändert
        assert _count_batches(db_path) == 5

    def test_main_database_not_found(self, tmp_path, monkeypatch):
        """Datenbank nicht gefunden."""
        monkeypatch.setattr(
            "sys.argv",
            [
                "archive_batches.py",
                "--database",
                str(tmp_path / "nonexistent.db"),
            ],
        )

        # Sollte keinen Fehler werfen, nur loggen
        main()
