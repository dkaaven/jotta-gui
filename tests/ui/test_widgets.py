
import pytest

pytest.importorskip("PySide6")

from jotta_gui.application.state import ApplicationState, SyncState
from jotta_gui.jotta.status.parser import parse_status
from jotta_gui.system.storage import DiskUsage
from jotta_gui.ui.components.header import Header
from jotta_gui.ui.pages.overview import OverviewPage
from jotta_gui.ui.pages.sync import SyncPage

pytestmark = pytest.mark.qt


def _state(status_payload: dict, sync_state: SyncState) -> ApplicationState:
    return ApplicationState(
        connected=True,
        status=parse_status(status_payload),
        disk_usage=DiskUsage(total=1_000, used=250, free=750),
        sync_state=sync_state,
    )


def test_header_renders_connection_and_sync_state(qt_app) -> None:
    header = Header()

    header.update_state(
        ApplicationState(connected=True, sync_state=SyncState.ACTIVE)
    )

    assert header.connection.text() == "● Connected"
    assert header.sync_status.text() == "● Sync active"


def test_sync_page_active_controls(qt_app, status_payload: dict) -> None:
    page = SyncPage()

    page.update_state(_state(status_payload, SyncState.ACTIVE))

    assert page.start_button.isEnabled() is False
    assert page.stop_button.isEnabled() is True
    assert page.trigger_button.isEnabled() is False


def test_sync_page_inactive_controls(qt_app, status_payload: dict) -> None:
    page = SyncPage()

    page.update_state(_state(status_payload, SyncState.INACTIVE))

    assert page.start_button.isEnabled() is True
    assert page.stop_button.isEnabled() is False
    assert page.trigger_button.isEnabled() is True


def test_sync_page_pending_disables_controls(qt_app, status_payload: dict) -> None:
    page = SyncPage()

    page.update_state(_state(status_payload, SyncState.STARTING))

    assert page.start_button.isEnabled() is False
    assert page.stop_button.isEnabled() is False
    assert page.trigger_button.isEnabled() is False


def test_sync_page_disabled_sync_disables_controls(qt_app, status_payload: dict) -> None:
    status_payload["Sync"]["Enabled"] = False
    page = SyncPage()

    page.update_state(_state(status_payload, SyncState.UNKNOWN))

    assert page.runtime_status.text() == "● Sync disabled"
    assert page.start_button.isEnabled() is False
    assert page.stop_button.isEnabled() is False
    assert page.trigger_button.isEnabled() is False


def test_overview_renders_account_and_disk(qt_app, status_payload: dict) -> None:
    page = OverviewPage()

    page.update_state(_state(status_payload, SyncState.ACTIVE))

    assert page.user_name.text() == "Example User"
    assert page.storage_card.value_label.text() == "250.0 KB"
    assert page.disk_card.value_label.text() == "750 B"
    assert page.storage_progress.value() == 25
    assert page.disk_progress.value() == 25
