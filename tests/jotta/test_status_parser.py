
import json

import pytest

from jotta_gui.jotta.status.parser import parse_status, parse_status_output


def test_parse_status_output(status_payload: dict) -> None:
    status = parse_status_output(json.dumps(status_payload))

    assert status.user.email == "user@example.com"
    assert status.user.fullname == "Example User"
    assert status.user.hostname == "workstation"
    assert status.user.account.capacity == 1_000_000
    assert status.sync.local.files == 12
    assert status.sync.remote.bytes == 1_200
    assert status.sync.folder_count == 3
    assert status.sync.state is None
    assert status.backups[0].name == "Documents"
    assert status.backups[0].device_id == "device-1"


def test_missing_counts_default_to_zero(status_payload: dict) -> None:
    status_payload["Sync"].pop("Count")
    status_payload["Sync"].pop("RemoteCount")
    status_payload["Sync"].pop("FolderCount")

    status = parse_status(status_payload)

    assert status.sync.local.files == 0
    assert status.sync.local.bytes == 0
    assert status.sync.remote.files == 0
    assert status.sync.remote.bytes == 0
    assert status.sync.folder_count == 0


def test_missing_backup_section_defaults_to_empty(status_payload: dict) -> None:
    status_payload.pop("Backup")

    status = parse_status(status_payload)

    assert status.backups == []


def test_optional_backup_values_default(status_payload: dict) -> None:
    backup = status_payload["Backup"]["State"]["Enabled"]["Backups"][0]
    for key in ("DeviceID", "LastUpdateMS", "LastScanStartedMS", "NextBackupMS"):
        backup.pop(key)

    parsed = parse_status(status_payload).backups[0]

    assert parsed.device_id == ""
    assert parsed.last_update_ms == 0
    assert parsed.last_scan_started_ms == 0
    assert parsed.next_backup_ms == 0


def test_invalid_json_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse_status_output("not json")


def test_missing_required_user_field_raises_key_error(status_payload: dict) -> None:
    status_payload["User"].pop("Email")

    with pytest.raises(KeyError):
        parse_status(status_payload)
