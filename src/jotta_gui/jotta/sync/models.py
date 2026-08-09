from dataclasses import dataclass
from enum import StrEnum


class SyncRuntimeState(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SyncRuntimeStatus:
    state: SyncRuntimeState
    mode: str | None = None
