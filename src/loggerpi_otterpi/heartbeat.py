"""Gemeinsame Heartbeat-/Offline-Status-Logik für Admin und Dashboard."""

from datetime import datetime, timezone
from typing import Optional


def offline_status(
    last_received_at: Optional[str],
    warning_seconds: int = 1800,
    critical_seconds: int = 3600,
) -> tuple[str, str]:
    """Liefert (CSS-Klasse, Text) für die Statusanzeige im Header.

    - ``status-off``: noch kein Batch empfangen oder ungültiger Zeitstempel
    - ``status-ok``: letzter Batch innerhalb der Warnschwelle
    - ``status-warn``: letzter Batch zwischen Warn- und Kritisch-Schwelle
    - ``status-critical``: letzter Batch älter als die Kritisch-Schwelle
    """
    if not last_received_at:
        return ("status-off", "No batch received yet")

    try:
        last_dt = datetime.fromisoformat(last_received_at)
    except ValueError:
        return ("status-off", "Invalid timestamp")

    age_seconds = (datetime.now(timezone.utc) - last_dt).total_seconds()
    minutes = int(age_seconds // 60)

    if age_seconds >= critical_seconds:
        return ("status-critical", f"LoggerPi offline for {minutes} min")
    if age_seconds >= warning_seconds:
        return ("status-warn", f"Last batch {minutes} min ago")
    return ("status-ok", f"Last batch {minutes} min ago")
