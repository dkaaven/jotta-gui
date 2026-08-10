from jotta_gui.jotta.sync.models import SyncRuntimeState
from jotta_gui.jotta.sync.parser import parse_sync_runtime_status


def test_runtime_status_listening_for_sync_root() -> None:
    output = """
Path: /other
Mode: idle
Path: /home/user/Jotta
Mode: listening to events
"""

    status = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert status.state == SyncRuntimeState.LISTENING
    assert status.mode == "listening to events"


def test_runtime_status_triggered_for_captured_manual_mode() -> None:
    output = """
Path: /home/user/Jotta
Mode: manually triggered
Status: Checking for changes...
"""

    status = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert status.state == SyncRuntimeState.TRIGGERED
    assert status.mode == "manually triggered"
    assert status.status == "Checking for changes..."


def test_runtime_status_unknown_for_unrecognized_mode() -> None:
    output = """
Path: /home/user/Jotta
Mode: paused
"""

    status = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert status.state == SyncRuntimeState.UNKNOWN
    assert status.mode == "paused"


def test_runtime_status_unknown_when_root_is_missing() -> None:
    status = parse_sync_runtime_status(
        "Path: /other\nMode: listening to events",
        "/home/user/Jotta",
    )

    assert status.state == SyncRuntimeState.UNKNOWN
    assert status.mode is None


def test_runtime_status_unknown_when_mode_is_missing() -> None:
    status = parse_sync_runtime_status("Path: /home/user/Jotta", "/home/user/Jotta")

    assert status.state == SyncRuntimeState.UNKNOWN


def test_runtime_parser_uses_exact_root_match() -> None:
    output = "Path: /home/user/Jotta2\nMode: listening to events"

    status = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert status.state == SyncRuntimeState.UNKNOWN


def test_runtime_parser_handles_colon_in_path_value() -> None:
    output = "Path: C:\\Users\\Daniel\\Jotta\nMode: listening to events"

    status = parse_sync_runtime_status(output, "C:\\Users\\Daniel\\Jotta")

    assert status.state == SyncRuntimeState.LISTENING


def test_runtime_parser_matches_known_modes_case_insensitively() -> None:
    listening = parse_sync_runtime_status(
        "Path: /home/user/Jotta\nMode: LISTENING TO EVENTS",
        "/home/user/Jotta",
    )
    triggered = parse_sync_runtime_status(
        "Path: /home/user/Jotta\nMode: MANUALLY TRIGGERED",
        "/home/user/Jotta",
    )

    assert listening.state == SyncRuntimeState.LISTENING
    assert triggered.state == SyncRuntimeState.TRIGGERED


def test_runtime_parser_does_not_take_status_from_backup_section() -> None:
    output = """
Path: /home/user/Jotta
Mode: listening to events
Path: /home/user/backup
Status: Up to date
"""

    status = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert status.state == SyncRuntimeState.LISTENING
    assert status.status is None
