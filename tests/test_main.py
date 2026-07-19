from unittest.mock import patch

from realty_agent.config import Settings
from realty_agent.errors import XFetchError
from realty_agent.main import _build_x_client, run
from realty_agent.sync.delta_sync import SyncResult
from realty_agent.x_client.mock_client import MockXClient
from realty_agent.x_client.x_api_client import XApiClient


def make_settings(**overrides) -> Settings:
    defaults = dict(
        x_username="test_wholesale_deals",
        x_bearer_token=None,
        onedrive_drive_id=None,
        onedrive_file_path="/RealEstate/listings.xlsx",
        timezone="America/Phoenix",
        operating_days=["Mon", "Tue", "Wed", "Thu", "Fri"],
        operating_start="06:00",
        operating_end="18:00",
        sync_frequency_minutes=5,
        backfill_days=0,
        ai_provider="none",
        ai_model="m",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def test_build_x_client_returns_mock_when_no_token():
    settings = make_settings(x_bearer_token=None)
    client = _build_x_client(settings)
    assert isinstance(client, MockXClient)


def test_build_x_client_returns_real_client_when_token_present():
    settings = make_settings(x_bearer_token="tok")
    client = _build_x_client(settings)
    assert isinstance(client, XApiClient)


def test_run_skips_when_outside_operating_window():
    settings = make_settings()
    with (
        patch("realty_agent.main.is_within_operating_window", return_value=False),
        patch("realty_agent.main.run_delta_sync") as mock_delta,
        patch("realty_agent.main.run_backfill") as mock_backfill,
    ):
        run(settings=settings)
        mock_delta.assert_not_called()
        mock_backfill.assert_not_called()


def test_run_calls_delta_sync_when_inside_window():
    settings = make_settings()
    with (
        patch("realty_agent.main.is_within_operating_window", return_value=True),
        patch("realty_agent.main.run_delta_sync", return_value=SyncResult()) as mock_delta,
        patch("realty_agent.main.run_backfill") as mock_backfill,
    ):
        run(settings=settings)
        mock_delta.assert_called_once()
        mock_backfill.assert_not_called()


def test_run_calls_backfill_and_bypasses_window_check_when_backfill_days_given():
    settings = make_settings()
    with (
        patch("realty_agent.main.is_within_operating_window", return_value=False),
        patch("realty_agent.main.run_backfill", return_value=SyncResult()) as mock_backfill,
        patch("realty_agent.main.run_delta_sync") as mock_delta,
    ):
        run(settings=settings, backfill_days=7)
        mock_backfill.assert_called_once()
        mock_delta.assert_not_called()


def test_run_writes_error_row_on_realty_agent_error():
    settings = make_settings()
    with (
        patch("realty_agent.main.is_within_operating_window", return_value=True),
        patch("realty_agent.main.run_delta_sync", side_effect=XFetchError("boom")),
        patch("realty_agent.main.insert_error_row") as mock_insert_error,
    ):
        run(settings=settings)
        mock_insert_error.assert_called_once()
        _, _, message = mock_insert_error.call_args[0]
        assert "XFetchError" in message
        assert "boom" in message


def test_run_writes_error_row_on_unexpected_error():
    settings = make_settings()
    with (
        patch("realty_agent.main.is_within_operating_window", return_value=True),
        patch("realty_agent.main.run_delta_sync", side_effect=RuntimeError("kaboom")),
        patch("realty_agent.main.insert_error_row") as mock_insert_error,
    ):
        run(settings=settings)
        mock_insert_error.assert_called_once()
        _, _, message = mock_insert_error.call_args[0]
        assert "kaboom" in message


def test_run_uses_default_settings_when_none_given():
    with (
        patch("realty_agent.main.Settings.load", return_value=make_settings()) as mock_load,
        patch("realty_agent.main.is_within_operating_window", return_value=False),
    ):
        run()
        mock_load.assert_called_once()


def test_cli_forwards_backfill_days_argument():
    with (
        patch("realty_agent.main.run") as mock_run,
        patch("sys.argv", ["prog", "--backfill-days", "5"]),
    ):
        from realty_agent.main import _cli

        _cli()
        mock_run.assert_called_once_with(backfill_days=5)


def test_cli_defaults_backfill_days_to_none():
    with patch("realty_agent.main.run") as mock_run, patch("sys.argv", ["prog"]):
        from realty_agent.main import _cli

        _cli()
        mock_run.assert_called_once_with(backfill_days=None)
