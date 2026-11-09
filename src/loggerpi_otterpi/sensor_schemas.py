"""Zentrale Schema-Definition pro Sensor-/Gerätetyp.

Beschreibt, welche Measurements und States ein Sensor-Typ grundsätzlich
liefern kann. Wird von Admin (Limits/States-Anzeige) und Alert-Engine
(Regel-Prüfung) genutzt.

Enthält auch Sensor-Typen, die im Decoder vorbereitet, aber noch nicht
in rooms.json eingebunden sind (z.B. weatherhub_id02, id04, id07, id10).

Die Definition ist bewusst statisch (manuell gepflegt) und wird durch
test_sensor_schemas.py gegen den Reader-Code abgesichert.
"""

from typing import Dict, List, Tuple

# Typ-Aliase für Lesbarkeit
MeasurementSpec = Tuple[str, str]  # (name, unit)
StateSpec = Tuple[str, str]  # (name, type)

SENSOR_SCHEMAS: Dict[str, Dict[str, List]] = {
    "atmoweb": {
        "measurements": [
            ("temperature_1", "celsius"),
            ("temperature_2", "celsius"),
            ("temperature_3", "celsius"),
            ("temperature_4", "celsius"),
            ("humidity", "percent"),
            ("vacuum", "mbar"),
            ("co2", "ppm"),
            ("o2", "percent"),
            ("fan_speed", "rpm"),
        ],
        "states": [
            ("door_open", "bool"),
            ("door_locked", "bool"),
            ("defrost", "bool"),
            ("flap", "percent"),
            ("lights.day", "bool"),
            ("lights.uv", "bool"),
            ("lights.led", "percent"),
            ("switches.a", "bool"),
            ("switches.b", "bool"),
            ("switches.c", "bool"),
            ("switches.d", "bool"),
        ],
    },
    "freezer": {
        "measurements": [
            ("temperature", "celsius"),
        ],
        "states": [
            ("alarms", "list"),
        ],
    },
    "memmert": {
        "measurements": [
            ("temperature", "celsius"),
        ],
        "states": [],
    },
    "weatherhub_id01": {
        "measurements": [
            ("temperature_1", "celsius"),
            ("temperature_2", "celsius"),
        ],
        "states": [
            ("battery_low", "bool"),
        ],
    },
    "weatherhub_id02": {
        "measurements": [
            ("temperature", "celsius"),
        ],
        "states": [
            ("battery_low", "bool"),
        ],
    },
    "weatherhub_id03": {
        "measurements": [
            ("temperature", "celsius"),
            ("humidity", "percent"),
        ],
        "states": [
            ("battery_low", "bool"),
        ],
    },
    "weatherhub_id04": {
        "measurements": [
            ("temperature", "celsius"),
            ("humidity", "percent"),
        ],
        "states": [
            ("battery_low", "bool"),
            ("water_contact", "bool"),  # vorbereitet, noch nicht im Reader
        ],
    },
    "weatherhub_id07": {
        "measurements": [
            ("temperature_indoor", "celsius"),
            ("humidity_indoor", "percent"),
            ("temperature_outdoor", "celsius"),
            ("humidity_outdoor", "percent"),
        ],
        "states": [
            ("battery_low", "bool"),
        ],
    },
    "weatherhub_id0e": {
        "measurements": [
            ("temperature", "celsius"),
            ("humidity", "percent"),
        ],
        "states": [
            ("battery_low", "bool"),
        ],
    },
    "weatherhub_id10": {
        "measurements": [],
        "states": [
            ("battery_low", "bool"),
            ("contact_open", "bool"),  # vorbereitet, noch nicht im Reader
        ],
    },
}


def get_schema(device_type: str) -> Dict[str, List]:
    """Liefert das Schema für einen Sensor-Typ.

    Fällt auf ein leeres Schema zurück, wenn der Typ unbekannt ist.
    """
    return SENSOR_SCHEMAS.get(device_type, {"measurements": [], "states": []})


def get_measurement_names(device_type: str) -> List[str]:
    """Liefert die Measurement-Namen für einen Sensor-Typ."""
    return [name for name, _ in get_schema(device_type)["measurements"]]


def get_state_names(device_type: str) -> List[str]:
    """Liefert die State-Namen für einen Sensor-Typ."""
    return [name for name, _ in get_schema(device_type)["states"]]


MEASUREMENT_DISPLAY_NAMES = {
    "temperature_1": "Temperature",
    "temperature_2": "Temperature",
    "temperature_3": "Temperature",
    "temperature_4": "Temperature",
    "temperature": "Temperature",
    "humidity": "Humidity",
    "vacuum": "Vacuum",
    "co2": "CO₂",
    "o2": "O₂",
    "fan_speed": "Fan speed",
    "battery_low": "Battery",
    "door_open": "Door",
    "contact_open": "Contact",
    "alarm": "Alarm",
    "loggerpi_offline": "LoggerPi",
}
