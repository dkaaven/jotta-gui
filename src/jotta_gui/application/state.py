from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from jotta_gui.jotta.models import JottaSnapshot
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

    refresh_state: RefreshState = RefreshState.IDLE
    sync_operation: SyncOperation = SyncOperation.IDLE

    error: ApplicationError | None = None

    @property
    def refreshing(self) -> bool:
        return self.refresh_state == RefreshState.REFRESHING

    @property
    def sync_busy(self) -> bool:
        return self.sync_operation != SyncOperation.IDLE
