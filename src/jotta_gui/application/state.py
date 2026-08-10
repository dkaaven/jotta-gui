from dataclasses import dataclass
from enum import StrEnum

from jotta_gui.jotta.status.models import JottaStatus
from jotta_gui.system.storage import DiskUsage


class SyncMode(StrEnum):
    UNKNOWN = "unknown"
    AUTOMATIC = "automatic"
    TRIGGERED = "triggered"


class SyncOperation(StrEnum):
    IDLE = "idle"
    STARTING = "starting"
    STOPPING = "stopping"
    TRIGGERING = "triggering"


class SyncActivity(StrEnum):
    UNKNOWN = "unknown"
    LISTENING = "listening"
    TRIGGERED = "triggered"


@dataclass(frozen=True, slots=True)
class ApplicationState:
    connected: bool = False
    status: JottaStatus | None = None
    disk_usage: DiskUsage | None = None
    sync_mode: SyncMode = SyncMode.UNKNOWN
    sync_operation: SyncOperation = SyncOperation.IDLE
    sync_activity: SyncActivity = SyncActivity.UNKNOWN
    sync_activity_status: str | None = None
    error_message: str | None = None


def sync_mode_from_automatic(automatic: bool | None) -> SyncMode:
    if automatic is True:
        return SyncMode.AUTOMATIC
    if automatic is None:
        return SyncMode.TRIGGERED
    return SyncMode.UNKNOWN
