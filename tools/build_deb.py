#!/usr/bin/env python3
"""Build a self-contained Debian package for Jotta GUI.

The package uses a PyInstaller one-directory bundle under /opt/jotta-gui and
installs a small launcher, desktop entry, and icon into standard system paths.
The target system still supplies jotta-cli/jottad through the official
``jotta-cli`` Debian package.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PROJECT_FILE = ROOT / "pyproject.toml"
PYINSTALLER_VERSION = "6.22.0"
DEFAULT_MAINTAINER = "Jotta GUI Project <jotta-gui@example.invalid>"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--maintainer",
        default=os.environ.get("DEB_MAINTAINER", DEFAULT_MAINTAINER),
        help="Debian Maintainer field (or set DEB_MAINTAINER).",
    )
    parser.add_argument(
        "--keep-build",
        action="store_true",
        help="Keep build/deb after the package is created.",
    )
    args = parser.parse_args(argv)

    require_command("uv")
    require_command("dpkg-deb")

    version = read_project_version()
    architecture = detect_debian_architecture()
    build_root = ROOT / "build" / "deb"
    output_dir = ROOT / "dist"
    output = output_dir / f"jotta-gui_{version}_{architecture}.deb"

    if build_root.exists():
        shutil.rmtree(build_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Building Jotta GUI {version} for {architecture}")
    frozen = build_frozen_application(build_root)
    stage = stage_debian_package(
        build_root=build_root,
        frozen=frozen,
        version=version,
        architecture=architecture,
        maintainer=args.maintainer,
    )

    run(
        [
            "dpkg-deb",
            "--root-owner-group",
            "--build",
            str(stage),
            str(output),
        ]
    )

    print()
    print(f"Created: {output}")
    print(f"Inspect: dpkg-deb --info {output}")
    print(f"Install: sudo apt install ./{output.relative_to(ROOT)}")

    if not args.keep_build:
        shutil.rmtree(build_root)

    return 0


def read_project_version(path: Path = PROJECT_FILE) -> str:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("pyproject.toml does not contain project.version")
    return version.strip()


def detect_debian_architecture() -> str:
    dpkg = shutil.which("dpkg")
    if dpkg:
        result = subprocess.run(
            [dpkg, "--print-architecture"],
            check=True,
            capture_output=True,
            text=True,
        )
        architecture = result.stdout.strip()
        if architecture:
            return architecture

    machine = platform.machine().casefold()
    fallback = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "i386": "i386",
        "i686": "i386",
        "armv7l": "armhf",
    }
    try:
        return fallback[machine]
    except KeyError as exc:
        raise RuntimeError(f"Unsupported Debian architecture: {machine}") from exc


def build_frozen_application(build_root: Path) -> Path:
    dist_path = build_root / "pyinstaller" / "dist"
    work_path = build_root / "pyinstaller" / "work"
    spec_path = build_root / "pyinstaller" / "spec"

    for path in (dist_path, work_path, spec_path):
        path.mkdir(parents=True, exist_ok=True)

    # A Debian package already provides a filesystem container, so onedir avoids
    # extracting a onefile bundle on every application start.
    run(
        [
            "uv",
            "run",
            "--with",
            f"pyinstaller=={PYINSTALLER_VERSION}",
            "pyinstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--windowed",
            "--name",
            "jotta-gui",
            "--paths",
            str(ROOT / "src"),
            "--collect-data",
            "jotta_gui",
            "--distpath",
            str(dist_path),
            "--workpath",
            str(work_path),
            "--specpath",
            str(spec_path),
            str(ROOT / "src" / "jotta_gui" / "__main__.py"),
        ]
    )

    frozen = dist_path / "jotta-gui"
    verify_frozen_application(frozen)
    return frozen


def verify_frozen_application(frozen: Path) -> None:
    """Fail the build if runtime files required by the frozen app are missing."""

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
    missing = [path for path in required if not path.is_file()]
    if missing:
        details = "\n".join(f"  - {path}" for path in missing)
        raise RuntimeError(
            "PyInstaller bundle is missing required runtime files:\n" + details
        )


def stage_debian_package(
    *,
    build_root: Path,
    frozen: Path,
    version: str,
    architecture: str,
    maintainer: str,
) -> Path:
    stage = build_root / "stage"
    debian_dir = stage / "DEBIAN"
    app_dir = stage / "opt" / "jotta-gui"
    bin_dir = stage / "usr" / "bin"
    desktop_dir = stage / "usr" / "share" / "applications"
    icon_dir = stage / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
    doc_dir = stage / "usr" / "share" / "doc" / "jotta-gui"

    for path in (debian_dir, bin_dir, desktop_dir, icon_dir, doc_dir):
        path.mkdir(parents=True, exist_ok=True)

    shutil.copytree(frozen, app_dir)
    shutil.copy2(
        ROOT / "packaging" / "linux" / "jotta-gui.desktop",
        desktop_dir / "jotta-gui.desktop",
    )
    shutil.copy2(
        ROOT / "src" / "jotta_gui" / "resources" / "jotta-gui.svg",
        icon_dir / "jotta-gui.svg",
    )
    if (ROOT / "README.md").is_file():
        shutil.copy2(ROOT / "README.md", doc_dir / "README.md")

    launcher = bin_dir / "jotta-gui"
    launcher.write_text(
        "#!/bin/sh\nexec /opt/jotta-gui/jotta-gui \"$@\"\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)

    control_template = (ROOT / "packaging" / "debian" / "control.in").read_text(
        encoding="utf-8"
    )
    control = render_control(
        control_template,
        version=version,
        architecture=architecture,
        maintainer=maintainer,
    )
    (debian_dir / "control").write_text(control, encoding="utf-8")

    return stage


def render_control(
    template: str,
    *,
    version: str,
    architecture: str,
    maintainer: str,
) -> str:
    replacements = {
        "@VERSION@": version,
        "@ARCHITECTURE@": architecture,
        "@MAINTAINER@": maintainer,
    }
    rendered = template
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)

    unresolved = [token for token in replacements if token in rendered]
    if unresolved:
        raise ValueError(
            f"Unresolved Debian control placeholder: {', '.join(unresolved)}"
        )
    return rendered.rstrip() + "\n"


def require_command(command: str) -> None:
    if shutil.which(command) is None:
        raise RuntimeError(f"Required command not found: {command}")


def run(arguments: list[str]) -> None:
    print("+", " ".join(arguments))
    subprocess.run(arguments, cwd=ROOT, check=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
