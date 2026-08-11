from pathlib import Path

import pytest

from jotta_gui.config import load_ignore_presets


def test_shipped_ignore_presets_are_available() -> None:
    presets = load_ignore_presets()

    assert [preset.pattern for preset in presets] == [
        "**/.git",
        "**/.venv",
        "**/__pycache__",
        "**/.pytest_cache",
        "**/.ruff_cache",
        "**/node_modules",
    ]
    assert all(preset.label for preset in presets)
    assert all(preset.description for preset in presets)


def test_ignore_preset_loader_rejects_duplicate_patterns(tmp_path: Path) -> None:
    config = tmp_path / "presets.toml"
    config.write_text(
        """
[[preset]]
id = "one"
label = "One"
category = "Test"
pattern = "**/.cache"
description = "One"

[[preset]]
id = "two"
label = "Two"
category = "Test"
pattern = "**/.cache"
description = "Two"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="patterns must be unique"):
        load_ignore_presets(config)
