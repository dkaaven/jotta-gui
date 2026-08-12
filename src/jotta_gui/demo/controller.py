from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QObject, Signal

from jotta_gui.application.state import (
    ApplicationState,
    BackupIgnoreState,
)
from jotta_gui.jotta.config import ConfigEntry, JottaConfig
from jotta_gui.jotta.models import SyncActivity, SyncMode

from .data import DEMO_IGNORE_RULES, build_demo_state, format_demo_ignore_rules


class DemoController(QObject):
    """In-memory controller used by ``jotta-gui --demo``.

    It deliberately has the same public workflow methods used by ``MainWindow`` but
    never constructs ``JottaRunner`` and never invokes ``jotta-cli``.
    """

    state_changed = Signal(object)  # ApplicationState
    command_error = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.state = build_demo_state()
        self._ignore_rules = {
            name: list(patterns) for name, patterns in DEMO_IGNORE_RULES.items()
        }

    def start(self) -> None:
        self._emit_state()

    def refresh(self) -> None:
        # Demo data is deterministic. Re-emit the current in-memory state instead
        # of resetting user interactions or consulting the real CLI.
        self._emit_state()

    def check_version(self) -> None:
        self._emit_state()

    def load_config(self) -> None:
        self._emit_state()

    def set_config(self, setting: str, value: str) -> None:
        setting = setting.strip()
        value = value.strip()
        if not setting or not value or self.state.config is None:
            return

        entries: list[ConfigEntry] = []
        found = False
        for entry in self.state.config.entries:
            if entry.name.casefold() == setting.casefold():
                entries.append(ConfigEntry(name=entry.name, value=value))
                found = True
            else:
                entries.append(entry)
        if not found:
            return

        config = JottaConfig(
            entries=tuple(entries),
            raw_output="\n".join(f"{entry.name} : {entry.value}" for entry in entries),
        )
        self._set_state(config=config, config_error=None)

    def start_sync(self, *, force: bool = False) -> None:
        del force
        self._replace_sync(
            mode=SyncMode.AUTOMATIC,
            activity=SyncActivity.LISTENING,
            activity_text="Listening for filesystem changes",
            runtime_mode_text="listening to events",
        )

    def stop_sync(self) -> None:
        self._replace_sync(
            mode=SyncMode.TRIGGERED,
            activity=SyncActivity.UNKNOWN,
            activity_text="Continuous Sync stopped; ready for manual Sync",
            runtime_mode_text=None,
        )

    def trigger_sync(self) -> None:
        self._replace_sync(
            mode=SyncMode.TRIGGERED,
            activity=SyncActivity.TRIGGERED,
            activity_text="Demo synchronization completed",
            runtime_mode_text="manually triggered",
        )

    def clear_error(self) -> None:
        if self.state.error is not None:
            self._set_state(error=None)

    def load_backup_ignores(self, backup_name: str) -> None:
        backup_name = backup_name.strip()
        if not backup_name:
            return
        rules = tuple(self._ignore_rules.get(backup_name, ()))
        self._set_state(
            backup_ignores=BackupIgnoreState(
                backup_name=backup_name,
                output=format_demo_ignore_rules(backup_name, rules),
            )
        )

    def add_backup_ignore(self, backup_name: str, pattern: str) -> None:
        backup_name = backup_name.strip()
        pattern = pattern.strip()
        if not backup_name or not pattern:
            return
        rules = self._ignore_rules.setdefault(backup_name, [])
        if pattern not in rules:
            rules.append(pattern)
        self.load_backup_ignores(backup_name)

    def remove_backup_ignore(self, backup_name: str, pattern: str) -> None:
        backup_name = backup_name.strip()
        pattern = pattern.strip()
        if not backup_name or not pattern:
            return
        rules = self._ignore_rules.setdefault(backup_name, [])
        if pattern in rules:
            rules.remove(pattern)
        self.load_backup_ignores(backup_name)

    def _replace_sync(
        self,
        *,
        mode: SyncMode,
        activity: SyncActivity,
        activity_text: str,
        runtime_mode_text: str | None,
    ) -> None:
        snapshot = self.state.snapshot
        if snapshot is None:
            return
        sync = replace(
            snapshot.sync,
            mode=mode,
            activity=activity,
            activity_text=activity_text,
            runtime_mode_text=runtime_mode_text,
        )
        self._set_state(snapshot=replace(snapshot, sync=sync))

    def _set_state(self, **changes: object) -> None:
        self.state = replace(self.state, **changes)
        self._emit_state()

    def _emit_state(self) -> None:
        self.state_changed.emit(self.state)
