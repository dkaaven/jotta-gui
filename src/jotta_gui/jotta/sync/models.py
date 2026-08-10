from dataclasses import dataclass
from enum import StrEnum


class SyncRuntimeState(StrEnum):
    LISTENING = "listening"
    TRIGGERED = "triggered"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SyncRuntimeStatus:
    state: SyncRuntimeState
    mode: str | None = None
    status: str | None = None
