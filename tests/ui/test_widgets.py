from datetime import datetime, timezone
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from jotta_gui.application.state import (
    ApplicationError,
    ApplicationState,
    BackupIgnoreState,
    RefreshState,
    SyncOperation,
    VersionCheckState,
)
from jotta_gui.jotta.models import (
    AccountStatus,
    BackupStatus,
    FileStats,
    JottaSnapshot,
    SyncActivity,
    SyncMode,
    SyncStatus,
)
from jotta_gui.jotta.version import VersionInfo
from jotta_gui.system.storage import DiskUsage
from jotta_gui.ui.components import ErrorBanner, Header
from jotta_gui.ui.pages import BackupPage, OverviewPage, SettingsPage, SyncPage

pytestmark = pytest.mark.qt


def _snapshot(mode: SyncMode = SyncMode.AUTOMATIC) -> JottaSnapshot:
    return JottaSnapshot(
        account=AccountStatus(
            email="user@example.com",
            fullname="Example User",
            hostname="example-host",
            brand="Jottacloud",
            capacity=1_000_000,
            usage=250_000,
            subscription_code=1,
            subscription_name="Home",
            product_name="Home 5 TB",
            device_name="Bob",
            device_type=12,
        ),
        sync=SyncStatus(
            enabled=True,
            mode=mode,
            activity=SyncActivity.LISTENING if mode == SyncMode.AUTOMATIC else SyncActivity.TRIGGERED,
            root_path=Path("/home/example/Jotta"),
            local=FileStats(files=12, bytes=1_000),
            remote=FileStats(files=None, bytes=None),
            folder_count=3,
            activity_text="Checking for changes...",
            runtime_mode_text="listening to events",
            cli_sync_state=1,
        ),
        backups=(
            BackupStatus(
                name="Documents",
                path=Path("/home/example/Documents"),
                count=FileStats(files=5, bytes=500),
                device_id="dev-1",
                last_update_ms=1_700_000_000_000,
                last_scan_started_ms=None,
                next_backup_ms=None,
            ),
        ),
        captured_at=datetime.now(timezone.utc),
    )


def _state(mode: SyncMode = SyncMode.AUTOMATIC, **changes) -> ApplicationState:
    values = dict(
        connected=True,
        snapshot=_snapshot(mode),
        disk_usage=DiskUsage(total=1_000, used=250, free=750),
    )
    values.update(changes)
    return ApplicationState(**values)


def test_header_shows_refreshing(qt_app) -> None:
    header = Header()
    header.update_state(_state(refresh_state=RefreshState.REFRESHING))
    assert header.connection.text() == "Refreshing…"
    assert header.refresh_button.isEnabled() is False


def test_error_banner_renders_application_error(qt_app) -> None:
    banner = ErrorBanner()
    error = ApplicationError("sync_trigger", "case collision", 1)
    banner.show_error(error.command, error.message)
    assert banner.isVisible() is True
    assert "sync trigger" in banner.message.text()
    assert "case collision" in banner.message.text()


def test_overview_uses_snapshot_without_inventing_remote_values(qt_app) -> None:
    page = OverviewPage()
    page.update_state(_state())
    assert page.account_name.text() == "Example User"
    assert page.storage_card.value_label.text() == "250.0 KB"
    assert page.sync_card.value_label.text() == "12"


def test_sync_page_automatic_controls(qt_app) -> None:
    page = SyncPage()
    page.update_state(_state(SyncMode.AUTOMATIC))
    assert page.start_button.isEnabled() is False
    assert page.stop_button.isEnabled() is True
    assert page.trigger_button.isEnabled() is False
    assert page.force_start_button.isHidden() is True


def test_sync_page_triggered_controls(qt_app) -> None:
    page = SyncPage()
    page.update_state(_state(SyncMode.TRIGGERED))
    assert page.start_button.isEnabled() is True
    assert page.stop_button.isEnabled() is False
    assert page.trigger_button.isEnabled() is True


