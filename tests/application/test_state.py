
from dataclasses import FrozenInstanceError

import pytest

from jotta_gui.application.state import ApplicationState, SyncState


def test_application_state_defaults() -> None:
    state = ApplicationState()

    assert state.connected is False
    assert state.status is None
    assert state.disk_usage is None
    assert state.sync_state == SyncState.UNKNOWN
    assert state.error_message is None


def test_application_state_is_immutable() -> None:
    state = ApplicationState()

    with pytest.raises(FrozenInstanceError):
        state.connected = True
