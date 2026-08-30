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
        "uptime_seconds": int(uptime_seconds),
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


def get_memory_info(
    proc_meminfo: Path = Path("/proc/meminfo"),
) -> dict[str, float]:
    """Return memory information from /proc/meminfo."""
    values = _read_meminfo(proc_meminfo)

    total_kib = values["MemTotal"]
    available_kib = values["MemAvailable"]

    return {
        "total_bytes": int(total_kib * 1024),
        "available_bytes": int(available_kib * 1024),
        "used_bytes": int((total_kib - available_kib) * 1024),
    }


def get_load_info(
    proc_loadavg: Path = Path("/proc/loadavg"),
) -> dict[str, float]:
    """Return system load averages from /proc/loadavg."""
    values = proc_loadavg.read_text(encoding="utf-8").split()

    return {
        "load_1m": float(values[0]),
        "load_5m": float(values[1]),
        "load_15m": float(values[2]),
    }


def get_cpu_temperature(
    proc_temperature: Path = Path("/sys/class/thermal/thermal_zone0/temp"),
) -> float:
    """Return CPU temperature in degrees Celsius."""
    return int(proc_temperature.read_text(encoding="utf-8").strip()) / 1000.0


def get_system_info(
    proc_uptime: Path = Path("/proc/uptime"),
    proc_stat: Path = Path("/proc/stat"),
    proc_meminfo: Path = Path("/proc/meminfo"),
    proc_loadavg: Path = Path("/proc/loadavg"),
    proc_temperature: Path = Path("/sys/class/thermal/thermal_zone0/temp"),
) -> dict[str, object]:
    """Return the collected system information."""
    return {
        "time": get_system_time(),
        "boot": get_boot_info(proc_uptime, proc_stat),
        "cpu": {
            **get_cpu_info(proc_stat),
            "load": get_load_info(proc_loadavg),
            "temperature_celsius": get_cpu_temperature(proc_temperature),
        },
        "memory": get_memory_info(proc_meminfo),
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


def _read_meminfo(proc_meminfo: Path) -> dict[str, float]:
    """Read memory values from /proc/meminfo."""
    values = {}

    for line in proc_meminfo.read_text(encoding="utf-8").splitlines():
        parts = line.split()

        if len(parts) >= 2:
            values[parts[0].rstrip(":")] = float(parts[1])

    return values
