from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from jotta_gui.application.state import ApplicationState, BackupIgnoreState
from jotta_gui.jotta.config import ConfigEntry, JottaConfig
from jotta_gui.jotta.models import (
    AccountStatus,
    BackupStatus,
    FileStats,
    JottaSnapshot,
    SyncActivity,
    SyncMode,
    SyncStatus,
)
from jotta_gui.jotta.version import VersionInfo
from jotta_gui.system.storage import DiskUsage

DEMO_CAPTURED_AT = datetime(2026, 8, 12, 17, 30, tzinfo=timezone.utc)

DEMO_IGNORE_RULES: dict[str, tuple[str, ...]] = {
    "Documents": ("**/.git", "**/.venv", "**/__pycache__"),
    "Photos": ("**/.DS_Store",),
    "Projects": ("**/.git", "**/node_modules", "**/.ruff_cache"),
}

DEMO_CONFIG_VALUES: tuple[tuple[str, str], ...] = (
    ("downloadrate", "0"),
    ("uploadrate", "0"),
    ("checksumreadrate", "0"),
    ("maxuploads", "6"),
    ("maxdownloads", "6"),
    ("scaninterval", "1h"),
    ("ignorehiddenfiles", "false"),
    ("slowmomode", "0"),
    ("logscanignores", "true"),
    ("logtransfers", "false"),
)


def build_demo_state() -> ApplicationState:
    """Build deterministic, sanitized state for screenshots and demonstrations."""

    snapshot = JottaSnapshot(
        account=AccountStatus(
            email="user@example.com",
            fullname="Example User",
            hostname="jotta-demo",
            brand="Jottacloud",
            capacity=5_000_000_000_000,
            usage=436_200_000_000,
            subscription_code=1,
            subscription_name="Home",
            product_name="Home 5 TB",
            device_name="Demo Workstation",
            device_type=12,
        ),
        sync=SyncStatus(
            enabled=True,
            mode=SyncMode.AUTOMATIC,
            activity=SyncActivity.LISTENING,
            root_path=Path("/home/example/Jotta"),
            local=FileStats(files=118_408, bytes=186_880_000_000),
            remote=FileStats(files=118_412, bytes=186_910_000_000),
            folder_count=24,
            activity_text="Listening for filesystem changes",
            runtime_mode_text="listening to events",
            cli_sync_state=1,
        ),
        backups=(
            BackupStatus(
                name="Documents",
                path=Path("/home/example/Documents"),
                count=FileStats(files=24_861, bytes=38_400_000_000),
                device_id="demo-device",
                last_update_ms=1_754_994_900_000,
                last_scan_started_ms=1_754_994_600_000,
                next_backup_ms=None,
            ),
            BackupStatus(
                name="Photos",
                path=Path("/home/example/Pictures"),
                count=FileStats(files=68_214, bytes=211_700_000_000),
                device_id="demo-device",
                last_update_ms=1_754_994_600_000,
                last_scan_started_ms=1_754_994_300_000,
                next_backup_ms=None,
            ),
            BackupStatus(
                name="Projects",
                path=Path("/home/example/Projects"),
                count=FileStats(files=9_732, bytes=12_900_000_000),
                device_id="demo-device",
                last_update_ms=1_754_994_300_000,
                last_scan_started_ms=1_754_994_000_000,
                next_backup_ms=None,
            ),
        ),
        captured_at=DEMO_CAPTURED_AT,
    )

    return ApplicationState(
        connected=True,
        snapshot=snapshot,
        disk_usage=DiskUsage(
            total=1_000_000_000_000,
            used=641_300_000_000,
            free=358_700_000_000,
        ),
        version=VersionInfo(
            cli_version="0.17.176206",
            daemon_version="0.17.176206",
            release_notes_url="https://docs.jottacloud.com/articles/1461561",
            daemon_executable="/usr/bin/jottad",
            appdata_path="/home/example/.jottad",
            logfile_path="/home/example/.jottad/jottabackup.log",
        ),
        config=build_demo_config(),
        backup_ignores=BackupIgnoreState(
            backup_name="Documents",
            output=format_demo_ignore_rules("Documents", DEMO_IGNORE_RULES["Documents"]),
        ),
    )


def build_demo_config(
    values: tuple[tuple[str, str], ...] = DEMO_CONFIG_VALUES,
) -> JottaConfig:
    entries = tuple(ConfigEntry(name=name, value=value) for name, value in values)
    raw_output = "\n".join(f"{name} : {value}" for name, value in values)
    return JottaConfig(entries=entries, raw_output=raw_output)


def format_demo_ignore_rules(backup_name: str, rules: tuple[str, ...]) -> str:
    lines = [f"Backup: {backup_name}"]
    lines.extend(f"  {pattern}" for pattern in rules)
    return "\n".join(lines)
