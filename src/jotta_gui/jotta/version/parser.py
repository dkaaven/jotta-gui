from __future__ import annotations

from .models import VersionInfo


_FIELD_NAMES = {
    "jotta-cli version": "cli_version",
    "jottad version": "daemon_version",
    "remote version": "remote_version",
    "release notes": "release_notes_url",
    "jottad executable": "daemon_executable",
    "jottad appdata": "appdata_path",
    "jottad logfile": "logfile_path",
}


def parse_version_output(output: str) -> VersionInfo:
    """Parse the stable labelled fields from ``jotta-cli version`` output.

    The command may prepend an update-available banner. Only labelled fields are
    interpreted; prose in the banner is intentionally ignored.
    """

    values: dict[str, str] = {}
    for line in output.splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            continue

        target = _FIELD_NAMES.get(key.strip().casefold())
        value = value.strip()
        if target and value:
            values[target] = value

    if not any(name in values for name in ("cli_version", "daemon_version", "remote_version")):
        raise ValueError("jotta-cli version output contained no recognized version fields")

    return VersionInfo(
        cli_version=values.get("cli_version"),
        daemon_version=values.get("daemon_version"),
        remote_version=values.get("remote_version"),
        release_notes_url=values.get("release_notes_url"),
        daemon_executable=values.get("daemon_executable"),
        appdata_path=values.get("appdata_path"),
        logfile_path=values.get("logfile_path"),
    )
