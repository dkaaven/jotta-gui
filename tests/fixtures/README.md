# Captured jotta-cli fixtures

`captured/` is reserved for sanitized output from the real `jotta-cli`.
Do not hand-author data and label it as captured evidence.

Create a fixture from the repository root with:

```bash
uv run python tools/capture_cli_fixtures.py linux-active \
  --scenario automatic-listening \
  --sync-mode automatic \
  --runtime-state listening
```

Each capture contains:

- `status.json` from `jotta-cli status --json`
- `runtime.txt` from `jotta-cli status`
- `metadata.json` describing the intended scenario and expected observations

The two status commands are separate and therefore not atomic. The JSON output is
used for configured state; human-readable status is runtime evidence only.

Review every generated fixture before committing it. Future CLI versions may expose
new fields that the sanitizer does not yet know about.
