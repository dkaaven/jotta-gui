from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def selective_list(runner: JottaRunner) -> None:
    runner.run("sync_selective_list", ["sync", "selective", "list"])


def selective_add(runner: JottaRunner, folder: str) -> None:
    runner.run("sync_selective_add", ["sync", "selective", "add", folder])


def selective_remove(runner: JottaRunner, folder: str) -> None:
    runner.run("sync_selective_remove", ["sync", "selective", "rem", folder])
