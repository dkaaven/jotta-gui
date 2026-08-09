
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AccountInfo:
    capacity: int
    usage: int
    subscription_name: str


@dataclass(frozen=True, slots=True)
class UserInfo:
    email: str
    fullname: str
    hostname: str
    account: AccountInfo


@dataclass(frozen=True, slots=True)
class FileCount:
    files: int = 0
    bytes: int = 0


@dataclass(frozen=True, slots=True)
class SyncInfo:
    enabled: bool
    root_path: str
    local: FileCount
    remote: FileCount
    folder_count: int
    state: int | None


@dataclass(frozen=True, slots=True)
class BackupInfo:
    name: str
    path: str
    count: FileCount
    device_id: str
    last_update_ms: int
    last_scan_started_ms: int
    next_backup_ms: int


@dataclass(frozen=True, slots=True)
class JottaStatus:
    user: UserInfo
    sync: SyncInfo
    backups: list[BackupInfo] = field(default_factory=list)
