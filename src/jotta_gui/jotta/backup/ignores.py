from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def list_ignores(runner: JottaRunner, backup: str | None = None) -> None:
    arguments = ["ignores", "list"]
    if backup:
        arguments.extend(["--backup", backup])
    runner.run("backup_ignores_list", arguments)


def add_ignore(
    runner: JottaRunner,
    pattern: str,
    backup: str | None = None,
) -> None:
    arguments = ["ignores", "add", "--pattern", pattern]
    if backup:
        arguments.extend(["--backup", backup])
    runner.run("backup_ignores_add", arguments)


def remove_ignore(runner: JottaRunner, pattern: str, backup: str) -> None:
    runner.run(
        "backup_ignores_remove",
        ["ignores", "rem", "--pattern", pattern, "--backup", backup],
    )


def test_ignore(runner: JottaRunner, pattern: str, path: str) -> None:
    runner.run(
        "backup_ignores_test",
        ["ignores", "test", "--pattern", pattern, "--path", path],
    )
