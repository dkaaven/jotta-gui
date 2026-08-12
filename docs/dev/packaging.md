# Debian packaging

Jotta GUI's first Debian package is a self-contained desktop bundle built with
PyInstaller and wrapped in a normal `.deb` filesystem layout.

## Why a bundled application

The Python project currently targets a newer PySide6 than some supported Ubuntu
repositories provide. The `.deb` therefore bundles Python, PySide6, Qt, and the
Jotta GUI Python package instead of installing Python modules into the system
Python environment.

`jotta-cli` is intentionally **not** bundled. It remains an external runtime
requirement and is declared as the Debian dependency `jotta-cli`.

The package layout is:

```text
/opt/jotta-gui/                         PyInstaller application bundle
/usr/bin/jotta-gui                      launcher
/usr/share/applications/jotta-gui.desktop
/usr/share/icons/hicolor/scalable/apps/jotta-gui.svg
/usr/share/doc/jotta-gui/README.md
```

## Build

Prerequisites on the build machine:

- `uv`
- `dpkg` / `dpkg-deb`
- the normal Jotta GUI development environment

From the repository root:

```bash
DEB_MAINTAINER='Your Name <you@example.com>' \
  uv run python tools/build_deb.py
```

The script uses a pinned PyInstaller build tool without adding it to the runtime
project dependencies.

Expected output:

```text
dist/jotta-gui_<version>_<architecture>.deb
```

For example:

```text
dist/jotta-gui_0.2.1_amd64.deb
```

Inspect the package before installation:

```bash
dpkg-deb --info dist/jotta-gui_0.2.1_amd64.deb
dpkg-deb --contents dist/jotta-gui_0.2.1_amd64.deb
```

Install or upgrade the local build:

```bash
sudo apt install ./dist/jotta-gui_0.2.0_amd64.deb
```

Remove it with:

```bash
sudo apt remove jotta-gui
```

The user's Jottacloud state under their home directory is not part of the package
and is not removed by uninstalling Jotta GUI.

## Runtime dependency

The package declares `jotta-cli` as a dependency. On Debian/Ubuntu, install the
official Jottacloud package/repository before installing Jotta GUI if it is not
already present.

## Linux compatibility

PyInstaller GNU/Linux bundles still use the target system's libc. Build release
artifacts on the **oldest Linux distribution/version you intend to support** and
build separately for each architecture. A package produced on a newer distribution
can fail on an older one even when the Debian package itself installs correctly.

For the first Jotta GUI release, building and testing on the Ubuntu version used for
development is acceptable. Before publishing packages for multiple Ubuntu/Debian
releases, move the build into clean release-specific containers or CI jobs.

## Before a public release

Add the following before treating the package as a public Debian distribution:

- project license and Debian copyright metadata;
- AppStream metadata;
- automated clean-environment package builds;
- installation/upgrade/removal smoke tests;
- dependency inspection with Debian tooling;
- package signing and a repository, if automatic updates are later implemented.

## Bundled package resources

PyInstaller freezes `src/jotta_gui/__main__.py` as the entry script, so the frozen
entry script is not located inside the `jotta_gui` package directory. Runtime
resources must therefore be loaded with `importlib.resources`, not by resolving
paths relative to `__main__.__file__`.

The build verifies that these required data files are present before creating the
Debian package:

```text
_internal/jotta_gui/resources/jotta-gui.svg
_internal/jotta_gui/ui/styles/dark.qss
_internal/jotta_gui/config/backup_ignore_presets.toml
```

If one of them is missing, `tools/build_deb.py` fails before `dpkg-deb` is run.
