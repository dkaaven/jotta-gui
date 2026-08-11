from __future__ import annotations

from dataclasses import replace
import logging

from PySide6.QtCore import QObject, Signal

from jotta_gui.application.state import (
    ApplicationError,
    ApplicationState,
    BackupIgnoreOperation,
    BackupIgnoreState,
    RefreshState,
    SyncOperation,
    VersionCheckState,
)
from jotta_gui.jotta.backup.ignores import add_ignore, list_ignores, remove_ignore
from jotta_gui.jotta.models import JottaSnapshot
from jotta_gui.jotta.runner import CommandResult, JottaRunner
from jotta_gui.jotta.snapshot import build_snapshot
from jotta_gui.jotta.status.models import CliStatus
from jotta_gui.jotta.status.parser import parse_status_output
from jotta_gui.jotta.status.query import request_status
from jotta_gui.jotta.sync.control import start_sync, stop_sync, trigger_sync
from jotta_gui.jotta.sync.parser import parse_sync_runtime_status
from jotta_gui.jotta.sync.query import request_sync_runtime_status
from jotta_gui.jotta.version import parse_version_output, request_version
from jotta_gui.system.storage import DiskUsage, get_disk_usage

logger = logging.getLogger(__name__)


class ApplicationController(QObject):
    """Coordinates application workflows without owning Jotta semantics.

    The controller never derives Sync mode or activity itself. It asks the Jotta
    layer to parse CLI observations and to build a stable ``JottaSnapshot``.
    """

    state_changed = Signal(object)  # ApplicationState
    command_error = Signal(object)  # ApplicationError

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.state = ApplicationState()
        self.runner = JottaRunner(self)
        self.runner.completed.connect(self._handle_completed)
        self.runner.failed.connect(self._handle_failed)

        # Raw CLI status is retained only while collecting the second, non-atomic
        # human-readable runtime observation for the same refresh workflow.
        self._status_observation: CliStatus | None = None
        self._preserve_error_on_refresh = False

    def start(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        """Refresh Jotta state and perform the independent version check."""

        self._request_refresh(preserve_error=False)
        self.check_version()

    def check_version(self) -> None:
        """Request read-only local/remote version information from jotta-cli."""

        if self.state.version_checking:
            return
        self._set_state(
            version_check_state=VersionCheckState.CHECKING,
            version_error=None,
        )
        request_version(self.runner)

    def start_sync(self, *, force: bool = False) -> None:
        if self.state.sync_busy:
            return
        self._set_state(
            sync_operation=SyncOperation.STARTING,
            error=None,
        )
        start_sync(self.runner, force=force)

    def stop_sync(self) -> None:
        if self.state.sync_busy:
            return
        self._set_state(
            sync_operation=SyncOperation.STOPPING,
            error=None,
        )
        stop_sync(self.runner)

    def trigger_sync(self) -> None:
        if self.state.sync_busy:
            return
        self._set_state(
            sync_operation=SyncOperation.TRIGGERING,
            error=None,
        )
        trigger_sync(self.runner)

    def clear_error(self) -> None:
        if self.state.error is not None:
            self._set_state(error=None)

    def load_backup_ignores(self, backup_name: str) -> None:
        """Request the authoritative ignore list for one configured backup."""

        backup_name = backup_name.strip()
        if not backup_name or self.state.backup_ignores.busy:
            return

        self._set_state(
            backup_ignores=BackupIgnoreState(
                backup_name=backup_name,
                output=(
                    self.state.backup_ignores.output
                    if self.state.backup_ignores.backup_name == backup_name
                    else None
                ),
                operation=BackupIgnoreOperation.LOADING,
            ),
            error=None,
        )
        list_ignores(self.runner, backup_name)

    def add_backup_ignore(self, backup_name: str, pattern: str) -> None:
        """Add one ignore pattern to a backup, then re-read Jotta's rule list."""

        backup_name = backup_name.strip()
        pattern = pattern.strip()
        if not backup_name or not pattern or self.state.backup_ignores.busy:
            return

        self._set_state(
            backup_ignores=BackupIgnoreState(
                backup_name=backup_name,
                output=(
                    self.state.backup_ignores.output
                    if self.state.backup_ignores.backup_name == backup_name
                    else None
                ),
                operation=BackupIgnoreOperation.ADDING,
            ),
            error=None,
        )
        add_ignore(self.runner, pattern, backup_name)

    def remove_backup_ignore(self, backup_name: str, pattern: str) -> None:
        """Remove one exact ignore pattern, then re-read Jotta's rule list."""

        backup_name = backup_name.strip()
        pattern = pattern.strip()
        if not backup_name or not pattern or self.state.backup_ignores.busy:
            return

        self._set_state(
            backup_ignores=BackupIgnoreState(
                backup_name=backup_name,
                output=(
                    self.state.backup_ignores.output
                    if self.state.backup_ignores.backup_name == backup_name
                    else None
                ),
                operation=BackupIgnoreOperation.REMOVING,
            ),
            error=None,
        )
        remove_ignore(self.runner, pattern, backup_name)

    def _request_refresh(self, *, preserve_error: bool) -> None:
        # Avoid stacking duplicate status/runtime refresh pairs. Mutating commands
        # are already serialized by JottaRunner and call this only after completion.
        if self.state.refreshing:
            return

        self._status_observation = None
        self._preserve_error_on_refresh = preserve_error
        changes: dict[str, object] = {"refresh_state": RefreshState.REFRESHING}
        if not preserve_error:
            changes["error"] = None
        self._set_state(**changes)
        request_status(self.runner)

    def _handle_completed(self, result: CommandResult) -> None:
        command = result.command.name
        logger.info("Completed %s", command)

        if command == "status":
            self._handle_status_result(result)
            return

        if command == "sync_runtime_status":
            self._handle_runtime_result(result)
            return

        if command == "version":
            self._handle_version_result(result)
            return

        if command == "backup_ignores_list":
            current = self.state.backup_ignores
            # The exact stream used by ``ignores list`` has not yet been captured.
            # Prefer normal stdout, but retain successful stderr output as a
            # compatibility fallback instead of presenting an empty rule list.
            output = result.stdout or result.stderr
            self._set_state(
                backup_ignores=BackupIgnoreState(
                    backup_name=current.backup_name,
                    output=output,
                    operation=BackupIgnoreOperation.IDLE,
                )
            )
            return

        if command in {"backup_ignores_add", "backup_ignores_remove"}:
            current = self.state.backup_ignores
            if current.backup_name:
                self._set_state(
                    backup_ignores=BackupIgnoreState(
                        backup_name=current.backup_name,
                        output=current.output,
                        operation=BackupIgnoreOperation.LOADING,
                    )
                )
                list_ignores(self.runner, current.backup_name)
            else:
                self._set_state(backup_ignores=BackupIgnoreState())
            return

        if command in {"sync_start", "sync_stop", "sync_trigger"}:
            # A successful command only means the CLI invocation completed. The
            # requested state is not trusted until status is read back.
            self._request_refresh(preserve_error=False)
            return

        # Unknown successful commands may still have changed status. Refreshing is
        # the safest generic behavior while this controller remains small.
        self._request_refresh(preserve_error=False)


    def _handle_version_result(self, result: CommandResult) -> None:
        try:
            output = "\n".join(part for part in (result.stdout, result.stderr) if part)
            version = parse_version_output(output)
        except ValueError as exc:
            logger.warning("Could not parse jotta-cli version output: %s", exc)
            self._set_state(
                version_check_state=VersionCheckState.IDLE,
                version_error=str(exc),
            )
            return

        self._set_state(
            version=version,
            version_check_state=VersionCheckState.IDLE,
            version_error=None,
        )

    def _handle_status_result(self, result: CommandResult) -> None:
        try:
            status = parse_status_output(result.stdout)
        except (ValueError, KeyError, TypeError) as exc:
            self._fail_refresh(
                ApplicationError(
                    command="status",
                    message=f"Could not parse status: {exc}",
                    exit_code=result.exit_code,
                ),
                disconnect=True,
            )
            return

        self._status_observation = status
        snapshot = build_snapshot(status)
        disk_usage = self._read_disk_usage(snapshot)

        changes: dict[str, object] = {
            "connected": True,
            "snapshot": snapshot,
            "disk_usage": disk_usage,
        }
        if not self._preserve_error_on_refresh:
            changes["error"] = None
        self._set_state(**changes)

        # Runtime status is deliberately a second observation. Keep REFRESHING set
        # until it completes (or fails) so the UI knows the snapshot is provisional.
        request_sync_runtime_status(self.runner)

    def _handle_runtime_result(self, result: CommandResult) -> None:
        status = self._status_observation
        if status is None:
            # A stale/out-of-sequence response should not corrupt the last snapshot.
            self._set_state(
                refresh_state=RefreshState.IDLE,
                sync_operation=SyncOperation.IDLE,
            )
            return

        runtime = parse_sync_runtime_status(
            result.stdout,
            status.sync.root_path,
        )
        snapshot = build_snapshot(status, runtime)

        changes: dict[str, object] = {
            "connected": True,
            "snapshot": snapshot,
            "refresh_state": RefreshState.IDLE,
            "sync_operation": SyncOperation.IDLE,
        }
        if not self._preserve_error_on_refresh:
            changes["error"] = None
        self._set_state(**changes)
        self._finish_refresh()

    def _handle_failed(self, result: CommandResult) -> None:
        command = result.command.name
        error = ApplicationError(
            command=command,
            message=result.error_message or "jotta-cli failed",
            exit_code=result.exit_code,
        )
        logger.error("Jotta error [%s]: %s", command, error.message)

        if command == "status":
            self._fail_refresh(error, disconnect=True)
            return

        if command == "version":
            logger.warning("Version check failed: %s", error.message)
            self._set_state(
                version_check_state=VersionCheckState.IDLE,
                version_error=error.message,
            )
            return

        self.command_error.emit(error)

        if command in {
            "backup_ignores_list",
            "backup_ignores_add",
            "backup_ignores_remove",
        }:
            current = self.state.backup_ignores
            self._set_state(
                backup_ignores=BackupIgnoreState(
                    backup_name=current.backup_name,
                    output=current.output,
                    operation=BackupIgnoreOperation.IDLE,
                ),
                error=error,
            )
            return

        if command == "sync_runtime_status":
            # JSON status already succeeded, so Jotta is still connected. Runtime
            # evidence simply remains UNKNOWN in the provisional snapshot. If this
            # probe belongs to a refresh after a failed mutation, keep that original
            # mutation error as the user-facing failure.
            surfaced_error = (
                self.state.error
                if self._preserve_error_on_refresh and self.state.error is not None
                else error
            )
            self._set_state(
                connected=True,
                refresh_state=RefreshState.IDLE,
                sync_operation=SyncOperation.IDLE,
                error=surfaced_error,
            )
            self._finish_refresh()
            return

        if command in {"sync_start", "sync_stop", "sync_trigger"}:
            # Preserve the command failure while refreshing authoritative state.
            self._set_state(
                sync_operation=SyncOperation.IDLE,
                error=error,
            )
            self._request_refresh(preserve_error=True)
            return

        self._set_state(error=error)

    def _fail_refresh(
        self,
        error: ApplicationError,
        *,
        disconnect: bool,
    ) -> None:
        logger.error("Refresh failed [%s]: %s", error.command, error.message)
        self.command_error.emit(error)
        self._set_state(
            connected=False if disconnect else self.state.connected,
            refresh_state=RefreshState.IDLE,
            sync_operation=SyncOperation.IDLE,
            error=error,
        )
        self._finish_refresh()

    def _read_disk_usage(self, snapshot: JottaSnapshot) -> DiskUsage | None:
        root = snapshot.sync.root_path
        if root is None:
            return None

        try:
            return get_disk_usage(root)
        except OSError as exc:
            logger.warning("Could not read disk usage for %s: %s", root, exc)
            return None

    def _finish_refresh(self) -> None:
        self._status_observation = None
        self._preserve_error_on_refresh = False

    def _set_state(self, **changes: object) -> None:
        self.state = replace(self.state, **changes)
        self.state_changed.emit(self.state)
