from datetime import datetime
from pathlib import Path

from loggerpi_otterpi.system_info import (
    get_boot_info,
    get_cpu_info,
    get_load_info,
    get_memory_info,
    get_system_time,
)


def test_get_system_time_returns_expected_fields() -> None:
    result = get_system_time()

    assert set(result) == {"current", "timezone", "clock_state"}
    datetime.fromisoformat(result["current"])
    assert result["timezone"]
    assert result["clock_state"] == "unknown"


def test_get_boot_info_reads_proc_files(tmp_path: Path) -> None:
    uptime = tmp_path / "uptime"
    uptime.write_text("1234.56 9876.54\n", encoding="utf-8")

    stat = tmp_path / "stat"
    stat.write_text(
        "cpu  100 200 300 400\nbtime 1750000000\n",
        encoding="utf-8",
    )

    result = get_boot_info(
        proc_uptime=uptime,
        proc_stat=stat,
    )

    assert result["uptime_seconds"] == 1234
    boot_time = datetime.fromisoformat(result["last_boot_at"])
    assert boot_time.timestamp() == 1750000000


def test_get_boot_info_falls_back_to_uptime(tmp_path: Path) -> None:
    uptime = tmp_path / "uptime"
    uptime.write_text("100.0 200.0\n", encoding="utf-8")

    stat = tmp_path / "stat"
    stat.write_text(
        "cpu  100 200 300 400\n",
        encoding="utf-8",
    )

    result = get_boot_info(
        proc_uptime=uptime,
        proc_stat=stat,
    )

    assert result["uptime_seconds"] == 100
    datetime.fromisoformat(result["last_boot_at"])


def test_get_cpu_info_reads_proc_stat(tmp_path: Path) -> None:
    stat = tmp_path / "stat"
    stat.write_text(
        "cpu  100 20 30 850 0 0 0 0 0 0\n",
        encoding="utf-8",
    )

    result = get_cpu_info(proc_stat=stat)

    assert result["usage_percent"] == 15.0


def test_get_memory_info_reads_proc_meminfo(tmp_path: Path) -> None:
    meminfo = tmp_path / "meminfo"
    meminfo.write_text(
        "MemTotal:       102400 kB\nMemAvailable:    25600 kB\nMemFree:         12800 kB\n",
        encoding="utf-8",
    )

    result = get_memory_info(proc_meminfo=meminfo)

    assert result["total_bytes"] == 102400 * 1024.0
    assert result["available_bytes"] == 25600 * 1024.0
    assert result["used_bytes"] == 76800 * 1024.0


def test_get_load_info_reads_proc_loadavg(tmp_path: Path) -> None:
    loadavg = tmp_path / "loadavg"
    loadavg.write_text(
        "0.42 0.35 0.28 1/123 45678\n",
        encoding="utf-8",
    )

    result = get_load_info(proc_loadavg=loadavg)

    assert result["load_1m"] == 0.42
    assert result["load_5m"] == 0.35
    assert result["load_15m"] == 0.28
