from datetime import datetime
from pathlib import Path

from loggerpi_otterpi.system_info import (
    get_boot_info,
    get_cpu_info,
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

    assert result["uptime_seconds"] == 1234.56
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

    assert result["uptime_seconds"] == 100.0
    datetime.fromisoformat(result["last_boot_at"])


def test_get_cpu_info_reads_proc_stat(tmp_path: Path) -> None:
    stat = tmp_path / "stat"
    stat.write_text(
        "cpu  100 20 30 850 0 0 0 0 0 0\n",
        encoding="utf-8",
    )

    result = get_cpu_info(proc_stat=stat)

    assert result["usage_percent"] == 15.0
