from __future__ import annotations

import json

import pytest

from jotta_gui.jotta.status.parser import parse_status, parse_status_output


def _payload() -> dict:
    return {
        "User": {
            "Email": "user@example.com",
            "Fullname": "Example User",
            "Hostname": "workstation",
            "Brand": "Jottacloud",
            "AccountInfo": {
                "Capacity": 1_000_000,
                "Usage": 250_000,
                "Subscription": 1,
                "CanUpgrade": True,
                "UpgradeHint": False,
                "SubscriptionNameLocalized": "Personal",
                "ProductNameLocalized": "Personal 1 TB",
            },
            "device": {"Name": "Workstation", "Type": 12},
        },
        "Sync": {
            "Enabled": True,
            "Automatic": True,
            "RootPath": "/home/user/Jotta",
            "Count": {"Files": 12, "Bytes": 1_000},
            "RemoteCount": {"Files": 14, "Bytes": 1_200},
            "FolderCount": 3,
            "WorkingProgress": {},
            "SyncState": 1,
        },
        "State": {
            "RestoreWorking": True,
            "Uploading": {},
            "Downloading": {},
            "LastTokenRefresh": 123,
        },
        "Backup": {
            "State": {
                "Enabled": {
                    "deviceName": "Workstation",
                    "Backups": [
                        {
                            "Name": "Documents",
                            "Path": "/home/user/Documents",
                            "Count": {"Files": 5, "Bytes": 500},
                            "DeviceID": "device-1",
                            "LastUpdateMS": 200,
                            "LastScanStartedMS": 190,
                            "NextBackupMS": 300,
                            "Uploading": {},
                            "Errors": {},
                            "ErrorFilesCount": {},
                            "History": [
                                {
                                    "Path": "/home/user/Documents",
                                    "Started": 100,
                                    "Ended": 110,
                                    "Finished": True,
                                    "Total": {"Files": 5, "Bytes": 500},
                                }
                            ],
                        }
                    ],
                }
            }
        },
    }


def test_parse_status_output_preserves_cli_facts() -> None:
    status = parse_status_output(json.dumps(_payload()))

    assert status.user.email == "user@example.com"
    assert status.user.account.capacity == 1_000_000
    assert status.user.account.can_upgrade is True
    assert status.user.device.name == "Workstation"
    assert status.sync.enabled is True
    assert status.sync.automatic is True
    assert status.sync.count.files == 12
    assert status.sync.remote_count.bytes == 1_200
    assert status.sync.sync_state == 1
    assert status.state.last_token_refresh == 123


def test_parser_preserves_missing_values_as_unknown() -> None:
    payload = _payload()
    payload["Sync"].pop("RemoteCount")
    payload["Sync"].pop("FolderCount")
    backup = payload["Backup"]["State"]["Enabled"]["Backups"][0]
    backup.pop("LastUpdateMS")

    status = parse_status(payload)

    assert status.sync.remote_count.files is None
    assert status.sync.remote_count.bytes is None
    assert status.sync.folder_count is None
    assert status.backups[0].last_update_ms is None


def test_parser_does_not_coerce_wrong_types() -> None:
    payload = _payload()
    payload["Sync"]["Enabled"] = 1
    payload["Sync"]["FolderCount"] = True
    payload["User"]["AccountInfo"]["Usage"] = "250000"

    status = parse_status(payload)

    assert status.sync.enabled is None
    assert status.sync.folder_count is None
    assert status.user.account.usage is None


def test_backup_history_is_preserved() -> None:
    status = parse_status(_payload())

    backup = status.backups[0]
    history = backup.history[0]
    assert backup.name == "Documents"
    assert history.finished is True
    assert history.total.files == 5
    assert history.total.bytes == 500


def test_missing_backup_section_means_no_backups() -> None:
    payload = _payload()
    payload.pop("Backup")

    status = parse_status(payload)

    assert status.backups == ()


def test_raw_payload_is_retained() -> None:
    payload = _payload()
    payload["FutureField"] = {"SomeNewValue": 42}

    status = parse_status(payload)

    assert status.raw["FutureField"] == {"SomeNewValue": 42}


def test_empty_json_object_is_a_tolerant_raw_observation() -> None:
    status = parse_status_output("{}")

    assert status.user.email is None
    assert status.sync.enabled is None
    assert status.backups == ()


def test_invalid_json_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Invalid jotta-cli status JSON"):
        parse_status_output("not json")


def test_non_object_json_raises_value_error() -> None:
    with pytest.raises(ValueError, match="did not return a JSON object"):
        parse_status_output("[]")
