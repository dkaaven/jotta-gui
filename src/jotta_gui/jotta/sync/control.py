from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def start_sync(runner: JottaRunner, *, force: bool = False) -> None:
    arguments = ["sync", "start"]
    if force:
        arguments.append("--force")
    runner.run("sync_start", arguments)


def stop_sync(runner: JottaRunner) -> None:
    runner.run("sync_stop", ["sync", "stop"])


def trigger_sync(runner: JottaRunner) -> None:
    # This command can legitimately run for a long time. JottaRunner has no short
    # command timeout and retains stdout/stderr on completion or failure.
    runner.run("sync_trigger", ["sync", "trigger"])
