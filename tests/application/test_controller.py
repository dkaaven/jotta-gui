from __future__ import annotations

import json

import pytest

pytest.importorskip("PySide6")

import jotta_gui.application.controller as controller_module
from jotta_gui.application.controller import ApplicationController
from jotta_gui.application.state import (
    BackupIgnoreOperation,
    BackupIgnoreState,
    RefreshState,
    SyncOperation,
    VersionCheckState,
)
from jotta_gui.jotta.models import SyncActivity, SyncMode
from jotta_gui.jotta.runner import Command, CommandResult
from jotta_gui.jotta.version import VersionInfo
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


def test_start_requests_status_and_version(qt_app, monkeypatch) -> None:
    controller = ApplicationController()
    status_calls = []
    version_calls = []
    monkeypatch.setattr(controller_module, "request_status", status_calls.append)
    monkeypatch.setattr(controller_module, "request_version", version_calls.append)

    controller.start()

    assert controller.state.refreshing is True
    assert controller.state.version_checking is True
    assert status_calls == [controller.runner]
    assert version_calls == [controller.runner]


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


def test_load_backup_ignores_requests_authoritative_list(qt_app, monkeypatch) -> None:
    controller = ApplicationController()
    calls = []
    monkeypatch.setattr(
        controller_module,
        "list_ignores",
        lambda runner, backup: calls.append((runner, backup)),
    )

    controller.load_backup_ignores("Documents")

    assert controller.state.backup_ignores.backup_name == "Documents"
    assert controller.state.backup_ignores.operation == BackupIgnoreOperation.LOADING
    assert calls == [(controller.runner, "Documents")]


def test_ignore_list_result_preserves_cli_output_verbatim(qt_app) -> None:
    controller = ApplicationController()
    controller._set_state(
        backup_ignores=BackupIgnoreState(
            backup_name="Documents",
            operation=BackupIgnoreOperation.LOADING,
        )
    )
    output = "Backup: Documents\n  **/.git\n  **/.venv"

    controller._handle_completed(result("backup_ignores_list", output))

    assert controller.state.backup_ignores.output == output
    assert controller.state.backup_ignores.operation == BackupIgnoreOperation.IDLE


def test_ignore_list_result_falls_back_to_successful_stderr(qt_app) -> None:
    controller = ApplicationController()
    controller._set_state(
        backup_ignores=BackupIgnoreState(
            backup_name="Documents",
            operation=BackupIgnoreOperation.LOADING,
        )
    )
    output = "Backup: Documents\n  **/.git\n  **/.venv"

    controller._handle_completed(
        result("backup_ignores_list", stdout="", stderr=output)
    )

    assert controller.state.backup_ignores.output == output
    assert controller.state.backup_ignores.operation == BackupIgnoreOperation.IDLE


def test_add_backup_ignore_requests_add_then_relist(qt_app, monkeypatch) -> None:
    controller = ApplicationController()
    add_calls = []
    list_calls = []
    monkeypatch.setattr(
        controller_module,
        "add_ignore",
        lambda runner, pattern, backup: add_calls.append((runner, pattern, backup)),
    )
    monkeypatch.setattr(
        controller_module,
        "list_ignores",
        lambda runner, backup: list_calls.append((runner, backup)),
    )

    controller.add_backup_ignore("Documents", "**/.git")

    assert controller.state.backup_ignores.operation == BackupIgnoreOperation.ADDING
    assert add_calls == [(controller.runner, "**/.git", "Documents")]

    controller._handle_completed(result("backup_ignores_add"))

    assert controller.state.backup_ignores.operation == BackupIgnoreOperation.LOADING
    assert list_calls == [(controller.runner, "Documents")]


def test_ignore_command_failure_stops_rule_workflow(qt_app) -> None:
    controller = ApplicationController()
    controller._set_state(
        backup_ignores=BackupIgnoreState(
            backup_name="Documents",
            output="old output",
            operation=BackupIgnoreOperation.ADDING,
        )
    )

    controller._handle_failed(
        result("backup_ignores_add", stderr="invalid pattern", exit_code=1)
    )

    assert controller.state.backup_ignores.operation == BackupIgnoreOperation.IDLE
    assert controller.state.backup_ignores.output == "old output"
    assert controller.state.error is not None
    assert controller.state.error.message == "invalid pattern"


def test_remove_backup_ignore_requests_remove_then_relist(qt_app, monkeypatch) -> None:
    controller = ApplicationController()
    remove_calls = []
    list_calls = []
    monkeypatch.setattr(
        controller_module,
        "remove_ignore",
        lambda runner, pattern, backup: remove_calls.append((runner, pattern, backup)),
    )
    monkeypatch.setattr(
        controller_module,
        "list_ignores",
        lambda runner, backup: list_calls.append((runner, backup)),
    )

    controller.remove_backup_ignore("Documents", "**/.git")

    assert controller.state.backup_ignores.operation == BackupIgnoreOperation.REMOVING
    assert remove_calls == [(controller.runner, "**/.git", "Documents")]

    controller._handle_completed(result("backup_ignores_remove"))

    assert controller.state.backup_ignores.operation == BackupIgnoreOperation.LOADING
    assert list_calls == [(controller.runner, "Documents")]


def test_version_result_updates_read_only_version_state(qt_app) -> None:
    controller = ApplicationController()
    controller._set_state(version_check_state=VersionCheckState.CHECKING)

    controller._handle_completed(
        result(
            "version",
            "jottad version    : 0.17.159692\n"
            "remote version    : 0.17.176206\n"
            "jotta-cli version : 0.17.159692\n"
            "release notes     : https://docs.example/release",
        )
    )

    assert controller.state.version == VersionInfo(
        cli_version="0.17.159692",
        daemon_version="0.17.159692",
        remote_version="0.17.176206",
        release_notes_url="https://docs.example/release",
    )
    assert controller.state.version.update_available is True
    assert controller.state.version_check_state == VersionCheckState.IDLE
    assert controller.state.version_error is None


def test_version_failure_does_not_surface_global_application_error(qt_app) -> None:
    controller = ApplicationController()
    errors = []
    controller.command_error.connect(errors.append)
    controller._set_state(version_check_state=VersionCheckState.CHECKING)

    controller._handle_failed(
        result("version", stderr="version unavailable", exit_code=1)
    )

    assert controller.state.version_check_state == VersionCheckState.IDLE
    assert controller.state.version_error == "version unavailable"
    assert controller.state.error is None
    assert errors == []


def test_invalid_version_output_becomes_unknown_without_global_error(qt_app) -> None:
    controller = ApplicationController()
    controller._set_state(version_check_state=VersionCheckState.CHECKING)

    controller._handle_completed(result("version", "unexpected output"))

    assert controller.state.version is None
    assert controller.state.version_check_state == VersionCheckState.IDLE
    assert "no recognized version fields" in (controller.state.version_error or "")
    assert controller.state.error is None
