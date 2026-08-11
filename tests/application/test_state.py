from dataclasses import FrozenInstanceError

import pytest

from jotta_gui.application.state import (
    ApplicationError,
    ApplicationState,
    RefreshState,
    SyncOperation,
    VersionCheckState,
)


def test_application_state_defaults() -> None:
    state = ApplicationState()

    assert state.connected is False
    assert state.snapshot is None
    assert state.disk_usage is None
    assert state.version is None
    assert state.version_check_state == VersionCheckState.IDLE
    assert state.version_error is None
    assert state.version_checking is False
    assert state.refresh_state == RefreshState.IDLE
    assert state.sync_operation == SyncOperation.IDLE
    assert state.backup_ignores.backup_name is None
    assert state.backup_ignores.busy is False
    assert state.error is None
    assert state.refreshing is False
    assert state.sync_busy is False


def test_application_state_reports_busy_properties() -> None:
    state = ApplicationState(
        refresh_state=RefreshState.REFRESHING,
        sync_operation=SyncOperation.TRIGGERING,
        version_check_state=VersionCheckState.CHECKING,
    )

    assert state.refreshing is True
    assert state.sync_busy is True
    assert state.version_checking is True


def test_application_error_is_structured() -> None:
    error = ApplicationError("sync_trigger", "case collision", exit_code=1)

    assert error.command == "sync_trigger"
    assert error.message == "case collision"
    assert error.exit_code == 1


def test_application_state_is_immutable() -> None:
    state = ApplicationState()

    with pytest.raises(FrozenInstanceError):
        state.connected = True