def test_sync_page_pending_disables_controls(qt_app) -> None:
    page = SyncPage()
    page.update_state(_state(SyncMode.TRIGGERED, sync_operation=SyncOperation.TRIGGERING))
    assert page.start_button.isEnabled() is False
    assert page.stop_button.isEnabled() is False
    assert page.trigger_button.isEnabled() is False
    assert page.status_pill.text() == "Syncing now…"


def test_backup_page_renders_snapshot_rows(qt_app) -> None:
    page = BackupPage()
    page.update_state(_state())
    assert page.folder_card.value_label.text() == "1"
    assert page.file_card.value_label.text() == "5"
    assert page.rows.count() == 1


def test_settings_page_uses_account_snapshot(qt_app) -> None:
    page = SettingsPage()
    page.update_state(_state())
    assert page.values["email"].text() == "user@example.com"
    assert page.values["device"].text() == "Bob"


def test_sync_page_offers_force_start_only_after_start_failure(qt_app) -> None:
    page = SyncPage()
    page.update_state(
        _state(
            SyncMode.TRIGGERED,
            error=ApplicationError("sync_start", "critical sync error", 1),
        )
    )
    assert page.force_start_button.isHidden() is False
    assert page.force_start_button.isEnabled() is True


def test_backup_page_loads_presets_from_config(qt_app) -> None:
    page = BackupPage()
    page.update_state(_state())

    assert page.backup_selector.currentText() == "Documents"
    assert len(page.presets) == 6
    assert page.preset_buttons["git"].isEnabled() is True


def test_backup_page_activation_requests_current_rules(qt_app) -> None:
    page = BackupPage()
    requested = []
    page.rules_requested.connect(requested.append)
    page.update_state(_state())

    page.activate()

    assert requested == ["Documents"]


def test_backup_page_displays_jotta_rule_output_verbatim(qt_app) -> None:
    page = BackupPage()
    output = "Backup: Documents\n  **/.git\n  **/.venv"
    page.update_state(
        _state(backup_ignores=BackupIgnoreState("Documents", output))
    )

    assert page.current_rules.toPlainText() == output
    assert page.rules_status.text() == "Current rules for Documents"


def test_backup_page_preset_emits_selected_backup_and_pattern(qt_app) -> None:
    page = BackupPage()
    requested = []
    page.ignore_add_requested.connect(
        lambda backup, pattern: requested.append((backup, pattern))
    )
    page.update_state(_state())

    page.preset_buttons["git"].click()

    assert requested == [("Documents", "**/.git")]


def test_backup_page_preset_remove_emits_selected_backup_and_pattern(qt_app) -> None:
    page = BackupPage()
    requested = []
    page.ignore_remove_requested.connect(
        lambda backup, pattern: requested.append((backup, pattern))
    )
    page.update_state(_state())

    page.preset_remove_buttons["git"].click()

    assert requested == [("Documents", "**/.git")]


def test_overview_shows_update_available(qt_app) -> None:
    page = OverviewPage()
    page.update_state(
        _state(
            version=VersionInfo(
                cli_version="0.17.159692",
                daemon_version="0.17.159692",
                remote_version="0.17.176206",
            )
        )
    )

    assert page.version_pill.text() == "Update available"
    assert "0.17.159692" in page.version_detail.text()
    assert "0.17.176206" in page.version_detail.text()


def test_overview_shows_up_to_date(qt_app) -> None:
    page = OverviewPage()
    page.update_state(
        _state(
            version=VersionInfo(
                cli_version="0.17.176206",
                remote_version="0.17.176206",
            )
        )
    )

    assert page.version_pill.text() == "Up to date"


def test_overview_shows_up_to_date_when_remote_version_is_omitted(qt_app) -> None:
    page = OverviewPage()
    page.update_state(
        _state(
            version=VersionInfo(
                cli_version="0.17.176206",
                daemon_version="0.17.176206",
                remote_version=None,
            )
        )
    )

    assert page.version_pill.text() == "Up to date"
    assert "no newer version reported" in page.version_detail.text()


def test_overview_shows_version_checking(qt_app) -> None:
    page = OverviewPage()
    page.update_state(
        _state(version_check_state=VersionCheckState.CHECKING)
    )

    assert page.version_pill.text() == "Checking…"
