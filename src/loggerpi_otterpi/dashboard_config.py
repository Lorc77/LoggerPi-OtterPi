"""Konfiguration für das Dashboard – Sensor-Zuordnung und Raumnamen.

Diese Datei enthält die Raum- und Gerätekonfiguration für das Dashboard.
Bei Sensor-Umzügen oder neuen Geräten muss nur diese Datei angepasst werden.

Deployment-Hinweis:
    Nach Änderungen an dieser Datei muss das Dashboard neu deployt werden:
        sudo /usr/local/sbin/loggerpi-otterpi-update otterpi

    Alternativ (ohne Deployment, direkt auf dem OtterPi):
        sudo nano /opt/loggerpi-otterpi/dashboard_config.py
        sudo systemctl restart otterpi.observer.service
"""

ROOMS = {
    "r1304": {
        "name": "R1304 · Culture Room I",
        "icon": "🦗",
        "devices": [
            {"name": "Freezer · -80 °C", "key": "freezer", "type": "freezer"},
            {"name": "DryAger", "key": "weatherhub_0e74a4597b54", "type": "weatherhub_id0e"},
            {"name": "Memmert HPP260 · left", "key": "atmoweb_101", "type": "atmoweb"},
            {"name": "Memmert HPP260 · right", "key": "atmoweb_102", "type": "atmoweb"},
            {"name": "Memmert IPP300 · left", "key": "memmert_ipp300_links", "type": "memmert"},
            {"name": "Memmert IPP300 · right", "key": "memmert_ipp300_rechts", "type": "memmert"},
        ],
        "weatherhub_climate": ["weatherhub_03469858af14"],
    },
    "r1306": {
        "name": "R1306 · Molecular Lab",
        "icon": "🧬",
        "devices": [
            {"name": "Freezer · Door", "key": "weatherhub_017453bf9a79", "type": "weatherhub_id01"},
            {
                "name": "Freezer · Windows",
                "key": "weatherhub_0106caf71038",
                "type": "weatherhub_id01",
            },
            {"name": "Fridge-freezer", "key": "weatherhub_015f9410f3eb", "type": "weatherhub_id01"},
        ],
        "weatherhub_climate": [],
    },
    "r1307": {
        "name": "R1307 · Cold Room Vestibule",
        "icon": "❄️",
        "devices": [
            {"name": "Freezer", "key": "weatherhub_017262bf9016", "type": "weatherhub_id01"},
        ],
        "weatherhub_climate": [],
    },
    "r1308": {
        "name": "R1308 · Culture Room II",
        "icon": "🧫",
        "devices": [
            {
                "name": "<i>Hypsibius</i> · top left/night",
                "key": "weatherhub_015c32e3ced1",
                "type": "weatherhub_id01",
            },
            {
                "name": "<i>Hypsibius</i> · bottom left/night",
                "key": "weatherhub_015eb583b95c",
                "type": "weatherhub_id01",
            },
            {
                "name": "<i>Hypsibius</i> · top right/day",
                "key": "weatherhub_015e664f727f",
                "type": "weatherhub_id01",
            },
            {
                "name": "<i>Hypsibius</i> · bottom right/day",
                "key": "weatherhub_0167554c25be",
                "type": "weatherhub_id01",
            },
        ],
        "weatherhub_climate": [],
    },
    "r1309": {
        "name": "R1309 · RNA Lab",
        "icon": "🧪",
        "devices": [
            {"name": "Fridge-freezer", "key": "weatherhub_0167ce8a9af4", "type": "weatherhub_id01"},
        ],
        "weatherhub_climate": [],
    },
    "r1310": {
        "name": "R1310 · Histology Lab",
        "icon": "🔬",
        "devices": [
            {
                "name": "<i>Ramazzottius</i> · left/day",
                "key": "weatherhub_015d087ca01c",
                "type": "weatherhub_id01",
            },
            {
                "name": "<i>Ramazzottius</i> · right/night",
                "key": "weatherhub_0146471130bf",
                "type": "weatherhub_id01",
            },
            {
                "name": "Freezer · Cryostat",
                "key": "weatherhub_010678c5ab4a",
                "type": "weatherhub_id01",
            },
        ],
        "weatherhub_climate": [],
    },
    "r1311": {
        "name": "R1311 · Immunology Lab",
        "icon": "🦠",
        "devices": [
            {
                "name": "Refrigerator · Antibodies",
                "key": "weatherhub_0101f89974e0",
                "type": "weatherhub_id01",
            },
            {
                "name": "Freezer · Antibodies",
                "key": "weatherhub_017a5cd3fc1c",
                "type": "weatherhub_id01",
            },
        ],
        "weatherhub_climate": [],
    },
    "r1313": {
        "name": "R1313 · Teaching Lab",
        "icon": "🎓",
        "devices": [
            {"name": "Freezer", "key": "weatherhub_0169706ebe2c", "type": "weatherhub_id01"},
        ],
        "weatherhub_climate": [],
    },
}
