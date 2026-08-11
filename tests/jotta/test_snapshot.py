from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from jotta_gui.jotta.models import SyncActivity, SyncMode
from jotta_gui.jotta.snapshot import build_snapshot
from jotta_gui.jotta.status.parser import parse_status
from jotta_gui.jotta.sync.models import SyncRuntimeActivity, SyncRuntimeObservation


BASE_STATUS = {
    "User": {
        "Email": "user@example.com",
        "Fullname": "Example User",
        "Hostname": "workstation",
        "Brand": "Jottacloud",
        "AccountInfo": {
            "Capacity": 1_000_000,
            "Usage": 250_000,
            "Subscription": 1,
            "SubscriptionNameLocalized": "Personal",
            "ProductNameLocalized": "Personal",
        },
        "device": {"Name": "Workstation", "Type": 12},
    },
    "Sync": {
        "Enabled": True,
        "Automatic": True,
        "RootPath": "/home/user/Jotta",
        "Count": {"Files": 12, "Bytes": 1_000},
        "RemoteCount": {},
        "FolderCount": 3,
        "SyncState": 1,
    },
    "Backup": {
        "State": {
            "Enabled": {
                "Backups": [
                    {
                        "Name": "Documents",
                        "Path": "/home/user/Documents",
                        "Count": {"Files": 5, "Bytes": 500},
                        "DeviceID": "device-1",
                    }
                ]
            }
        }
    },
}


def _status(**sync_changes):
    payload = deepcopy(BASE_STATUS)
    payload["Sync"].update(sync_changes)
    return parse_status(payload)


@pytest.mark.parametrize(
    ("enabled", "automatic", "root_path", "expected"),
    [
        (False, True, "/home/user/Jotta", SyncMode.DISABLED),
        (True, True, "/home/user/Jotta", SyncMode.AUTOMATIC),
        (True, None, "/home/user/Jotta", SyncMode.TRIGGERED),
        (True, False, "/home/user/Jotta", SyncMode.UNKNOWN),
        (None, True, "/home/user/Jotta", SyncMode.UNKNOWN),
        (True, None, None, SyncMode.UNKNOWN),
    ],
)
def test_sync_mode_uses_only_verified_cli_semantics(
    enabled,
    automatic,
    root_path,
    expected: SyncMode,
) -> None:
    snapshot = build_snapshot(
        _status(Enabled=enabled, Automatic=automatic, RootPath=root_path)
    )

    assert snapshot.sync.mode == expected


def test_runtime_activity_is_separate_from_configured_mode() -> None:
    runtime = SyncRuntimeObservation(
        activity=SyncRuntimeActivity.TRIGGERED,
        path="/home/user/Jotta",
        mode="manually triggered",
        status="Checking for changes...",
    )

    snapshot = build_snapshot(_status(Automatic=True), runtime)

    assert snapshot.sync.mode == SyncMode.AUTOMATIC
    assert snapshot.sync.activity == SyncActivity.TRIGGERED
    assert snapshot.sync.activity_text == "Checking for changes..."
    assert snapshot.sync.runtime_mode_text == "manually triggered"


def test_missing_runtime_observation_stays_unknown() -> None:
    snapshot = build_snapshot(_status())

    assert snapshot.sync.activity == SyncActivity.UNKNOWN
    assert snapshot.sync.activity_text is None
    assert snapshot.sync.runtime_mode_text is None


def test_cli_sync_state_is_preserved_but_does_not_choose_mode() -> None:
    triggered = build_snapshot(_status(Automatic=None, SyncState=1))
    automatic = build_snapshot(_status(Automatic=True, SyncState=1))

    assert triggered.sync.cli_sync_state == 1
    assert automatic.sync.cli_sync_state == 1
    assert triggered.sync.mode == SyncMode.TRIGGERED
    assert automatic.sync.mode == SyncMode.AUTOMATIC


def test_missing_remote_counts_stay_unknown_in_domain_model() -> None:
    snapshot = build_snapshot(_status(RemoteCount={}))

    assert snapshot.sync.remote.files is None
    assert snapshot.sync.remote.bytes is None


def test_zero_is_not_treated_as_missing() -> None:
    snapshot = build_snapshot(
        _status(Count={"Files": 0, "Bytes": 0}, FolderCount=0)
    )

    assert snapshot.sync.local.files == 0
    assert snapshot.sync.local.bytes == 0
    assert snapshot.sync.folder_count == 0


def test_paths_are_normalized_to_path_objects() -> None:
    snapshot = build_snapshot(_status())

    assert snapshot.sync.root_path == Path("/home/user/Jotta")
    assert snapshot.backups[0].path == Path("/home/user/Documents")


def test_account_and_backup_facts_are_normalized() -> None:
    snapshot = build_snapshot(_status())

    assert snapshot.account.email == "user@example.com"
    assert snapshot.account.capacity == 1_000_000
    assert snapshot.account.device_name == "Workstation"
    assert snapshot.backups[0].name == "Documents"
    assert snapshot.backups[0].count.files == 5


def test_explicit_capture_time_is_preserved() -> None:
    captured_at = datetime(2026, 8, 12, 0, 0, tzinfo=timezone.utc)

    snapshot = build_snapshot(_status(), captured_at=captured_at)

    assert snapshot.captured_at == captured_at
