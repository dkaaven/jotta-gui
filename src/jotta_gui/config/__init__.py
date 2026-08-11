"""Static application configuration shipped with Jotta GUI."""

from .backup_ignores import IgnorePreset, load_ignore_presets

__all__ = ["IgnorePreset", "load_ignore_presets"]
