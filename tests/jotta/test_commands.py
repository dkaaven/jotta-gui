import pytest

from jotta_gui.jotta.backup import (
    add_backup,
    add_ignore,
    list_ignores,
    pause_backup,
    remove_backup,
    remove_ignore,
    resume_backup,
    scan_backups,
    test_ignore as run_ignore_test,
)
from jotta_gui.jotta.status.query import request_status
from jotta_gui.jotta.sync.control import start_sync, stop_sync, trigger_sync
from jotta_gui.jotta.sync.query import request_sync_runtime_status
from jotta_gui.jotta.sync.selective import list_selective_sync
from jotta_gui.jotta.version import request_version


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str] | tuple[str, ...]]] = []

    def run(self, name: str, arguments: list[str] | tuple[str, ...]) -> None:
        self.calls.append((name, arguments))


@pytest.mark.parametrize(
    ("invoke", "expected"),
    [
        (lambda r: request_status(r), ("status", ["status", "--json"])),
        (lambda r: request_version(r), ("version", ["version"])),
        (
            lambda r: request_sync_runtime_status(r),
            ("sync_runtime_status", ["status"]),
        ),
        (lambda r: start_sync(r), ("sync_start", ["sync", "start"])),
        (
            lambda r: start_sync(r, force=True),
            ("sync_start", ["sync", "start", "--force"]),
        ),
        (lambda r: stop_sync(r), ("sync_stop", ["sync", "stop"])),
        (lambda r: trigger_sync(r), ("sync_trigger", ["sync", "trigger"])),
        (
            lambda r: list_selective_sync(r),
            ("sync_selective_list", ["sync", "selective", "list"]),
        ),
        (
            lambda r: add_backup(r, "/data/Documents"),
            ("backup_add", ["add", "/data/Documents"]),
        ),
        (
            lambda r: add_backup(
                r,
                "/data/Documents",
                name="Docs",
                confirm_existing=True,
            ),
            (
                "backup_add",
                ["add", "/data/Documents", "--name", "Docs", "--confirmexisting"],
            ),
        ),
        (
            lambda r: remove_backup(r, "/data/Documents"),
            ("backup_remove", ["rem", "/data/Documents"]),
        ),
        (lambda r: scan_backups(r), ("backup_scan", ["scan"])),
        (
            lambda r: scan_backups(r, "Documents"),
            ("backup_scan", ["scan", "Documents"]),
        ),
        (
            lambda r: pause_backup(r, "/data/Documents"),
            ("backup_pause", ["pause", "--backup", "/data/Documents"]),
        ),
        (
            lambda r: resume_backup(r, "/data/Documents"),
            ("backup_resume", ["resume", "--backup", "/data/Documents"]),
        ),
        (
            lambda r: list_ignores(r),
            ("backup_ignores_list", ["ignores", "list"]),
        ),
        (
            lambda r: list_ignores(r, "Documents"),
            ("backup_ignores_list", ["ignores", "list", "--backup", "Documents"]),
        ),
        (
            lambda r: add_ignore(r, "**/.git", "Documents"),
            (
                "backup_ignores_add",
                ["ignores", "add", "--pattern", "**/.git", "--backup", "Documents"],
            ),
        ),
        (
            lambda r: remove_ignore(r, "**/.git", "Documents"),
            (
                "backup_ignores_remove",
                ["ignores", "rem", "--pattern", "**/.git", "--backup", "Documents"],
            ),
        ),
        (
            lambda r: run_ignore_test(r, "**/.git", "src/.git"),
            (
                "backup_ignores_test",
                ["ignores", "test", "--pattern", "**/.git", "--path", "src/.git"],
            ),
        ),
    ],
)
def test_command_wrapper_builds_expected_invocation(invoke, expected) -> None:
    runner = RecordingRunner()

    invoke(runner)

    assert runner.calls == [expected]
