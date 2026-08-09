
from jotta_gui.jotta.sync.models import SyncRuntimeState
from jotta_gui.jotta.sync.parser import parse_sync_runtime_status


def test_runtime_status_active_for_sync_root() -> None:
    output = """
Path: /other
Mode: idle
Path: /home/user/Jotta
Mode: listening to events
"""

    status = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert status.state == SyncRuntimeState.ACTIVE
    assert status.mode == "listening to events"


def test_runtime_status_inactive_preserves_mode() -> None:
    output = """
Path: /home/user/Jotta
Mode: paused
"""

    status = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert status.state == SyncRuntimeState.INACTIVE
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

    assert status.state == SyncRuntimeState.ACTIVE


def test_runtime_parser_matches_active_mode_case_insensitively() -> None:
    output = "Path: /home/user/Jotta\nMode: LISTENING TO EVENTS"

    status = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert status.state == SyncRuntimeState.ACTIVE
