from __future__ import annotations

import json
from typing import Any, Mapping

from .models import (
    AccountInfo,
    BackupEnabledInfo,
    BackupHistoryInfo,
    BackupInfo,
    BackupSection,
    BackupStateInfo,
    CliStatus,
    DeviceInfo,
    FileCount,
    SyncInfo,
    TransferStateInfo,
    UserInfo,
)


def parse_status_output(output: str) -> CliStatus:
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid jotta-cli status JSON: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValueError("jotta-cli status --json did not return a JSON object")

    return parse_status(data)


def parse_status(data: Mapping[str, Any]) -> CliStatus:
    user_data = _mapping(data.get("User"))
    account_data = _mapping(user_data.get("AccountInfo"))
    device_data = _mapping(user_data.get("device"))
    sync_data = _mapping(data.get("Sync"))
    state_data = _mapping(data.get("State"))

    user = UserInfo(
        email=_str(user_data.get("Email")),
        fullname=_str(user_data.get("Fullname")),
        hostname=_str(user_data.get("Hostname")),
        brand=_str(user_data.get("Brand")),
        account=AccountInfo(
            capacity=_int(account_data.get("Capacity")),
            usage=_int(account_data.get("Usage")),
            subscription=_int(account_data.get("Subscription")),
            can_upgrade=_bool(account_data.get("CanUpgrade")),
            upgrade_hint=_bool(account_data.get("UpgradeHint")),
            subscription_name=_str(account_data.get("SubscriptionNameLocalized")),
            product_name=_str(account_data.get("ProductNameLocalized")),
        ),
        device=DeviceInfo(
            name=_str(device_data.get("Name")),
            type_code=_int(device_data.get("Type")),
        ),
    )

    sync = SyncInfo(
        enabled=_bool(sync_data.get("Enabled")),
        automatic=_bool(sync_data.get("Automatic")),
        root_path=_str(sync_data.get("RootPath")),
        count=_file_count(sync_data.get("Count")),
        remote_count=_file_count(sync_data.get("RemoteCount")),
        folder_count=_int(sync_data.get("FolderCount")),
        working_progress=_optional_mapping(sync_data.get("WorkingProgress")),
        sync_state=_int(sync_data.get("SyncState")),
    )

    state = TransferStateInfo(
        restore_working=_bool(state_data.get("RestoreWorking")),
        uploading=_optional_mapping(state_data.get("Uploading")),
        downloading=_optional_mapping(state_data.get("Downloading")),
        last_token_refresh=_int(state_data.get("LastTokenRefresh")),
    )

    return CliStatus(
        user=user,
        sync=sync,
        state=state,
        backup=_backup_section(data.get("Backup")),
        raw=data,
    )


def _backup_section(value: Any) -> BackupSection:
    backup_data = _mapping(value)
    state_data = _mapping(backup_data.get("State"))
    enabled_value = state_data.get("Enabled")
    if not isinstance(enabled_value, Mapping):
        return BackupSection(state=BackupStateInfo(enabled=None))

    enabled_data = _mapping(enabled_value)
    backups_value = enabled_data.get("Backups")
    backups: tuple[BackupInfo, ...]
    if isinstance(backups_value, list):
        backups = tuple(
            _backup_info(item)
            for item in backups_value
            if isinstance(item, Mapping)
        )
    else:
        backups = ()

    return BackupSection(
        state=BackupStateInfo(
            enabled=BackupEnabledInfo(
                device_name=_str(enabled_data.get("deviceName")),
                backups=backups,
            )
        )
    )


def _backup_info(value: Mapping[str, Any]) -> BackupInfo:
    history_value = value.get("History")
    history: tuple[BackupHistoryInfo, ...]
    if isinstance(history_value, list):
        history = tuple(
            _backup_history(item)
            for item in history_value
            if isinstance(item, Mapping)
        )
    else:
        history = ()

    return BackupInfo(
        name=_str(value.get("Name")),
        path=_str(value.get("Path")),
        count=_file_count(value.get("Count")),
        device_id=_str(value.get("DeviceID")),
        last_update_ms=_int(value.get("LastUpdateMS")),
        last_scan_started_ms=_int(value.get("LastScanStartedMS")),
        next_backup_ms=_int(value.get("NextBackupMS")),
        uploading=_optional_mapping(value.get("Uploading")),
        errors=_optional_mapping(value.get("Errors")),
        error_files_count=_optional_mapping(value.get("ErrorFilesCount")),
        history=history,
    )


def _backup_history(value: Mapping[str, Any]) -> BackupHistoryInfo:
    return BackupHistoryInfo(
        path=_str(value.get("Path")),
        started=_int(value.get("Started")),
        ended=_int(value.get("Ended")),
        finished=_bool(value.get("Finished")),
        total=_file_count(value.get("Total")),
    )


def _file_count(value: Any) -> FileCount:
    data = _mapping(value)
    return FileCount(
        files=_int(data.get("Files")),
        bytes=_int(data.get("Bytes")),
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _optional_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
