from dataclasses import dataclass
from pathlib import Path

from .common import FileStats


@dataclass(frozen=True, slots=True)
class BackupStatus:
    name: str | None
    path: Path | None
    count: FileStats
    device_id: str | None

    last_update_ms: int | None
    last_scan_started_ms: int | None
    next_backup_ms: int | None
