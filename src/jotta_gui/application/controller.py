from dataclasses import replace
import logging

from PySide6.QtCore import QObject, Signal

from jotta_gui.application.state import (
    ApplicationState,
    SyncActivity,
    SyncMode,
    SyncOperation,
    sync_mode_from_automatic,
)
from jotta_gui.jotta.runner import JottaRunner
from jotta_gui.jotta.status.get import get_status
from jotta_gui.jotta.status.parser import parse_status_output
from jotta_gui.jotta.sync.control import sync_start, sync_stop, sync_trigger
from jotta_gui.jotta.sync.models import SyncRuntimeState
from jotta_gui.jotta.sync.parser import parse_sync_runtime_status
from jotta_gui.jotta.sync.status import get_sync_runtime_status
from jotta_gui.system.storage import get_disk_usage

logger = logging.getLogger(__name__)


class ApplicationController(QObject):
    state_changed = Signal(object)
    command_error = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.state = ApplicationState()
        self.runner = JottaRunner(self)
        self.runner.completed.connect(self._handle_completed)
        self.runner.error.connect(self._handle_error)

    def start(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        get_status(self.runner)

    def start_sync(self) -> None:
        self._set_state(sync_operation=SyncOperation.STARTING, error_message=None)
        sync_start(self.runner)

    def stop_sync(self) -> None:
        self._set_state(sync_operation=SyncOperation.STOPPING, error_message=None)
        sync_stop(self.runner)

    def trigger_sync(self) -> None:
        self._set_state(sync_operation=SyncOperation.TRIGGERING, error_message=None)
        sync_trigger(self.runner)

    def _handle_completed(self, command: str, output: str) -> None:
        logger.info("Completed %s", command)

        if command == "status":
            self._handle_status_output(output)
            return

        if command == "sync_runtime_status":
            self._handle_runtime_output(output)
            return

        self.refresh()

    def _handle_status_output(self, output: str) -> None:
        try:
            status = parse_status_output(output)
        except (ValueError, KeyError, TypeError) as exc:
            self._handle_error("status", f"Could not parse status: {exc}")
            return

        disk_usage = None
        try:
            disk_usage = get_disk_usage(status.sync.root_path)
        except OSError as exc:
            logger.warning("Could not read disk usage for %s: %s", status.sync.root_path, exc)

        self._set_state(
            connected=True,
            status=status,
            disk_usage=disk_usage,
            sync_mode=sync_mode_from_automatic(status.sync.automatic),
            sync_operation=SyncOperation.IDLE,
            sync_activity=SyncActivity.UNKNOWN,
            sync_activity_status=None,
            error_message=None,
        )

        get_sync_runtime_status(self.runner)

    def _handle_runtime_output(self, output: str) -> None:
        status = self.state.status
        if status is None:
            return

        runtime = parse_sync_runtime_status(output, status.sync.root_path)
        activity_map = {
            SyncRuntimeState.LISTENING: SyncActivity.LISTENING,
            SyncRuntimeState.TRIGGERED: SyncActivity.TRIGGERED,
            SyncRuntimeState.UNKNOWN: SyncActivity.UNKNOWN,
        }
        self._set_state(
            sync_activity=activity_map[runtime.state],
            sync_activity_status=runtime.status,
        )

        if runtime.mode:
            logger.info("Sync runtime mode: %s", runtime.mode)
        if runtime.status:
            logger.info("Sync runtime status: %s", runtime.status)

    def _handle_error(self, command: str, message: str) -> None:
        logger.error("Jotta error [%s]: %s", command, message)
        self.command_error.emit(command, message)

        if command == "status":
            self._set_state(
                connected=False,
                sync_mode=SyncMode.UNKNOWN,
                sync_operation=SyncOperation.IDLE,
                sync_activity=SyncActivity.UNKNOWN,
                sync_activity_status=None,
                error_message=message,
            )
            return

        if command == "sync_runtime_status":
            self._set_state(
                sync_activity=SyncActivity.UNKNOWN,
                sync_activity_status=None,
                error_message=message,
            )
            return

        self._set_state(
            sync_operation=SyncOperation.IDLE,
            error_message=message,
        )
        self.refresh()

    def _set_state(self, **changes: object) -> None:
        self.state = replace(self.state, **changes)
        self.state_changed.emit(self.state)
