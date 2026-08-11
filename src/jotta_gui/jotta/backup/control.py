from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def add_backup(
    runner: JottaRunner,
    path: str,
    *,
    name: str | None = None,
    confirm_existing: bool = False,
) -> None:
    arguments = ["add", path]
    if name:
        arguments.extend(["--name", name])
    if confirm_existing:
        arguments.append("--confirmexisting")
    runner.run("backup_add", arguments)


def remove_backup(runner: JottaRunner, path: str) -> None:
    runner.run("backup_remove", ["rem", path])


def scan_backups(runner: JottaRunner, name: str | None = None) -> None:
    arguments = ["scan"]
    if name:
        arguments.append(name)
    runner.run("backup_scan", arguments)


def pause_backup(runner: JottaRunner, path: str) -> None:
    runner.run("backup_pause", ["pause", "--backup", path])


def resume_backup(runner: JottaRunner, path: str) -> None:
    runner.run("backup_resume", ["resume", "--backup", path])
