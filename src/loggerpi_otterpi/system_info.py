from datetime import datetime, timezone
from pathlib import Path


def get_system_time() -> dict[str, str]:
    """Return the current system time information."""
    now = datetime.now(timezone.utc).astimezone()

    return {
        "current": now.isoformat(),
        "timezone": now.tzname() or "unknown",
        "clock_state": "unknown",
    }


def get_boot_info(
    proc_uptime: Path = Path("/proc/uptime"),
    proc_stat: Path = Path("/proc/stat"),
) -> dict[str, object]:
    """Return the last boot time and current uptime."""
    uptime_seconds = _read_uptime(proc_uptime)
    last_boot_at = _read_boot_time(proc_stat, uptime_seconds)

    return {
        "last_boot_at": last_boot_at,
        "uptime_seconds": uptime_seconds,
    }


def get_cpu_info(
    proc_stat: Path = Path("/proc/stat"),
) -> dict[str, float]:
    """Return CPU load information from /proc/stat."""
    line = _read_cpu_line(proc_stat)
    fields = line.split()

    user = float(fields[1])
    nice = float(fields[2])
    system = float(fields[3])
    idle = float(fields[4])
    iowait = float(fields[5])

    total = user + nice + system + idle + iowait
    busy = user + nice + system

    usage_percent = (busy / total * 100.0) if total else 0.0

    return {
        "usage_percent": usage_percent,
    }


def _read_uptime(proc_uptime: Path) -> float:
    """Read uptime in seconds from /proc/uptime."""
    content = proc_uptime.read_text(encoding="utf-8")
    return float(content.split()[0])


def _read_boot_time(proc_stat: Path, uptime_seconds: float) -> str:
    """Calculate the boot timestamp from /proc/stat uptime information."""
    for line in proc_stat.read_text(encoding="utf-8").splitlines():
        if line.startswith("btime "):
            boot_timestamp = float(line.split()[1])
            return (
                datetime.fromtimestamp(
                    boot_timestamp,
                    tz=timezone.utc,
                )
                .astimezone()
                .isoformat()
            )

    boot_time = datetime.now(timezone.utc).timestamp() - uptime_seconds
    return (
        datetime.fromtimestamp(
            boot_time,
            tz=timezone.utc,
        )
        .astimezone()
        .isoformat()
    )


def _read_cpu_line(proc_stat: Path) -> str:
    """Read the aggregate CPU line from /proc/stat."""
    for line in proc_stat.read_text(encoding="utf-8").splitlines():
        if line.startswith("cpu "):
            return line

    raise ValueError("CPU information not found in /proc/stat")
