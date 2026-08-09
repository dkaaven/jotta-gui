import json
from pathlib import Path

import pytest

from jotta_gui.devtools.fixtures import (
    Capture,
    SANITIZED_SYNC_ROOT,
    main,
    sanitize_capture,
    sanitize_status,
    write_capture,
)


def test_sanitize_status_replaces_personal_fields(status_payload: dict) -> None:
    sanitized, replacements = sanitize_status(status_payload)

    user = sanitized["User"]
    sync = sanitized["Sync"]
    backup = sanitized["Backup"]["State"]["Enabled"]["Backups"][0]

    assert user["Email"] == "user@example.com"
    assert user["Fullname"] == "Example User"
    assert user["Hostname"] == "example-host"
    assert sync["RootPath"] == SANITIZED_SYNC_ROOT
    assert backup["Name"] == "Backup 1"
    assert backup["Path"] == "/home/example/backup-1"
    assert backup["DeviceID"] == "device-1"
    assert replacements["/home/user/Jotta"] == SANITIZED_SYNC_ROOT


def test_sanitize_capture_keeps_runtime_root_in_sync(status_payload: dict) -> None:
    capture = Capture(
        status=status_payload,
        runtime="Path: /home/user/Jotta\nMode: listening to events\n",
        replacements={},
    )

    sanitized = sanitize_capture(capture)

    assert f"Path: {SANITIZED_SYNC_ROOT}" in sanitized.runtime
    assert "/home/user/Jotta" not in sanitized.runtime


def test_sanitize_capture_redacts_unexpected_runtime_email(status_payload: dict) -> None:
    capture = Capture(
        status=status_payload,
        runtime="Contact: other.person@private.example\n",
        replacements={},
    )

    sanitized = sanitize_capture(capture)

    assert "other.person@private.example" not in sanitized.runtime
    assert "user@example.com" in sanitized.runtime


def test_write_capture_creates_complete_fixture(
    tmp_path: Path,
    status_payload: dict,
) -> None:
    capture = sanitize_capture(
        Capture(
            status=status_payload,
            runtime="Path: /home/user/Jotta\nMode: listening to events\n",
            replacements={},
        )
    )

    destination = write_capture(
        "Linux Active",
        capture,
        expected_sync_state="active",
        output_root=tmp_path,
    )

    assert destination.name == "linux-active"
    assert (destination / "status.json").is_file()
    assert (destination / "runtime.txt").is_file()

    metadata = json.loads((destination / "metadata.json").read_text())
    assert metadata["schema"] == 1
    assert metadata["expected_sync_state"] == "active"


def test_write_capture_rejects_unsafe_name(
    tmp_path: Path,
    status_payload: dict,
) -> None:
    capture = Capture(status=status_payload, runtime="", replacements={})

    with pytest.raises(ValueError):
        write_capture("../outside", capture, None, output_root=tmp_path)


def test_main_captures_and_writes_fixture(
    tmp_path: Path,
    status_payload: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture = Capture(
        status=status_payload,
        runtime="Path: /home/user/Jotta\nMode: listening to events\n",
        replacements={},
    )
    monkeypatch.setattr("jotta_gui.devtools.fixtures.capture_cli", lambda binary: capture)

    result = main(
        [
            "Linux Active",
            "--sync-state",
            "active",
            "--output-root",
            str(tmp_path),
        ]
    )

    assert result == 0
    destination = tmp_path / "linux-active"
    assert (destination / "status.json").is_file()
    assert (destination / "runtime.txt").is_file()
    assert (destination / "metadata.json").is_file()
