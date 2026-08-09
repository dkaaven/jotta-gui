import pytest

from jotta_gui.jotta.backup.control import backup_add, backup_remove
from jotta_gui.jotta.backup.ignores import ignores_add, ignores_list
from jotta_gui.jotta.status.get import get_status
from jotta_gui.jotta.sync.control import sync_start, sync_stop, sync_trigger
from jotta_gui.jotta.sync.selective import (
    selective_add,
    selective_list,
    selective_remove,
)
from jotta_gui.jotta.sync.status import get_sync_runtime_status


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def run(self, name: str, arguments: list[str]) -> None:
        self.calls.append((name, arguments))


@pytest.mark.parametrize(
    ("invoke", "expected"),
    [
        (lambda runner: get_status(runner), ("status", ["status", "--json"])),
        (
            lambda runner: get_sync_runtime_status(runner),
            ("sync_runtime_status", ["status"]),
        ),
        (lambda runner: sync_start(runner), ("sync_start", ["sync", "start"])),
        (lambda runner: sync_stop(runner), ("sync_stop", ["sync", "stop"])),
        (
            lambda runner: sync_trigger(runner),
            ("sync_trigger", ["sync", "trigger"]),
        ),
        (
            lambda runner: selective_list(runner),
            ("sync_selective_list", ["sync", "selective", "list"]),
        ),
        (
            lambda runner: selective_add(runner, "Photos"),
            ("sync_selective_add", ["sync", "selective", "add", "Photos"]),
        ),
        (
            lambda runner: selective_remove(runner, "Photos"),
            ("sync_selective_remove", ["sync", "selective", "rem", "Photos"]),
        ),
        (
            lambda runner: backup_add(runner, "/data/Documents"),
            ("backup_add", ["add", "/data/Documents"]),
        ),
        (
            lambda runner: backup_remove(runner, "/data/Documents"),
            ("backup_remove", ["rem", "/data/Documents"]),
        ),
        (
            lambda runner: ignores_list(runner, "Documents"),
            ("backup_ignores_list", ["ignores", "list", "--backup", "Documents"]),
        ),
        (
            lambda runner: ignores_add(runner, "Documents", "*.tmp"),
            (
                "backup_ignores_add",
                [
                    "ignores",
                    "add",
                    "--pattern",
                    "*.tmp",
                    "--backup",
                    "Documents",
                ],
            ),
        ),
    ],
)
def test_feature_builds_expected_command(invoke, expected) -> None:
    runner = RecordingRunner()

    invoke(runner)

    assert runner.calls == [expected]
