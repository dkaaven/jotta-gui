from jotta_gui.jotta.sync.models import SyncRuntimeActivity
from jotta_gui.jotta.sync.parser import parse_sync_runtime_status


def test_runtime_status_listening_for_exact_sync_root() -> None:
    output = """
Path: /other
Mode: idle
Path: /home/user/Jotta
Mode: listening to events
Status: Checking for changes...
"""

    observation = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert observation.activity == SyncRuntimeActivity.LISTENING
    assert observation.path == "/home/user/Jotta"
    assert observation.mode == "listening to events"
    assert observation.status == "Checking for changes..."


def test_runtime_status_triggered_for_observed_manual_mode() -> None:
    observation = parse_sync_runtime_status(
        "Path: /home/user/Jotta\nMode: manually triggered",
        "/home/user/Jotta",
    )

    assert observation.activity == SyncRuntimeActivity.TRIGGERED
    assert observation.mode == "manually triggered"


def test_runtime_status_unknown_for_unrecognized_mode_but_preserves_text() -> None:
    observation = parse_sync_runtime_status(
        "Path: /home/user/Jotta\nMode: paused",
        "/home/user/Jotta",
    )

    assert observation.activity == SyncRuntimeActivity.UNKNOWN
    assert observation.mode == "paused"


def test_runtime_status_unknown_when_root_is_missing() -> None:
    observation = parse_sync_runtime_status(
        "Path: /other\nMode: listening to events",
        "/home/user/Jotta",
    )

    assert observation.activity == SyncRuntimeActivity.UNKNOWN
    assert observation.path is None
    assert observation.mode is None


def test_runtime_status_unknown_when_configured_root_is_unknown() -> None:
    observation = parse_sync_runtime_status(
        "Path: /home/user/Jotta\nMode: listening to events",
        None,
    )

    assert observation.activity == SyncRuntimeActivity.UNKNOWN


def test_runtime_parser_uses_exact_root_match() -> None:
    observation = parse_sync_runtime_status(
        "Path: /home/user/Jotta2\nMode: listening to events",
        "/home/user/Jotta",
    )

    assert observation.activity == SyncRuntimeActivity.UNKNOWN


def test_runtime_parser_handles_colon_in_path_value() -> None:
    observation = parse_sync_runtime_status(
        "Path: C:\\Users\\Daniel\\Jotta\nMode: listening to events",
        "C:\\Users\\Daniel\\Jotta",
    )

    assert observation.activity == SyncRuntimeActivity.LISTENING


def test_runtime_parser_matches_known_modes_case_insensitively() -> None:
    listening = parse_sync_runtime_status(
        "Path: /home/user/Jotta\nMode: LISTENING TO EVENTS",
        "/home/user/Jotta",
    )
    triggered = parse_sync_runtime_status(
        "Path: /home/user/Jotta\nMode: MANUALLY TRIGGERED",
        "/home/user/Jotta",
    )

    assert listening.activity == SyncRuntimeActivity.LISTENING
    assert triggered.activity == SyncRuntimeActivity.TRIGGERED


def test_runtime_parser_does_not_take_status_from_next_path() -> None:
    output = """
Path: /home/user/Jotta
Mode: listening to events
Path: /home/user/backup
Status: Up to date
"""

    observation = parse_sync_runtime_status(output, "/home/user/Jotta")

    assert observation.activity == SyncRuntimeActivity.LISTENING
    assert observation.status is None
