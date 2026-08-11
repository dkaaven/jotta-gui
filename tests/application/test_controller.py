from __future__ import annotations

import json

import pytest

pytest.importorskip("PySide6")

import jotta_gui.application.controller as controller_module
from jotta_gui.application.controller import ApplicationController
from jotta_gui.application.state import RefreshState, SyncOperation
from jotta_gui.jotta.models import SyncActivity, SyncMode
from jotta_gui.jotta.runner import Command, CommandResult
from jotta_gui.system.storage import DiskUsage

pytestmark = pytest.mark.qt


@pytest.fixture
def application_status_payload() -> dict:
    return {
        "User": {
            "Email": "user@example.com",
            "Fullname": "Example User",
            "Hostname": "workstation",
            "Brand": "Jottacloud",
            "AccountInfo": {
                "Capacity": 1_000_000,
                "Usage": 250_000,
                "Subscription": 1,
                "SubscriptionNameLocalized": "Personal",
                "ProductNameLocalized": "Personal",
            },
            "device": {"Name": "Workstation", "Type": 12},
        },
        "Sync": {
            "Enabled": True,
            "RootPath": "/home/user/Jotta",
            "Count": {"Files": 12, "Bytes": 1_000},
            "RemoteCount": {"Files": 14, "Bytes": 1_200},
            "FolderCount": 3,
            "SyncState": 1,
        },
        "Backup": {"State": {"Enabled": {"Backups": []}}},
    }


def result(
    name: str,
    stdout: str = "",
    stderr: str = "",
    exit_code: int = 0,
) -> CommandResult:
    return CommandResult(
        command=Command(name, (name,)),
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
    )


def test_start_requests_status(qt_app, monkeypatch) -> None:
    controller = ApplicationController()
    calls = []
    monkeypatch.setattr(controller_module, "request_status", calls.append)

    controller.start()

    assert controller.state.refreshing is True
    assert calls == [controller.runner]


@pytest.mark.parametrize(
    ("method_name", "function_name", "expected_operation"),
    [
        ("start_sync", "start_sync", SyncOperation.STARTING),
        ("stop_sync", "stop_sync", SyncOperation.STOPPING),
        ("trigger_sync", "trigger_sync", SyncOperation.TRIGGERING),
    ],
)
def test_sync_action_sets_pending_operation(
    qt_app,
    monkeypatch,
    method_name: str,
    function_name: str,
    expected_operation: SyncOperation,
) -> None:
    controller = ApplicationController()
    calls = []

    if function_name == "start_sync":
        monkeypatch.setattr(
            controller_module,
            function_name,
            lambda runner, force=False: calls.append((runner, force)),
        )
    else:
        monkeypatch.setattr(
            controller_module,
            function_name,
            lambda runner: calls.append(runner),
        )

    getattr(controller, method_name)()

    assert controller.state.sync_operation == expected_operation
    assert controller.state.error is None
    assert calls


def test_duplicate_sync_action_is_ignored_while_busy(qt_app, monkeypatch) -> None:
    controller = ApplicationController()
    calls = []
    monkeypatch.setattr(controller_module, "stop_sync", calls.append)
    controller._set_state(sync_operation=SyncOperation.STARTING)

    controller.stop_sync()

    assert calls == []
    assert controller.state.sync_operation == SyncOperation.STARTING


def test_status_result_builds_provisional_snapshot_and_requests_runtime(
    qt_app,
    monkeypatch,
    application_status_payload: dict,
) -> None:
    application_status_payload["Sync"]["Automatic"] = True
    controller = ApplicationController()
    runtime_calls = []
    disk = DiskUsage(total=1_000, used=250, free=750)
    monkeypatch.setattr(controller_module, "get_disk_usage", lambda path: disk)
    monkeypatch.setattr(
        controller_module,
        "request_sync_runtime_status",
        runtime_calls.append,
    )
    controller._set_state(refresh_state=RefreshState.REFRESHING)

    controller._handle_status_result(
        result("status", json.dumps(application_status_payload))
    )

    assert controller.state.connected is True
    assert controller.state.snapshot is not None
    assert controller.state.snapshot.sync.mode == SyncMode.AUTOMATIC
    assert controller.state.snapshot.sync.activity == SyncActivity.UNKNOWN
    assert controller.state.disk_usage == disk
    assert controller.state.refreshing is True
    assert runtime_calls == [controller.runner]


