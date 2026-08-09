from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def backup_add(runner: JottaRunner, path: str) -> None:
    runner.run("backup_add", ["add", path])


def backup_remove(runner: JottaRunner, path: str) -> None:
    runner.run("backup_remove", ["rem", path])
