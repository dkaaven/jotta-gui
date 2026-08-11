from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class FileCount:
    files: int | None = None
    bytes: int | None = None


@dataclass(frozen=True, slots=True)
class AccountInfo:
    capacity: int | None = None
    usage: int | None = None
    subscription: int | None = None
    can_upgrade: bool | None = None
    upgrade_hint: bool | None = None
    subscription_name: str | None = None
    product_name: str | None = None


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    name: str | None = None
    type_code: int | None = None


@dataclass(frozen=True, slots=True)
class UserInfo:
    email: str | None = None
    fullname: str | None = None
    hostname: str | None = None
    brand: str | None = None
    account: AccountInfo = field(default_factory=AccountInfo)
    device: DeviceInfo = field(default_factory=DeviceInfo)


@dataclass(frozen=True, slots=True)
class SyncInfo:
    enabled: bool | None = None
    automatic: bool | None = None
    root_path: str | None = None
    count: FileCount = field(default_factory=FileCount)
    remote_count: FileCount = field(default_factory=FileCount)
    folder_count: int | None = None
    working_progress: Mapping[str, Any] | None = None
    sync_state: int | None = None


@dataclass(frozen=True, slots=True)
class TransferStateInfo:
    restore_working: bool | None = None
    uploading: Mapping[str, Any] | None = None
    downloading: Mapping[str, Any] | None = None
    last_token_refresh: int | None = None


@dataclass(frozen=True, slots=True)
class BackupHistoryInfo:
    path: str | None = None
    started: int | None = None
    ended: int | None = None
    finished: bool | None = None
    total: FileCount = field(default_factory=FileCount)


@dataclass(frozen=True, slots=True)
class BackupInfo:
    name: str | None = None
    path: str | None = None
    count: FileCount = field(default_factory=FileCount)
    device_id: str | None = None
    last_update_ms: int | None = None
    last_scan_started_ms: int | None = None
    next_backup_ms: int | None = None
    uploading: Mapping[str, Any] | None = None
    errors: Mapping[str, Any] | None = None
    error_files_count: Mapping[str, Any] | None = None
    history: tuple[BackupHistoryInfo, ...] = ()


@dataclass(frozen=True, slots=True)
class BackupEnabledInfo:
    device_name: str | None = None
    backups: tuple[BackupInfo, ...] = ()


@dataclass(frozen=True, slots=True)
class BackupStateInfo:
    enabled: BackupEnabledInfo | None = None


@dataclass(frozen=True, slots=True)
class BackupSection:
    state: BackupStateInfo | None = None


@dataclass(frozen=True, slots=True)
class CliStatus:
    """Parsed observation from ``jotta-cli status --json``.

    These models preserve CLI facts without assigning application semantics.
    ``raw`` is retained so newly introduced CLI fields are not lost while support is
    being added.
    """

    user: UserInfo
    sync: SyncInfo
    state: TransferStateInfo
    backup: BackupSection
    raw: Mapping[str, Any] = field(repr=False, compare=False)

    @property
    def backups(self) -> tuple[BackupInfo, ...]:
        if self.backup.state is None or self.backup.state.enabled is None:
            return ()
        return self.backup.state.enabled.backups
