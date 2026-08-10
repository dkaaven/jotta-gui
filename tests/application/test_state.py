from dataclasses import FrozenInstanceError

import pytest

from jotta_gui.application.state import (
    ApplicationState,
    SyncActivity,
    SyncMode,
    SyncOperation,
    sync_mode_from_automatic,
)


def test_application_state_defaults() -> None:
    state = ApplicationState()

    assert state.connected is False
    assert state.status is None
    assert state.disk_usage is None
    assert state.sync_mode == SyncMode.UNKNOWN
    assert state.sync_operation == SyncOperation.IDLE
    assert state.sync_activity == SyncActivity.UNKNOWN
    assert state.sync_activity_status is None
    assert state.error_message is None


@pytest.mark.parametrize(
    ("automatic", "expected"),
    [
        (True, SyncMode.AUTOMATIC),
        (None, SyncMode.TRIGGERED),
        (False, SyncMode.UNKNOWN),
    ],
)
def test_sync_mode_uses_only_observed_automatic_values(
    automatic: bool | None,
    expected: SyncMode,
) -> None:
    assert sync_mode_from_automatic(automatic) == expected


def test_application_state_is_immutable() -> None:
    state = ApplicationState()

    with pytest.raises(FrozenInstanceError):
        state.connected = True
