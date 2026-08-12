from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "build_deb.py"


def _module():
    spec = importlib.util.spec_from_file_location("build_deb", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_read_project_version(tmp_path: Path) -> None:
    module = _module()
    project = tmp_path / "pyproject.toml"
    project.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")

    assert module.read_project_version(project) == "1.2.3"


def test_render_control_replaces_metadata() -> None:
    module = _module()
    template = (
        "Package: jotta-gui\n"
        "Version: @VERSION@\n"
        "Architecture: @ARCHITECTURE@\n"
        "Maintainer: @MAINTAINER@\n"
    )

    rendered = module.render_control(
        template,
        version="0.2.0",
        architecture="amd64",
        maintainer="Example <example@example.com>",
    )

    assert "Version: 0.2.0" in rendered
    assert "Architecture: amd64" in rendered
    assert "Maintainer: Example <example@example.com>" in rendered
    assert "@VERSION@" not in rendered


def test_architecture_fallback(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module.shutil, "which", lambda command: None)
    monkeypatch.setattr(module.platform, "machine", lambda: "x86_64")

    assert module.detect_debian_architecture() == "amd64"


def test_unknown_architecture_fails(monkeypatch) -> None:
    module = _module()
    monkeypatch.setattr(module.shutil, "which", lambda command: None)
    monkeypatch.setattr(module.platform, "machine", lambda: "mystery-cpu")

    with pytest.raises(RuntimeError, match="Unsupported Debian architecture"):
        module.detect_debian_architecture()


def test_verify_frozen_application_accepts_required_resources(tmp_path: Path) -> None:
    module = _module()
    frozen = tmp_path / "jotta-gui"
    required = (
        frozen / "jotta-gui",
        frozen / "_internal" / "jotta_gui" / "resources" / "jotta-gui.svg",
        frozen / "_internal" / "jotta_gui" / "ui" / "styles" / "dark.qss",
        frozen
        / "_internal"
        / "jotta_gui"
        / "config"
        / "backup_ignore_presets.toml",
    )
    for path in required:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test", encoding="utf-8")

    module.verify_frozen_application(frozen)


def test_verify_frozen_application_rejects_missing_resources(tmp_path: Path) -> None:
    module = _module()
    frozen = tmp_path / "jotta-gui"
    frozen.mkdir()
    (frozen / "jotta-gui").write_text("test", encoding="utf-8")

    with pytest.raises(RuntimeError, match="missing required runtime files"):
        module.verify_frozen_application(frozen)
