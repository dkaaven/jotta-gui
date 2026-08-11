from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .models import (
    AccountStatus,
    BackupStatus,
    FileStats,
    JottaSnapshot,
    SyncActivity,
    SyncMode,
    SyncStatus,
)
from .status.models import CliStatus, FileCount
from .sync.models import SyncRuntimeActivity, SyncRuntimeObservation


def build_snapshot(
    status: CliStatus,
    runtime: SyncRuntimeObservation | None = None,
    *,
    captured_at: datetime | None = None,
) -> JottaSnapshot:
    """Normalize raw CLI observations into the stable Jotta domain model."""

    runtime = runtime or SyncRuntimeObservation(
        activity=SyncRuntimeActivity.UNKNOWN
    )

    account = status.user.account
    device = status.user.device

    return JottaSnapshot(
        account=AccountStatus(
            email=status.user.email,
            fullname=status.user.fullname,
            hostname=status.user.hostname,
            brand=status.user.brand,
            capacity=account.capacity,
            usage=account.usage,
            subscription_code=account.subscription,
            subscription_name=account.subscription_name,
            product_name=account.product_name,
            device_name=device.name,
            device_type=device.type_code,
        ),
        sync=SyncStatus(
            enabled=status.sync.enabled,
            mode=_sync_mode(status),
            activity=_sync_activity(runtime),
            root_path=_path(status.sync.root_path),
            local=_file_stats(status.sync.count),
            remote=_file_stats(status.sync.remote_count),
            folder_count=status.sync.folder_count,
            activity_text=runtime.status,
            runtime_mode_text=runtime.mode,
            cli_sync_state=status.sync.sync_state,
        ),
        backups=tuple(
            BackupStatus(
                name=backup.name,
                path=_path(backup.path),
                count=_file_stats(backup.count),
                device_id=backup.device_id,
                last_update_ms=backup.last_update_ms,
                last_scan_started_ms=backup.last_scan_started_ms,
                next_backup_ms=backup.next_backup_ms,
            )
            for backup in status.backups
        ),
        captured_at=captured_at or datetime.now(timezone.utc),
    )


def _sync_mode(status: CliStatus) -> SyncMode:
    sync = status.sync

    if sync.enabled is False:
        return SyncMode.DISABLED
    if sync.enabled is not True:
        return SyncMode.UNKNOWN

    if sync.automatic is True:
        return SyncMode.AUTOMATIC

    # Observed on jotta-cli 0.17.159692: after ``sync stop`` Automatic is
    # null/missing while Sync remains configured and trigger mode is accepted.
    if sync.automatic is None and sync.root_path:
        return SyncMode.TRIGGERED

    # False has not been assigned verified semantics.
    return SyncMode.UNKNOWN


def _sync_activity(runtime: SyncRuntimeObservation) -> SyncActivity:
    mapping = {
        SyncRuntimeActivity.LISTENING: SyncActivity.LISTENING,
        SyncRuntimeActivity.TRIGGERED: SyncActivity.TRIGGERED,
        SyncRuntimeActivity.UNKNOWN: SyncActivity.UNKNOWN,
    }
    return mapping[runtime.activity]


def _file_stats(value: FileCount) -> FileStats:
    return FileStats(files=value.files, bytes=value.bytes)


def _path(value: str | None) -> Path | None:
    return Path(value) if value else None
