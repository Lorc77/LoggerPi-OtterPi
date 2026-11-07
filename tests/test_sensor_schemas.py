"""Tests für die zentrale Sensor-Schema-Definition."""

from memmert import ALL_MEASUREMENT_COMMANDS
from sensor_schemas import (
    SENSOR_SCHEMAS,
    get_measurement_names,
    get_schema,
    get_state_names,
)


class TestSchemaStructure:
    """Prüft die Grundstruktur der Schema-Definition."""

    def test_all_schemas_have_measurements_and_states(self):
        for device_type, schema in SENSOR_SCHEMAS.items():
            assert "measurements" in schema, f"{device_type} fehlt 'measurements'"
            assert "states" in schema, f"{device_type} fehlt 'states'"
            assert isinstance(schema["measurements"], list)
            assert isinstance(schema["states"], list)

    def test_measurement_entries_are_tuples(self):
        for device_type, schema in SENSOR_SCHEMAS.items():
            for entry in schema["measurements"]:
                assert isinstance(entry, tuple), f"{device_type}: {entry!r} ist kein Tuple"
                assert len(entry) == 2, f"{device_type}: {entry!r} hat nicht 2 Elemente"
                name, unit = entry
                assert isinstance(name, str) and name
                assert isinstance(unit, str) and unit

    def test_state_entries_are_tuples(self):
        for device_type, schema in SENSOR_SCHEMAS.items():
            for entry in schema["states"]:
                assert isinstance(entry, tuple), f"{device_type}: {entry!r} ist kein Tuple"
                assert len(entry) == 2, f"{device_type}: {entry!r} hat nicht 2 Elemente"
                name, state_type = entry
                assert isinstance(name, str) and name
                assert isinstance(state_type, str) and state_type


class TestGetSchema:
    """Prüft die get_schema-Funktion."""

    def test_known_type(self):
        schema = get_schema("atmoweb")
        assert "temperature_1" in [name for name, _ in schema["measurements"]]

    def test_unknown_type_returns_empty(self):
        schema = get_schema("unknown_type")
        assert schema == {"measurements": [], "states": []}


class TestGetMeasurementNames:
    """Prüft die get_measurement_names-Funktion."""

    def test_atmoweb(self):
        names = get_measurement_names("atmoweb")
        assert "temperature_1" in names
        assert "humidity" in names
        assert "vacuum" in names

    def test_freezer(self):
        assert get_measurement_names("freezer") == ["temperature"]

    def test_unknown(self):
        assert get_measurement_names("unknown") == []


class TestGetStateNames:
    """Prüft die get_state_names-Funktion."""

    def test_atmoweb(self):
        names = get_state_names("atmoweb")
        assert "door_open" in names
        assert "lights.led" in names

    def test_freezer(self):
        assert get_state_names("freezer") == ["alarms"]

    def test_unknown(self):
        assert get_state_names("unknown") == []


class TestConsistencyWithReaderCode:
    """Prüft, dass die Schema-Definition mit dem Reader-Code übereinstimmt."""

    def test_memmert_measurements_match_reader(self):
        """Die MEMMERT-Schema-Messwerte müssen mit ALL_MEASUREMENT_COMMANDS übereinstimmen."""
        reader_names = {name for _, name, _ in ALL_MEASUREMENT_COMMANDS}
        schema_names = set(get_measurement_names("memmert"))
        # Schema enthält nur die für IPP300 relevanten Messwerte,
        # ALL_MEASUREMENT_COMMANDS enthält alle möglichen.
        # Deshalb prüfen wir nur, dass die Schema-Namen eine Teilmenge sind.
        assert schema_names <= reader_names, (
            f"Schema-Namen {schema_names - reader_names} sind nicht im Reader-Code"
        )

    def test_weatherhub_types_are_known(self):
        """Alle WeatherHub-Sensor-Typen aus dem Decoder müssen im Schema sein."""
        from weatherhub_gateway_decoder import SUPPORTED_SENSOR_TYPES

        for sensor_type, info in SUPPORTED_SENSOR_TYPES.items():
            name = info["name"].lower()  # z.B. "id01"
            device_type = f"weatherhub_{name}"
            assert device_type in SENSOR_SCHEMAS, (
                f"Sensor-Typ {info['name']} (0x{sensor_type:02X}) fehlt im Schema"
            )
