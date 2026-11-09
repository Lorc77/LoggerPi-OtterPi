"""Tests für config_store."""

import pytest
from config_store import (
    _DEFAULT_MESSAGES,
    ConfigValidationError,
    load_alarm_limits,
    load_mail,
    load_messages,
    load_notifications,
    load_rooms,
    save_alarm_limits,
    save_mail,
    save_messages,
    save_notifications,
    save_rooms,
)


@pytest.fixture(autouse=True)
def _config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("OTTERPI_CONFIG_DIR", str(tmp_path))
    return tmp_path


def _valid_rooms():
    return {
        "r1304": {
            "name": "R1304 · Culture Room I",
            "icon": "🦗",
            "devices": [
                {"name": "Freezer", "key": "freezer", "type": "freezer"},
            ],
            "weatherhub_climate": ["weatherhub_03469858af14"],
        }
    }


class TestRooms:
    def test_roundtrip(self):
        save_rooms(_valid_rooms())
        assert load_rooms() == _valid_rooms()

    def test_missing_name(self):
        rooms = _valid_rooms()
        del rooms["r1304"]["name"]
        with pytest.raises(ConfigValidationError):
            save_rooms(rooms)

    def test_duplicate_key(self):
        rooms = _valid_rooms()
        rooms["r1304"]["devices"].append({"name": "Dup", "key": "freezer", "type": "freezer"})
        with pytest.raises(ConfigValidationError):
            save_rooms(rooms)

    def test_invalid_room_id(self):
        rooms = {"R1304": {"name": "X", "devices": []}}
        with pytest.raises(ConfigValidationError):
            save_rooms(rooms)

    def test_backup_created(self, _config_dir):
        save_rooms(_valid_rooms())
        save_rooms(_valid_rooms())
        assert (_config_dir / "rooms.json.bak").exists()


class TestAlarmLimits:
    def test_roundtrip(self):
        data = {
            "sensors": {
                "atmoweb_101.temperature_1": {
                    "warning_min": 20.0,
                    "warning_max": 26.0,
                    "critical_min": 18.0,
                    "critical_max": 28.0,
                    "enabled": True,
                }
            }
        }
        save_alarm_limits(data)
        assert load_alarm_limits() == data

    def test_roundtrip_with_states(self):
        data = {
            "sensors": {},
            "states": {
                "freezer.alarms": {"enabled": True},
                "weatherhub_015f9410f3eb.battery_low": {"enabled": True},
                "atmoweb_101.door_open": {"enabled": True, "max_open_seconds": 300},
            },
        }
        save_alarm_limits(data)
        assert load_alarm_limits() == data

    def test_consistency_error(self):
        data = {
            "sensors": {"atmoweb_101.temperature_1": {"warning_min": 30.0, "warning_max": 20.0}}
        }
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_unknown_field(self):
        data = {"sensors": {"atmoweb_101.temperature_1": {"foo": 1}}}
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_invalid_stale(self):
        data = {"sensors": {"atmoweb_101.temperature_1": {"stale_after_seconds": 0}}}
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_states_invalid_key(self):
        data = {"sensors": {}, "states": {"INVALID": {"enabled": True}}}
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_states_missing_enabled(self):
        data = {"sensors": {}, "states": {"freezer.alarms": {}}}
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_states_invalid_max_open_seconds(self):
        data = {
            "sensors": {},
            "states": {"atmoweb_101.door_open": {"enabled": True, "max_open_seconds": 0}},
        }
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)


class TestMail:
    def _valid_mail(self):
        return {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "zoology.kassel@gmail.com",
            "from": "zoology.kassel@gmail.com",
            "recipients": ["a@example.com", "b@example.com"],
            "routing": {"critical": ["a@example.com"], "warning": ["b@example.com"]},
            "dedup_seconds": 3600,
            "quiet_hours": {"start": "22:00", "end": "07:00", "critical_always": True},
        }

    def test_roundtrip(self):
        save_mail(self._valid_mail())
        assert load_mail() == self._valid_mail()

    def test_invalid_email(self):
        mail = self._valid_mail()
        mail["from"] = "not-an-email"
        with pytest.raises(ConfigValidationError):
            save_mail(mail)

    def test_invalid_port(self):
        mail = self._valid_mail()
        mail["smtp_port"] = 70000
        with pytest.raises(ConfigValidationError):
            save_mail(mail)

    def test_routing_subset(self):
        mail = self._valid_mail()
        mail["routing"]["critical"] = ["c@example.com"]
        with pytest.raises(ConfigValidationError):
            save_mail(mail)

    def test_invalid_quiet_hours(self):
        mail = self._valid_mail()
        mail["quiet_hours"]["start"] = "25:00"
        with pytest.raises(ConfigValidationError):
            save_mail(mail)

    def test_enabled_flag(self):
        mail = self._valid_mail()
        mail["enabled"] = True
        save_mail(mail)
        assert load_mail()["enabled"] is True


class TestNotifications:
    def test_roundtrip(self):
        data = {
            "channels": [
                {"type": "ntfy", "enabled": True, "url": "https://ntfy.sh", "topic": "t"},
                {"type": "webhook", "enabled": False, "url": "https://x", "format": "discord"},
            ]
        }
        save_notifications(data)
        assert load_notifications() == data

    def test_invalid_type(self):
        data = {"channels": [{"type": "sms", "enabled": True}]}
        with pytest.raises(ConfigValidationError):
            save_notifications(data)

    def test_missing_enabled(self):
        data = {"channels": [{"type": "ntfy", "url": "https://ntfy.sh", "topic": "t"}]}
        with pytest.raises(ConfigValidationError):
            save_notifications(data)

    def test_ntfy_requires_topic(self):
        data = {"channels": [{"type": "ntfy", "enabled": True, "url": "https://ntfy.sh"}]}
        with pytest.raises(ConfigValidationError):
            save_notifications(data)


