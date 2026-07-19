import os
from pathlib import Path
from zoneinfo import ZoneInfo

from realty_agent.config import Settings

_ENV_KEYS = [
    "REALTY_AGENT_X_USERNAME",
    "REALTY_AGENT_X_BEARER_TOKEN",
    "REALTY_AGENT_SYNC_FREQUENCY_MINUTES",
    "REALTY_AGENT_BACKFILL_DAYS",
    "REALTY_AGENT_TIMEZONE",
]


def _clear_env():
    for key in _ENV_KEYS:
        os.environ.pop(key, None)


def test_load_defaults_when_file_missing(tmp_path: Path):
    _clear_env()
    settings = Settings.load(tmp_path / "does_not_exist.yaml")
    assert settings.x_username == ""
    assert settings.timezone == "America/Phoenix"
    assert settings.operating_days == ["Mon", "Tue", "Wed", "Thu", "Fri"]
    assert settings.operating_start == "06:00"
    assert settings.operating_end == "18:00"
    assert settings.sync_frequency_minutes == 5
    assert settings.backfill_days == 0
    assert settings.ai_provider == "none"


def test_load_reads_values_from_yaml_file(tmp_path: Path):
    _clear_env()
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(
        'x_username: "my_test_account"\n'
        'timezone: "America/New_York"\n'
        "backfill_days: 14\n"
        "sync_frequency_minutes: 10\n",
        encoding="utf-8",
    )
    settings = Settings.load(config_path)
    assert settings.x_username == "my_test_account"
    assert settings.timezone == "America/New_York"
    assert settings.backfill_days == 14
    assert settings.sync_frequency_minutes == 10


def test_env_var_overrides_yaml_value(tmp_path: Path):
    _clear_env()
    config_path = tmp_path / "settings.yaml"
    config_path.write_text('x_username: "yaml_user"\n', encoding="utf-8")
    os.environ["REALTY_AGENT_X_USERNAME"] = "env_user"
    try:
        settings = Settings.load(config_path)
        assert settings.x_username == "env_user"
    finally:
        _clear_env()


def test_env_var_int_field_is_coerced(tmp_path: Path):
    _clear_env()
    os.environ["REALTY_AGENT_BACKFILL_DAYS"] = "30"
    try:
        settings = Settings.load(tmp_path / "does_not_exist.yaml")
        assert settings.backfill_days == 30
        assert isinstance(settings.backfill_days, int)
    finally:
        _clear_env()


def test_tzinfo_property_returns_zoneinfo(tmp_path: Path):
    _clear_env()
    settings = Settings.load(tmp_path / "does_not_exist.yaml")
    assert settings.tzinfo == ZoneInfo("America/Phoenix")
