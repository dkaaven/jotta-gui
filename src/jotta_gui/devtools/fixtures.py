from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import getpass
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Sequence

DEFAULT_FIXTURE_ROOT = Path("tests") / "fixtures" / "captured"
SANITIZED_HOME = "/home/example"
SANITIZED_SYNC_ROOT = f"{SANITIZED_HOME}/Jotta"
EMAIL_PATTERN = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")


@dataclass(frozen=True, slots=True)
class Capture:
    status: dict[str, Any]
    runtime: str
    replacements: dict[str, str]


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    capture = sanitize_capture(capture_cli(args.binary))
    destination = write_capture(
        name=args.name,
        capture=capture,
        scenario=args.scenario,
        expected_sync_mode=args.sync_mode,
        expected_runtime_state=args.runtime_state,
        output_root=args.output_root,
    )

    print(f"Captured sanitized fixtures in {destination.resolve()}")
    print("Review the files before committing them.")
    return 0


def capture_cli(binary: str = "jotta-cli") -> Capture:
    status_output = run_cli(binary, "status", "--json")
    runtime_output = run_cli(binary, "status")
    status = json.loads(status_output)

    if not isinstance(status, dict):
        raise ValueError("jotta-cli status --json did not return a JSON object")

    return Capture(status=status, runtime=runtime_output, replacements={})


def sanitize_capture(capture: Capture) -> Capture:
    status, replacements = sanitize_status(capture.status)
    runtime = sanitize_runtime(capture.runtime, replacements)
    return Capture(status=status, runtime=runtime, replacements=replacements)


def sanitize_status(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    sanitized = deepcopy(data)
    replacements: dict[str, str] = {}

    user = sanitized.get("User")
    if isinstance(user, dict):
        replace_value(user, "Email", "user@example.com", replacements)
        replace_value(user, "Fullname", "Example User", replacements)
        replace_value(user, "Hostname", "example-host", replacements)

    sync = sanitized.get("Sync")
    if isinstance(sync, dict):
        replace_value(sync, "RootPath", SANITIZED_SYNC_ROOT, replacements)

    for index, backup in enumerate(backup_entries(sanitized), start=1):
        replace_value(backup, "Name", f"Backup {index}", replacements)
        replace_value(
            backup,
            "Path",
            f"{SANITIZED_HOME}/backup-{index}",
            replacements,
        )
        replace_value(backup, "DeviceID", f"device-{index}", replacements)

    return sanitized, replacements


def sanitize_runtime(output: str, replacements: dict[str, str]) -> str:
    sanitized = output
    all_replacements = dict(replacements)

    home = str(Path.home())
    if home and home != "/":
        all_replacements.setdefault(home, SANITIZED_HOME)

    username = getpass.getuser()
    if username:
        all_replacements.setdefault(username, "example")

    for original, replacement in sorted(
        all_replacements.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if original:
            sanitized = sanitized.replace(original, replacement)

    sanitized = EMAIL_PATTERN.sub("user@example.com", sanitized)
    return sanitized.strip() + "\n"


def write_capture(
    name: str,
    capture: Capture,
    scenario: str | None = None,
    expected_sync_mode: str | None = None,
    expected_runtime_state: str | None = None,
    output_root: Path = DEFAULT_FIXTURE_ROOT,
) -> Path:
    destination = output_root / safe_name(name)
    destination.mkdir(parents=True, exist_ok=True)

    (destination / "status.json").write_text(
        json.dumps(capture.status, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (destination / "runtime.txt").write_text(capture.runtime, encoding="utf-8")
    (destination / "metadata.json").write_text(
        json.dumps(
            {
                "schema": 2,
                "scenario": scenario,
                "expected_sync_mode": expected_sync_mode,
                "expected_runtime_state": expected_runtime_state,
                "commands": {
                    "status": "jotta-cli status --json",
                    "runtime": "jotta-cli status",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return destination


def backup_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    backup = data.get("Backup")
    if not isinstance(backup, dict):
        return []

    state = backup.get("State")
    if not isinstance(state, dict):
        return []

    enabled = state.get("Enabled")
    if not isinstance(enabled, dict):
        return []

    backups = enabled.get("Backups")
    if not isinstance(backups, list):
        return []

    return [item for item in backups if isinstance(item, dict)]


def replace_value(
    target: dict[str, Any],
    key: str,
    replacement: str,
    replacements: dict[str, str],
) -> None:
    original = target.get(key)
    if isinstance(original, str) and original:
        replacements[original] = replacement
        target[key] = replacement


def run_cli(binary: str, *arguments: str) -> str:
    result = subprocess.run(
        [binary, *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def safe_name(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-").replace(" ", "-")
    if not normalized or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-"
        for character in normalized
    ):
        raise ValueError(
            "Capture name may only contain letters, numbers, spaces, '_' and '-'"
        )
    return normalized


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture and sanitize jotta-cli output for parser regression tests."
    )
    parser.add_argument("name", help="Fixture name, for example 'linux-active'")
    parser.add_argument(
        "--scenario",
        default=None,
        help="Human-readable scenario name for the capture.",
    )
    parser.add_argument(
        "--sync-mode",
        choices=("automatic", "triggered", "unknown"),
        default=None,
        help="Expected configured Sync mode from status --json.",
    )
    parser.add_argument(
        "--runtime-state",
        choices=("listening", "triggered", "unknown"),
        default=None,
        help="Expected activity observation from human-readable status.",
    )
    parser.add_argument("--binary", default="jotta-cli")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_FIXTURE_ROOT,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)
