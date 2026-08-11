from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from jotta_gui.jotta.config import JottaConfig
from jotta_gui.jotta.models import JottaSnapshot
from jotta_gui.jotta.version import VersionInfo
from jotta_gui.system.storage import DiskUsage


class RefreshState(StrEnum):
    """Application-owned state for a status refresh workflow."""

    IDLE = "idle"
    REFRESHING = "refreshing"


class SyncOperation(StrEnum):
    """User-requested Sync operation currently in flight."""

    IDLE = "idle"
    STARTING = "starting"
    STOPPING = "stopping"
    TRIGGERING = "triggering"


class VersionCheckState(StrEnum):
    """Application-owned state for the read-only version check."""

    IDLE = "idle"
    CHECKING = "checking"


class ConfigOperation(StrEnum):
    """Application-owned state for daemon configuration workflows."""

    IDLE = "idle"
    LOADING = "loading"
    SAVING = "saving"


class BackupIgnoreOperation(StrEnum):
    """Application-owned workflow state for Backup ignore rules."""

    IDLE = "idle"
    LOADING = "loading"
    ADDING = "adding"
    REMOVING = "removing"


@dataclass(frozen=True, slots=True)
class BackupIgnoreState:
    """Ignore-rule state for the currently requested backup.

    ``output`` intentionally stores Jotta's command output verbatim until the exact
    ``ignores list`` stream/format contract has been captured and a parser can be
    added.
    """

    backup_name: str | None = None
    output: str | None = None
    operation: BackupIgnoreOperation = BackupIgnoreOperation.IDLE

    @property
    def busy(self) -> bool:
        return self.operation != BackupIgnoreOperation.IDLE


@dataclass(frozen=True, slots=True)
class ApplicationError:
    """Failure surfaced by an application workflow.

    The domain snapshot remains separate from failures. A failed runtime observation,
    for example, must not mutate the configured Sync mode into an invented state.
    """

    command: str
    message: str
    exit_code: int | None = None


@dataclass(frozen=True, slots=True)
class ApplicationState:
    """Immutable state consumed by the UI.

    Jottacloud facts live in ``snapshot``. Everything else here belongs to the
    application itself: connectivity, pending workflows, local disk information,
    and the latest surfaced error.
    """

    connected: bool = False
    snapshot: JottaSnapshot | None = None
    disk_usage: DiskUsage | None = None
    version: VersionInfo | None = None
    version_check_state: VersionCheckState = VersionCheckState.IDLE
    version_error: str | None = None

    config: JottaConfig | None = None
    config_operation: ConfigOperation = ConfigOperation.IDLE
    config_saving_setting: str | None = None
    config_error: str | None = None

    refresh_state: RefreshState = RefreshState.IDLE
    sync_operation: SyncOperation = SyncOperation.IDLE
    backup_ignores: BackupIgnoreState = field(default_factory=BackupIgnoreState)

    error: ApplicationError | None = None

    @property
    def refreshing(self) -> bool:
        return self.refresh_state == RefreshState.REFRESHING

    @property
    def sync_busy(self) -> bool:
        return self.sync_operation != SyncOperation.IDLE

    @property
    def version_checking(self) -> bool:
        return self.version_check_state == VersionCheckState.CHECKING

    @property
    def config_busy(self) -> bool:
        return self.config_operation != ConfigOperation.IDLE
