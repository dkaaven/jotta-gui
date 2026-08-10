import json

import pytest

pytest.importorskip("PySide6")

import jotta_gui.application.controller as controller_module
from jotta_gui.application.controller import ApplicationController
from jotta_gui.application.state import SyncActivity, SyncMode, SyncOperation
from jotta_gui.system.storage import DiskUsage

pytestmark = pytest.mark.qt


def test_start_requests_status(qt_app, monkeypatch) -> None:
    controller = ApplicationController()
    calls = []
    monkeypatch.setattr(controller_module, "get_status", calls.append)

    controller.start()

    assert calls == [controller.runner]


@pytest.mark.parametrize(
    ("method_name", "command_name", "expected_operation"),
    [
        ("start_sync", "sync_start", SyncOperation.STARTING),
        ("stop_sync", "sync_stop", SyncOperation.STOPPING),
        ("trigger_sync", "sync_trigger", SyncOperation.TRIGGERING),
    ],
)
def test_sync_action_sets_pending_operation_and_runs_command(
    qt_app,
    monkeypatch,
    method_name: str,
    command_name: str,
    expected_operation: SyncOperation,
) -> None:
    controller = ApplicationController()
    calls = []
    monkeypatch.setattr(
        controller_module,
        command_name,
        lambda runner: calls.append(runner),
    )

    getattr(controller, method_name)()

    assert controller.state.sync_operation == expected_operation
    assert controller.state.error_message is None
    assert calls == [controller.runner]


def test_status_output_sets_triggered_mode_when_automatic_is_absent(
    qt_app,
    monkeypatch,
    status_output: str,
) -> None:
    controller = ApplicationController()
    runtime_calls = []
    disk = DiskUsage(total=1_000, used=250, free=750)
    monkeypatch.setattr(controller_module, "get_disk_usage", lambda path: disk)
    monkeypatch.setattr(
        controller_module,
        "get_sync_runtime_status",
        runtime_calls.append,
    )

    controller._handle_status_output(status_output)

    assert controller.state.connected is True
    assert controller.state.status is not None
    assert controller.state.status.user.fullname == "Example User"
    assert controller.state.disk_usage == disk
    assert controller.state.sync_mode == SyncMode.TRIGGERED
    assert controller.state.sync_operation == SyncOperation.IDLE
    assert controller.state.sync_activity == SyncActivity.UNKNOWN
    assert controller.state.error_message is None
    assert runtime_calls == [controller.runner]


def test_status_output_sets_automatic_mode_from_json(
    qt_app,
    monkeypatch,
    status_payload: dict,
) -> None:
    status_payload["Sync"]["Automatic"] = True
    controller = ApplicationController()
    monkeypatch.setattr(
        controller_module,
        "get_disk_usage",
        lambda path: DiskUsage(total=1, used=0, free=1),
    )
    monkeypatch.setattr(controller_module, "get_sync_runtime_status", lambda runner: None)

    controller._handle_status_output(json.dumps(status_payload))

    assert controller.state.sync_mode == SyncMode.AUTOMATIC


def test_disk_failure_does_not_disconnect_jotta(
    qt_app,
    monkeypatch,
    status_output: str,
) -> None:
    controller = ApplicationController()

    def fail_disk_usage(path: str):
        raise OSError("not mounted")

    monkeypatch.setattr(controller_module, "get_disk_usage", fail_disk_usage)
    monkeypatch.setattr(controller_module, "get_sync_runtime_status", lambda runner: None)

    controller._handle_status_output(status_output)

    assert controller.state.connected is True
    assert controller.state.status is not None
    assert controller.state.disk_usage is None


def test_invalid_status_marks_connection_unavailable(qt_app) -> None:
    controller = ApplicationController()
    errors = []
    controller.command_error.connect(lambda command, message: errors.append((command, message)))

    controller._handle_status_output("not json")

    assert controller.state.connected is False
    assert controller.state.sync_mode == SyncMode.UNKNOWN
    assert controller.state.sync_operation == SyncOperation.IDLE
    assert controller.state.error_message is not None
    assert errors[0][0] == "status"


def test_runtime_output_updates_activity_without_changing_mode(
    qt_app,
    monkeypatch,
    status_payload: dict,
) -> None:
    status_payload["Sync"]["Automatic"] = True
    controller = ApplicationController()
    monkeypatch.setattr(
        controller_module,
        "get_disk_usage",
        lambda path: DiskUsage(total=1, used=0, free=1),
    )
    monkeypatch.setattr(controller_module, "get_sync_runtime_status", lambda runner: None)
    controller._handle_status_output(json.dumps(status_payload))

    controller._handle_runtime_output(
        "Path: /home/user/Jotta\nMode: listening to events"
    )

    assert controller.state.sync_mode == SyncMode.AUTOMATIC
    assert controller.state.sync_activity == SyncActivity.LISTENING


def test_runtime_output_preserves_activity_status(
    qt_app,
    monkeypatch,
    status_output: str,
) -> None:
    controller = ApplicationController()
    monkeypatch.setattr(
        controller_module,
        "get_disk_usage",
        lambda path: DiskUsage(total=1, used=0, free=1),
    )
    monkeypatch.setattr(controller_module, "get_sync_runtime_status", lambda runner: None)
    controller._handle_status_output(status_output)

    controller._handle_runtime_output(
        "Path: /home/user/Jotta\nMode: manually triggered\nStatus: Checking for changes..."
    )

    assert controller.state.sync_mode == SyncMode.TRIGGERED
    assert controller.state.sync_activity == SyncActivity.TRIGGERED
    assert controller.state.sync_activity_status == "Checking for changes..."


def test_runtime_error_preserves_configured_mode(qt_app) -> None:
    controller = ApplicationController()
    controller._set_state(connected=True, sync_mode=SyncMode.TRIGGERED)

    controller._handle_error("sync_runtime_status", "runtime unavailable")

    assert controller.state.connected is True
    assert controller.state.sync_mode == SyncMode.TRIGGERED
    assert controller.state.sync_activity == SyncActivity.UNKNOWN
    assert controller.state.error_message == "runtime unavailable"


def test_failed_mutating_command_refreshes_real_state(qt_app, monkeypatch) -> None:
    controller = ApplicationController()
    refreshes = []
    controller._set_state(sync_operation=SyncOperation.STARTING)
    monkeypatch.setattr(controller, "refresh", lambda: refreshes.append(True))

    controller._handle_error("sync_start", "failed")

    assert controller.state.sync_operation == SyncOperation.IDLE
    assert controller.state.error_message == "failed"
    assert refreshes == [True]


def test_completed_mutating_command_refreshes_status(qt_app, monkeypatch) -> None:
    controller = ApplicationController()
    refreshes = []
    monkeypatch.setattr(controller, "refresh", lambda: refreshes.append(True))

    controller._handle_completed("sync_trigger", "")

    assert refreshes == [True]
