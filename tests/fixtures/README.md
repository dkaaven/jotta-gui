# Captured jotta-cli fixtures

`captured/` contains sanitized output from the real `jotta-cli`. These fixtures complement the small synthetic unit-test payloads and protect the parsers from CLI format changes.

Configuration and human-readable runtime output are intentionally modeled separately:

- `status.json` determines the configured Sync mode from `Sync.Automatic`
- `runtime.txt` is optional activity evidence from human-readable `jotta-cli status`
- absence of the Sync root in `runtime.txt` means the activity is unknown, not inactive

Example capture:

```bash
uv run python tools/capture_cli_fixtures.py linux-active \
  --scenario automatic-listening \
  --sync-mode automatic \
  --runtime-state listening
```

A triggered-mode capture with no visible Sync runtime block can use:

```bash
uv run python tools/capture_cli_fixtures.py linux-triggered \
  --scenario triggered-after-complete \
  --sync-mode triggered \
  --runtime-state unknown
```

Each capture contains:

- `status.json` from `jotta-cli status --json`
- `runtime.txt` from `jotta-cli status`
- `metadata.json` with separate expected configuration and runtime observations

The capture command is a thin wrapper around `jotta_gui.devtools.fixtures`. The capture logic replaces the account email, full name, hostname, Sync root, backup names, backup paths, device IDs, home directory, and local username. Review captured files before committing them because `jotta-cli` may add new fields in future versions.

Schema 1 fixtures remain readable, but `expected_sync_state` is intentionally ignored because it mixed configuration with runtime activity. New captures use schema 2.
