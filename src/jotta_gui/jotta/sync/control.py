from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def sync_start(runner: JottaRunner) -> None:
    runner.run("sync_start", ["sync", "start"])


def sync_stop(runner: JottaRunner) -> None:
    runner.run("sync_stop", ["sync", "stop"])


def sync_trigger(runner: JottaRunner) -> None:
    runner.run("sync_trigger", ["sync", "trigger"])
