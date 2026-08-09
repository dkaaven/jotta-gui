from dataclasses import dataclass
from enum import StrEnum

from jotta_gui.jotta.status.models import JottaStatus
from jotta_gui.system.storage import DiskUsage


class SyncState(StrEnum):
    UNKNOWN = "unknown"
    ACTIVE = "active"
    INACTIVE = "inactive"
    STARTING = "starting"
    STOPPING = "stopping"
    SYNCING = "syncing"


@dataclass(frozen=True, slots=True)
class ApplicationState:
    connected: bool = False
    status: JottaStatus | None = None
    disk_usage: DiskUsage | None = None
    sync_state: SyncState = SyncState.UNKNOWN
    error_message: str | None = None
