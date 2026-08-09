# Captured jotta-cli fixtures

`captured/` contains sanitized output from the real `jotta-cli`. These fixtures complement the small synthetic unit-test payloads and protect the parsers from CLI format changes.

Capture the current state with:

```bash
uv run python tools/capture_cli_fixtures.py linux-active --sync-state active
```

For a stopped Sync service, capture a separate fixture:

```bash
uv run python tools/capture_cli_fixtures.py linux-stopped --sync-state inactive
```

Each capture contains:

- `status.json` from `jotta-cli status --json`
- `runtime.txt` from `jotta-cli status`
- `metadata.json` with the expected runtime state when known

The capture command is a thin wrapper around `jotta_gui.devtools.fixtures`. The capture logic replaces the account email, full name, hostname, Sync root, backup names, backup paths, device IDs, home directory, and local username. Review captured files before committing them because `jotta-cli` may add new fields in future versions.
