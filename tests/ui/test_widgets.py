import pytest

pytest.importorskip("PySide6")

from jotta_gui.application.state import (
    ApplicationState,
    SyncActivity,
    SyncMode,
    SyncOperation,
)
from jotta_gui.jotta.status.parser import parse_status
from jotta_gui.system.storage import DiskUsage
from jotta_gui.ui.components.header import Header
from jotta_gui.ui.pages.overview import OverviewPage
from jotta_gui.ui.pages.sync import SyncPage

pytestmark = pytest.mark.qt


def _state(
    status_payload: dict,
    *,
    mode: SyncMode = SyncMode.TRIGGERED,
    operation: SyncOperation = SyncOperation.IDLE,
    activity: SyncActivity = SyncActivity.UNKNOWN,
    activity_status: str | None = None,
) -> ApplicationState:
    return ApplicationState(
        connected=True,
        status=parse_status(status_payload),
        disk_usage=DiskUsage(total=1_000, used=250, free=750),
        sync_mode=mode,
        sync_operation=operation,
        sync_activity=activity,
        sync_activity_status=activity_status,
    )


def test_header_renders_connection_and_automatic_mode(qt_app) -> None:
    header = Header()

    header.update_state(
        ApplicationState(connected=True, sync_mode=SyncMode.AUTOMATIC)
    )

    assert header.connection.text() == "● Connected"
    assert header.sync_status.text() == "● Automatic sync"


def test_sync_page_automatic_controls(qt_app, status_payload: dict) -> None:
    page = SyncPage()

    page.update_state(_state(status_payload, mode=SyncMode.AUTOMATIC))

    assert page.start_button.isEnabled() is False
    assert page.stop_button.isEnabled() is True
    assert page.trigger_button.isEnabled() is False


def test_sync_page_triggered_controls(qt_app, status_payload: dict) -> None:
    page = SyncPage()

    page.update_state(_state(status_payload, mode=SyncMode.TRIGGERED))

    assert page.start_button.isEnabled() is True
    assert page.stop_button.isEnabled() is False
    assert page.trigger_button.isEnabled() is True


def test_sync_page_pending_disables_controls(qt_app, status_payload: dict) -> None:
    page = SyncPage()

    page.update_state(
        _state(
            status_payload,
            mode=SyncMode.TRIGGERED,
            operation=SyncOperation.STARTING,
        )
    )

    assert page.start_button.isEnabled() is False
    assert page.stop_button.isEnabled() is False
    assert page.trigger_button.isEnabled() is False


def test_sync_page_unknown_mode_disables_controls(qt_app, status_payload: dict) -> None:
    page = SyncPage()

    page.update_state(_state(status_payload, mode=SyncMode.UNKNOWN))

    assert page.start_button.isEnabled() is False
    assert page.stop_button.isEnabled() is False
    assert page.trigger_button.isEnabled() is False


def test_sync_page_disabled_sync_disables_controls(qt_app, status_payload: dict) -> None:
    status_payload["Sync"]["Enabled"] = False
    page = SyncPage()

    page.update_state(_state(status_payload, mode=SyncMode.UNKNOWN))

    assert page.runtime_status.text() == "● Sync disabled"
    assert page.start_button.isEnabled() is False
    assert page.stop_button.isEnabled() is False
    assert page.trigger_button.isEnabled() is False


def test_sync_page_shows_activity_as_secondary_information(
    qt_app,
    status_payload: dict,
) -> None:
    page = SyncPage()

    page.update_state(
        _state(
            status_payload,
            mode=SyncMode.TRIGGERED,
            activity=SyncActivity.TRIGGERED,
            activity_status="Checking for changes...",
        )
    )

    assert page.runtime_status.text() == "● Manual sync mode — Checking for changes..."


def test_overview_renders_account_and_disk(qt_app, status_payload: dict) -> None:
    page = OverviewPage()

    page.update_state(_state(status_payload, mode=SyncMode.AUTOMATIC))

    assert page.user_name.text() == "Example User"
    assert page.storage_card.value_label.text() == "250.0 KB"
    assert page.disk_card.value_label.text() == "750 B"
    assert page.storage_progress.value() == 25
    assert page.disk_progress.value() == 25
