from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def ignores_list(runner: JottaRunner, backup: str) -> None:
    runner.run("backup_ignores_list", ["ignores", "list", "--backup", backup])


def ignores_add(runner: JottaRunner, backup: str, pattern: str) -> None:
    runner.run(
        "backup_ignores_add",
        ["ignores", "add", "--pattern", pattern, "--backup", backup],
    )
