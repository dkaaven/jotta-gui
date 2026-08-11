from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """Version information reported by ``jotta-cli version``.

    ``remote_version`` is the update target reported by Jottacloud itself. The GUI
    does not consult a separate release service, so this remains useful offline and
    stays aligned with the installed CLI's own update mechanism.
    """

    cli_version: str | None = None
    daemon_version: str | None = None
    remote_version: str | None = None
    release_notes_url: str | None = None

    @property
    def update_available(self) -> bool | None:
        """Whether the reported remote version is newer than the installed CLI.

        Observed on jotta-cli 0.17.176206: when no update is available, the
        command omits ``remote version`` entirely. A missing remote version is
        therefore treated as "no newer version reported" when the installed CLI
        version itself is valid. Unknown version formats remain unknown.
        """

        current = _numeric_version(self.cli_version)
        if current is None:
            return None

        if self.remote_version is None:
            return False

        remote = _numeric_version(self.remote_version)
        if remote is None:
            return None

        width = max(len(current), len(remote))
        current += (0,) * (width - len(current))
        remote += (0,) * (width - len(remote))
        return remote > current



def _numeric_version(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None

    parts = value.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)
