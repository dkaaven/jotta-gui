from jotta_gui.jotta.sync.models import SyncRuntimeState, SyncRuntimeStatus


def parse_sync_runtime_status(output: str, root_path: str) -> SyncRuntimeStatus:
    current_path: str | None = None

    for line in output.splitlines():
        key, value = _parse_field(line)
        if key == "Path":
            current_path = value
            continue

        if key != "Mode" or current_path != root_path:
            continue

        if value.casefold() == "listening to events":
            return SyncRuntimeStatus(SyncRuntimeState.ACTIVE, value)

        return SyncRuntimeStatus(SyncRuntimeState.INACTIVE, value)

    return SyncRuntimeStatus(SyncRuntimeState.UNKNOWN)


def _parse_field(line: str) -> tuple[str, str]:
    key, separator, value = line.strip().partition(":")
    if not separator:
        return "", ""
    return key.strip(), value.strip()