class TestAlarmLimitsSystem:
    def test_roundtrip_with_system(self):
        data = {
            "system": {
                "loggerpi_offline_warning_seconds": 1800,
                "loggerpi_offline_critical_seconds": 3600,
                "loggerpi_offline_warning_alert_enabled": False,
            },
            "sensors": {},
        }
        save_alarm_limits(data)
        assert load_alarm_limits() == data

    def test_system_optional(self):
        data = {"sensors": {}}
        save_alarm_limits(data)
        assert load_alarm_limits() == data

    def test_system_unknown_field(self):
        data = {"system": {"foo": 1}, "sensors": {}}
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_system_invalid_warning_seconds(self):
        data = {"system": {"loggerpi_offline_warning_seconds": 0}, "sensors": {}}
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_system_invalid_critical_seconds(self):
        data = {"system": {"loggerpi_offline_critical_seconds": -1}, "sensors": {}}
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_system_warning_must_be_less_than_critical(self):
        data = {
            "system": {
                "loggerpi_offline_warning_seconds": 3600,
                "loggerpi_offline_critical_seconds": 1800,
            },
            "sensors": {},
        }
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_system_warning_alert_enabled_must_be_bool(self):
        data = {
            "system": {"loggerpi_offline_warning_alert_enabled": "yes"},
            "sensors": {},
        }
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)


class TestMessages:
    def test_load_defaults_when_missing(self):
        messages = load_messages()
        assert messages["critical_max"] == "too high"
        assert messages["loggerpi_offline"] == "offline"

    def test_roundtrip(self):
        data = dict(_DEFAULT_MESSAGES)
        data["critical_max"] = "Too hot!"
        save_messages(data)
        assert load_messages()["critical_max"] == "Too hot!"

    def test_missing_keys_filled_with_defaults(self):
        save_messages({"critical_max": "Too hot!"})
        messages = load_messages()
        assert messages["critical_max"] == "Too hot!"
        assert messages["critical_min"] == "too low"

    def test_unknown_key(self):
        with pytest.raises(ConfigValidationError):
            save_messages({"unknown_key": "x"})

    def test_non_string_value(self):
        with pytest.raises(ConfigValidationError):
            save_messages({"critical_max": 123})

    def test_too_long_value(self):
        with pytest.raises(ConfigValidationError):
            save_messages({"critical_max": "x" * 201})


class TestNotificationsSeverities:
    def test_valid_severities(self):
        data = {
            "channels": [
                {
                    "type": "ntfy",
                    "enabled": True,
                    "url": "https://ntfy.sh",
                    "topic": "t",
                    "severities": ["critical"],
                }
            ]
        }
        save_notifications(data)
        assert load_notifications() == data

    def test_invalid_severity(self):
        data = {
            "channels": [
                {
                    "type": "ntfy",
                    "enabled": True,
                    "url": "https://ntfy.sh",
                    "topic": "t",
                    "severities": ["info"],
                }
            ]
        }
        with pytest.raises(ConfigValidationError):
            save_notifications(data)

    def test_severities_optional(self):
        data = {
            "channels": [
                {
                    "type": "ntfy",
                    "enabled": True,
                    "url": "https://ntfy.sh",
                    "topic": "t",
                }
            ]
        }
        save_notifications(data)
        assert load_notifications() == data


def test_states_nested_key():
    data = {
        "sensors": {},
        "states": {"atmoweb_101.switches.a": {"enabled": True}},
    }
    save_alarm_limits(data)
    assert load_alarm_limits() == data


def test_states_nested_lights_key():
    data = {
        "sensors": {},
        "states": {"atmoweb_101.lights.day": {"enabled": True}},
    }
    save_alarm_limits(data)
    assert load_alarm_limits() == data


class TestStaleInvalidEnabled:
    def test_stale_enabled_valid(self):
        data = {"sensors": {"atmoweb_101.temperature_1": {"stale_enabled": True}}}
        save_alarm_limits(data)
        assert load_alarm_limits() == data

    def test_stale_enabled_invalid(self):
        data = {"sensors": {"atmoweb_101.temperature_1": {"stale_enabled": "yes"}}}
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_invalid_enabled_valid(self):
        data = {"sensors": {"atmoweb_101.temperature_1": {"invalid_enabled": False}}}
        save_alarm_limits(data)
        assert load_alarm_limits() == data

    def test_invalid_enabled_invalid(self):
        data = {"sensors": {"atmoweb_101.temperature_1": {"invalid_enabled": 1}}}
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)


class TestDeviceSection:
    def test_device_roundtrip(self):
        data = {
            "sensors": {},
            "device": {
                "atmoweb_101": {"stale_enabled": True, "invalid_enabled": False},
            },
        }
        save_alarm_limits(data)
        assert load_alarm_limits() == data

    def test_device_invalid_key(self):
        data = {
            "sensors": {},
            "device": {"INVALID": {"stale_enabled": True}},
        }
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_device_invalid_field(self):
        data = {
            "sensors": {},
            "device": {"atmoweb_101": {"stale_enabled": "yes"}},
        }
        with pytest.raises(ConfigValidationError):
            save_alarm_limits(data)

    def test_device_optional(self):
        data = {"sensors": {}}
        save_alarm_limits(data)
        assert load_alarm_limits() == data