def test_runtime_result_completes_snapshot(
    qt_app,
    monkeypatch,
    application_status_payload: dict,
) -> None:
    application_status_payload["Sync"]["Automatic"] = True
    controller = ApplicationController()
    monkeypatch.setattr(controller_module, "get_disk_usage", lambda path: None)
    monkeypatch.setattr(
        controller_module,
        "request_sync_runtime_status",
        lambda runner: None,
    )
    controller._set_state(
        refresh_state=RefreshState.REFRESHING,
        sync_operation=SyncOperation.STARTING,
    )
    controller._handle_status_result(
        result("status", json.dumps(application_status_payload))
    )

    controller._handle_runtime_result(
        result(
            "sync_runtime_status",
            "Path: /home/user/Jotta\n"
            "Mode: listening to events\n"
            "Status: Checking for changes...",
        )
    )

    assert controller.state.snapshot is not None
    assert controller.state.snapshot.sync.mode == SyncMode.AUTOMATIC
    assert controller.state.snapshot.sync.activity == SyncActivity.LISTENING
    assert controller.state.snapshot.sync.activity_text == "Checking for changes..."
    assert controller.state.refresh_state == RefreshState.IDLE
    assert controller.state.sync_operation == SyncOperation.IDLE


def test_disk_failure_does_not_disconnect_jotta(
    qt_app,
    monkeypatch,
    application_status_payload: dict,
) -> None:
    controller = ApplicationController()

    def fail_disk_usage(path):
        raise OSError("not mounted")

    monkeypatch.setattr(controller_module, "get_disk_usage", fail_disk_usage)
    monkeypatch.setattr(
        controller_module,
        "request_sync_runtime_status",
        lambda runner: None,
    )
    controller._set_state(refresh_state=RefreshState.REFRESHING)

    controller._handle_status_result(
        result("status", json.dumps(application_status_payload))
    )

    assert controller.state.connected is True
    assert controller.state.snapshot is not None
    assert controller.state.disk_usage is None


def test_invalid_status_marks_connection_unavailable(qt_app) -> None:
    controller = ApplicationController()
    errors = []
    controller.command_error.connect(errors.append)
    controller._set_state(refresh_state=RefreshState.REFRESHING)

    controller._handle_status_result(result("status", "not json"))

    assert controller.state.connected is False
    assert controller.state.refresh_state == RefreshState.IDLE
    assert controller.state.error is not None
    assert controller.state.error.command == "status"
    assert errors[-1].command == "status"


def test_runtime_failure_keeps_json_snapshot_and_connection(
    qt_app,
    monkeypatch,
    application_status_payload: dict,
) -> None:
    controller = ApplicationController()
    monkeypatch.setattr(controller_module, "get_disk_usage", lambda path: None)
    monkeypatch.setattr(
        controller_module,
        "request_sync_runtime_status",
        lambda runner: None,
    )
    controller._set_state(refresh_state=RefreshState.REFRESHING)
    controller._handle_status_result(
        result("status", json.dumps(application_status_payload))
    )

    controller._handle_failed(
        result("sync_runtime_status", stderr="runtime unavailable", exit_code=1)
    )

    assert controller.state.connected is True
    assert controller.state.snapshot is not None
    assert controller.state.snapshot.sync.activity == SyncActivity.UNKNOWN
    assert controller.state.refresh_state == RefreshState.IDLE
    assert controller.state.error is not None
    assert controller.state.error.message == "runtime unavailable"


def test_failed_sync_command_refreshes_real_state_and_preserves_error(
    qt_app,
    monkeypatch,
) -> None:
    controller = ApplicationController()
    refresh_calls = []
    monkeypatch.setattr(controller_module, "request_status", refresh_calls.append)
    controller._set_state(sync_operation=SyncOperation.TRIGGERING)

    controller._handle_failed(
        result("sync_trigger", stderr="case collision", exit_code=1)
    )

    assert controller.state.sync_operation == SyncOperation.IDLE
    assert controller.state.refresh_state == RefreshState.REFRESHING
    assert controller.state.error is not None
    assert controller.state.error.message == "case collision"
    assert refresh_calls == [controller.runner]


def test_completed_sync_command_keeps_pending_operation_until_verified(
    qt_app,
    monkeypatch,
) -> None:
    controller = ApplicationController()
    refresh_calls = []
    monkeypatch.setattr(controller_module, "request_status", refresh_calls.append)
    controller._set_state(sync_operation=SyncOperation.STARTING)

    controller._handle_completed(result("sync_start"))

    assert controller.state.sync_operation == SyncOperation.STARTING
    assert controller.state.refresh_state == RefreshState.REFRESHING
    assert refresh_calls == [controller.runner]


def test_clear_error(qt_app) -> None:
    controller = ApplicationController()
    controller._set_state(
        error=controller_module.ApplicationError("status", "boom")
    )

    controller.clear_error()

    assert controller.state.error is None
