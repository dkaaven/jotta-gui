
import json
from typing import Any

from jotta_gui.jotta.status.models import (
    AccountInfo,
    BackupInfo,
    FileCount,
    JottaStatus,
    SyncInfo,
    UserInfo,
)


def parse_status_output(output: str) -> JottaStatus:
    return parse_status(json.loads(output))


def parse_status(data: dict[str, Any]) -> JottaStatus:
    user_data = data["User"]
    account_data = user_data["AccountInfo"]
    sync_data = data["Sync"]

    user = UserInfo(
        email=user_data["Email"],
        fullname=user_data["Fullname"],
        hostname=user_data["Hostname"],
        account=AccountInfo(
            capacity=account_data["Capacity"],
            usage=account_data["Usage"],
            subscription_name=account_data["SubscriptionNameLocalized"],
        ),
    )

    sync = SyncInfo(
        enabled=sync_data["Enabled"],
        root_path=sync_data["RootPath"],
        local=_file_count(sync_data.get("Count")),
        remote=_file_count(sync_data.get("RemoteCount")),
        folder_count=sync_data.get("FolderCount", 0),
        state=sync_data.get("SyncState"),
    )

    backup_data = (
        data.get("Backup", {})
        .get("State", {})
        .get("Enabled", {})
        .get("Backups", [])
    )

    backups = [
        BackupInfo(
            name=backup["Name"],
            path=backup["Path"],
            count=_file_count(backup.get("Count")),
            device_id=backup.get("DeviceID", ""),
            last_update_ms=backup.get("LastUpdateMS", 0),
            last_scan_started_ms=backup.get("LastScanStartedMS", 0),
            next_backup_ms=backup.get("NextBackupMS", 0),
        )
        for backup in backup_data
    ]

    return JottaStatus(user=user, sync=sync, backups=backups)


def _file_count(data: dict[str, Any] | None) -> FileCount:
    data = data or {}
    return FileCount(
        files=data.get("Files", 0),
        bytes=data.get("Bytes", 0),
    )
