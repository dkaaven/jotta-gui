# Jottacloud CLI developer reference

This directory documents `jotta-cli` as an external dependency of Jotta GUI.

The goal is not to duplicate Jottacloud's end-user documentation. It is to keep a version-aware engineering reference for command construction, parsing, state modelling, error handling, and future GUI features.

## Evidence levels

Every non-trivial behavioural statement should be understood as one of:

- **Official** — documented by Jottacloud.
- **Observed** — reproduced against a specific installed CLI version or preserved in a captured fixture.
- **Inferred** — best explanation of observed behaviour, but not guaranteed by Jottacloud.
- **Unknown** — semantics have not been established and must not be invented in application code.

When official documentation and the installed binary disagree, the installed binary wins for command syntax and the disagreement must be recorded.

## Reference version

The initial reference is based on:

- `jotta-cli` / `jottad` 0.17.159692
- Linux
- observed during Jotta GUI development in August 2026

Version-specific command syntax should be refreshed after upgrading the CLI.

## Files

- [commands.md](commands.md) — complete top-level command inventory and known subcommands/options.
- [status.md](status.md) — human and JSON status output, parsing rules, and state semantics.
- [sync.md](sync.md) — Sync setup, modes, operations, logging, and observed edge cases.
- [backup-and-ignores.md](backup-and-ignores.md) — continuous backup, scans, pause/resume, and ignore rules.
- [transfers-and-remote.md](transfers-and-remote.md) — archive, download, list, observe, ls, share, and trash.
- [configuration-and-runtime.md](configuration-and-runtime.md) — config, daemon/runtime, logs, completion, remote jottad, and webhooks.
- [errors-and-observations.md](errors-and-observations.md) — errors and undocumented behaviour encountered by Jotta GUI.
- [capture.md](capture.md) — how to capture the exact CLI help tree from an installed version.
- [sources.md](sources.md) — official sources used by this reference.

## Rules for Jotta GUI

1. UI code must never construct `jotta-cli` commands directly.
2. Command syntax belongs in `jotta_gui/jotta/`.
3. Prefer machine-readable output when the CLI provides it.
4. Preserve unknown values rather than assigning guessed semantics.
5. Command completion is not the same thing as requested state being reached.
6. Long-running commands must remain asynchronous.
7. Capture real CLI output when adding or changing parsers.
8. Record observed errors before adding special-case GUI behaviour.
