from __future__ import annotations

from .models import SyncRuntimeActivity, SyncRuntimeObservation

LISTENING_MODE = "listening to events"
TRIGGERED_MODE = "manually triggered"


def parse_sync_runtime_status(
    output: str,
    root_path: str | None,
) -> SyncRuntimeObservation:
    """Extract runtime evidence only for the exact configured Sync root.

    Human-readable status may omit the Sync root or include backup paths beneath the
    Sync heading. In either case, no exact root match means UNKNOWN rather than
    stopped/inactive.
    """

    if not root_path:
        return SyncRuntimeObservation(activity=SyncRuntimeActivity.UNKNOWN)

    matched = False
    mode: str | None = None
    status: str | None = None

    for line in output.splitlines():
        key, value = _parse_field(line)
        if not key:
            continue

        if key == "Path":
            if matched:
                break
            matched = value == root_path
            continue

        if not matched:
            continue

        if key == "Mode":
            mode = value
        elif key == "Status":
            status = value

    if not matched:
        return SyncRuntimeObservation(activity=SyncRuntimeActivity.UNKNOWN)

    return SyncRuntimeObservation(
        activity=_runtime_activity(mode),
        path=root_path,
        mode=mode,
        status=status,
    )


def _runtime_activity(mode: str | None) -> SyncRuntimeActivity:
    if mode is None:
        return SyncRuntimeActivity.UNKNOWN

    normalized = mode.casefold()
    if normalized == LISTENING_MODE:
        return SyncRuntimeActivity.LISTENING
    if normalized == TRIGGERED_MODE:
        return SyncRuntimeActivity.TRIGGERED
    return SyncRuntimeActivity.UNKNOWN


def _parse_field(line: str) -> tuple[str, str]:
    key, separator, value = line.strip().partition(":")
    if not separator:
        return "", ""
    return key.strip(), value.strip()
