from dataclasses import dataclass
from enum import StrEnum


class SyncRuntimeActivity(StrEnum):
    LISTENING = "listening"
    TRIGGERED = "triggered"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SyncRuntimeObservation:
    """Runtime evidence parsed from human-readable ``jotta-cli status``."""

    activity: SyncRuntimeActivity
    path: str | None = None
    mode: str | None = None
    status: str | None = None
