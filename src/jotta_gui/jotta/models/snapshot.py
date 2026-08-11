from dataclasses import dataclass
from datetime import datetime

from .account import AccountStatus
from .backup import BackupStatus
from .sync import SyncStatus


@dataclass(frozen=True, slots=True)
class JottaSnapshot:
    """Stable Jotta-domain snapshot consumed by the application layer."""

    account: AccountStatus
    sync: SyncStatus
    backups: tuple[BackupStatus, ...]
    captured_at: datetime
