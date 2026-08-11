from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def request_status(runner: JottaRunner) -> None:
    runner.run("status", ["status", "--json"])
