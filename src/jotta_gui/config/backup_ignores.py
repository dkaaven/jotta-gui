from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
import tomllib
from typing import Any


@dataclass(frozen=True, slots=True)
class IgnorePreset:
    """One convenience ignore pattern shipped with Jotta GUI.

    Presets are never treated as active state. Jotta's own ignore list remains the
    source of truth; this model only describes a pattern the user may choose to add.
    """

    id: str
    label: str
    category: str
    pattern: str
    description: str


def load_ignore_presets(path: str | Path | None = None) -> tuple[IgnorePreset, ...]:
    """Load and validate the shipped backup-ignore preset catalogue."""

    if path is None:
        text = (
            resources.files(__package__)
            .joinpath("backup_ignore_presets.toml")
            .read_text(encoding="utf-8")
        )
    else:
        text = Path(path).read_text(encoding="utf-8")

    data = tomllib.loads(text)
    entries = data.get("preset")
    if not isinstance(entries, list):
        raise ValueError("Ignore preset config must contain [[preset]] entries")

    presets = tuple(_parse_preset(entry) for entry in entries)
    _validate_unique(presets)
    return presets


def _parse_preset(value: Any) -> IgnorePreset:
    if not isinstance(value, dict):
        raise ValueError("Each ignore preset must be a TOML table")

    def required(key: str) -> str:
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Ignore preset field {key!r} must be a non-empty string")
        return item.strip()

    return IgnorePreset(
        id=required("id"),
        label=required("label"),
        category=required("category"),
        pattern=required("pattern"),
        description=required("description"),
    )


def _validate_unique(presets: tuple[IgnorePreset, ...]) -> None:
    ids = [preset.id for preset in presets]
    if len(ids) != len(set(ids)):
        raise ValueError("Ignore preset ids must be unique")

    patterns = [preset.pattern for preset in presets]
    if len(patterns) != len(set(patterns)):
        raise ValueError("Ignore preset patterns must be unique")
