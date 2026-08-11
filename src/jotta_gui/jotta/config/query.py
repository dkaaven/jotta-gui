from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def request_config(runner: JottaRunner) -> None:
    runner.run("config_list", ["config"])


def set_config_value(runner: JottaRunner, setting: str, value: str) -> None:
    runner.run("config_set", ["config", setting, value])
