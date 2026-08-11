from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfigEntry:
    """One value reported by ``jotta-cli config``."""

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class JottaConfig:
    """Read-only snapshot of daemon configuration values.

    The CLI remains the source of truth. ``raw_output`` is retained so newly added
    settings stay inspectable before Jotta GUI gains dedicated controls for them.
    """

    entries: tuple[ConfigEntry, ...]
    raw_output: str

    def get(self, name: str) -> str | None:
        normalized = name.casefold()
        for entry in self.entries:
            if entry.name.casefold() == normalized:
                return entry.value
        return None
