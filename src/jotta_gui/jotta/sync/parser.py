from jotta_gui.jotta.sync.models import SyncRuntimeState, SyncRuntimeStatus

LISTENING_MODE = "listening to events"
TRIGGERED_MODE = "manually triggered"


def parse_sync_runtime_status(output: str, root_path: str) -> SyncRuntimeStatus:
    current_path: str | None = None
    mode: str | None = None
    status: str | None = None

    for line in output.splitlines():
        key, value = _parse_field(line)

        if key == "Path":
            if current_path == root_path:
                break
            current_path = value
            continue

        if current_path != root_path:
            continue

        if key == "Mode":
            mode = value
        elif key == "Status":
            status = value

    return SyncRuntimeStatus(
        state=_runtime_state(mode),
        mode=mode,
        status=status,
    )


def _runtime_state(mode: str | None) -> SyncRuntimeState:
    if mode is None:
        return SyncRuntimeState.UNKNOWN

    normalized = mode.casefold()
    if normalized == LISTENING_MODE:
        return SyncRuntimeState.LISTENING
    if normalized == TRIGGERED_MODE:
        return SyncRuntimeState.TRIGGERED
    return SyncRuntimeState.UNKNOWN


def _parse_field(line: str) -> tuple[str, str]:
    key, separator, value = line.strip().partition(":")
    if not separator:
        return "", ""
    return key.strip(), value.strip()
