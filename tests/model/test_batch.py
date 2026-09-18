import pytest
from model.batch import Batch, BatchValidationError
from model.measurement import Measurement


def test_batch_requires_non_empty_identity_fields():
    with pytest.raises(BatchValidationError):
        Batch(
            batch_id="",
            logger_id="logger-001",
            sequence=1,
            created_at="2026-08-29T20:00:00+02:00",
        )

    with pytest.raises(BatchValidationError):
        Batch(
            batch_id="batch-001",
            logger_id="",
            sequence=1,
            created_at="2026-08-29T20:00:00+02:00",
        )


def test_batch_uses_schema_version_1_0():
    batch = Batch(
        batch_id="batch-001",
        logger_id="logger-001",
        sequence=1,
        created_at="2026-08-29T20:00:00+02:00",
    )

    assert batch.schema_version == "1.0"


def test_batch_requires_integer_sequence():
    with pytest.raises(BatchValidationError):
        Batch(
            batch_id="batch-001",
            logger_id="logger-001",
            sequence="1",
            created_at="2026-08-29T20:00:00+02:00",
        )


def test_batch_requires_timezone_aware_created_at():
    with pytest.raises(BatchValidationError):
        Batch(
            batch_id="batch-001",
            logger_id="logger-001",
            sequence=1,
            created_at="2026-08-29T20:00:00",
        )


def test_optional_batch_sections_are_omitted():
    batch = Batch(
        batch_id="batch-001",
        logger_id="logger-001",
        sequence=1,
        created_at="2026-08-29T20:00:00+02:00",
    )

    assert batch.to_dict() == {
        "schema_version": "1.0",
        "batch_id": "batch-001",
        "logger_id": "logger-001",
        "sequence": 1,
        "created_at": "2026-08-29T20:00:00+02:00",
    }


def test_batch_can_contain_measurements():
    measurement = Measurement(
        value=21.5,
        unit="celsius",
        measured_at="2026-08-29T20:00:00+02:00",
        validity="valid",
        source="test",
    )

    batch = Batch(
        batch_id="batch-001",
        logger_id="logger-001",
        sequence=1,
        created_at="2026-08-29T20:00:00+02:00",
        measurements={"temperature": measurement},
    )

    assert batch.to_dict()["measurements"] == {
        "temperature": {
            "value": 21.5,
            "unit": "celsius",
            "measured_at": "2026-08-29T20:00:00+02:00",
            "validity": "valid",
            "source": "test",
        }
    }


def test_measurement_contains_required_fields():
    measurement = Measurement(
        value=21.5,
        unit="celsius",
        measured_at="2026-08-29T20:00:00+02:00",
        validity="valid",
        source="test",
    )

    assert measurement.to_dict() == {
        "value": 21.5,
        "unit": "celsius",
        "measured_at": "2026-08-29T20:00:00+02:00",
        "validity": "valid",
        "source": "test",
    }


def test_valid_measurement_requires_value():
    with pytest.raises(BatchValidationError):
        Measurement(
            value=None,
            unit="celsius",
            measured_at="2026-08-29T20:00:00+02:00",
            validity="valid",
            source="test",
        )


def test_unavailable_measurement_requires_null_value():
    with pytest.raises(BatchValidationError):
        Measurement(
            value=21.5,
            unit="celsius",
            measured_at="2026-08-29T20:00:00+02:00",
            validity="unavailable",
            source="test",
        )


def test_stale_measurement_requires_value():
    with pytest.raises(BatchValidationError):
        Measurement(
            value=None,
            unit="celsius",
            measured_at="2026-08-29T20:00:00+02:00",
            validity="stale",
            source="test",
        )


def test_batch_serializes_system_and_memory() -> None:
    batch = Batch(
        batch_id="batch-001",
        logger_id="logger-001",
        sequence=0,
        created_at="2026-08-30T12:00:00+00:00",
        system={
            "time": {
                "current": "2026-08-30T12:00:00+00:00",
                "timezone": "CEST",
                "clock_state": "unknown",
            },
            "boot": {
                "last_boot_at": "2026-08-30T10:00:00+00:00",
                "uptime_seconds": 7200,
            },
            "cpu": {
                "usage_percent": 15.0,
                "load": {
                    "1m": 0.42,
                    "5m": 0.35,
                    "15m": 0.28,
                },
            },
        },
        memory={
            "total_bytes": 104857600,
            "available_bytes": 26214400,
            "used_bytes": 78643200,
        },
    )

    result = batch.to_dict()

    assert result["system"]["time"]["timezone"] == "CEST"
    assert result["system"]["boot"]["uptime_seconds"] == 7200
    assert result["system"]["cpu"]["usage_percent"] == 15.0
    assert result["system"]["cpu"]["load"]["1m"] == 0.42
    assert result["memory"]["total_bytes"] == 104857600
