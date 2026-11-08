"""Konstanten für das Dashboard."""

from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")
VERSION = "v1.11.7"

TIME_RANGES = {
    "24h": 24,
    "48h": 48,
    "7d": 7 * 24,
    "14d": 14 * 24,
    "30d": 30 * 24,
    "90d": 90 * 24,
    "365d": 365 * 24,  # Funktionalität bleibt, Button wird ausgeblendet
}

VISIBLE_TIME_RANGES = (
    ("24h", "24h"),
    ("48h", "48h"),
    ("7d", "7d"),
    ("14d", "14d"),
    ("30d", "30d"),
    ("90d", "90d"),
)

SENSOR_COLORS = [
    "#fb923c",  # Orange
    "#38bdf8",  # Hellblau
    "#a78bfa",  # Violett
    "#34d399",  # Grün
    "#f472b6",  # Pink
    "#fbbf24",  # Gelb
    "#22d3ee",  # Cyan
    "#f87171",  # Rot
    "#a3e635",  # Limette
    "#c084fc",  # Lila
]

HUMIDITY_COLORS = [
    "#38bdf8",  # Hellblau (Standard)
    "#a78bfa",  # Violett
    "#34d399",  # Grün
    "#f472b6",  # Pink
    "#22d3ee",  # Cyan
    "#fbbf24",  # Gelb
    "#f87171",  # Rot
    "#a3e635",  # Limette
    "#c084fc",  # Lila
    "#fb923c",  # Orange
]
