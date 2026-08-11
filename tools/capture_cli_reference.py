#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


COMMAND_HEADER = "Available Commands:"
SECTION_HEADERS = {
    "Flags:",
    "Global Flags:",
    "Additional help topics:",
    "Use \"jotta-cli [command] --help\" for more information about a command.",
}
VERSION_RE = re.compile(r"jotta-cli version\s*:\s*([^\s]+)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    output: str


def run_cli(*args: str) -> CommandResult:
    process = subprocess.run(
        ["jotta-cli", *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=15,
        check=False,
    )
    return CommandResult(args, process.returncode, process.stdout)


def sanitize(text: str) -> str:
    home = str(Path.home())
    if home:
        text = text.replace(home, "$HOME")

    username = os.environ.get("USER")
    if username and username != "root":
        text = text.replace(f"/home/{username}", "$HOME")

    return text


def parse_subcommands(output: str) -> list[str]:
    lines = output.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == COMMAND_HEADER)
    except StopIteration:
        return []

    commands: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            if commands:
                break
            continue
        if stripped in SECTION_HEADERS or stripped.endswith("Flags:"):
            break
        if not line[:1].isspace():
            break

        command = stripped.split(maxsplit=1)[0]
        if command and not command.startswith("-"):
            commands.append(command)

    return commands


def help_filename(path: tuple[str, ...]) -> str:
    return "root.txt" if not path else "__".join(path) + ".txt"


def capture_help_tree(help_dir: Path) -> list[dict[str, object]]:
    help_dir.mkdir(parents=True, exist_ok=True)
    queue: list[tuple[str, ...]] = [()]
    seen: set[tuple[str, ...]] = set()
    index: list[dict[str, object]] = []

    while queue:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)

        args = (*path, "--help") if path else ("--help",)
        result = run_cli(*args)
        output = sanitize(result.output)
        filename = help_filename(path)
        (help_dir / filename).write_text(output, encoding="utf-8")

        subcommands = parse_subcommands(output)
        index.append(
            {
                "command": list(path),
                "help_file": f"help/{filename}",
                "returncode": result.returncode,
                "subcommands": subcommands,
            }
        )

        for child in subcommands:
            queue.append((*path, child))

    return index


def version_from_output(output: str) -> str:
    match = VERSION_RE.search(output)
    return match.group(1) if match else "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture a read-only, version-specific jotta-cli help tree."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("tests/fixtures/cli-reference"),
        help="Directory that will contain the per-version capture.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    version_result = run_cli("version")
    version_output = sanitize(version_result.output)
    version = version_from_output(version_output)

    output_dir = args.output_root / version
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "version.txt").write_text(version_output, encoding="utf-8")

    index = capture_help_tree(output_dir / "help")
    metadata = {
        "schema": 1,
        "jotta_cli_version": version,
        "capture_kind": "read-only-help-tree",
        "commands": index,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Captured jotta-cli {version} reference in {output_dir}")
    print("Review generated files before committing them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
