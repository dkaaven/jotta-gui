from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .common import FileStats


class SyncMode(StrEnum):
    """Configured Sync mode inferred only from verified CLI fields."""

    AUTOMATIC = "automatic"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class SyncActivity(StrEnum):
    """Observed runtime activity from human-readable status output."""

    LISTENING = "listening"
    TRIGGERED = "triggered"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SyncStatus:
    enabled: bool | None
    mode: SyncMode
    activity: SyncActivity

    root_path: Path | None
    local: FileStats
    remote: FileStats
    folder_count: int | None

    activity_text: str | None
    runtime_mode_text: str | None

    # Undocumented CLI value: preserved as evidence, never interpreted here.
    cli_sync_state: int | None
