⚠️ ChatGPT was heavily used, this is an AI assisted repo ⚠️

# Jotta GUI

A PySide6 desktop interface for `jotta-cli`.

This is my playground to test and learn. I use ChatGPT to support me on this journey.
You are free to copy and play around on your own.

The application uses a layered architecture:

```text
UI
 ↓
Application
 ↓
Jotta / System
```

Run the application with:

```bash
uv run jotta-gui
```

## Testing

Run the full test suite:

```bash
uv run pytest
```

Run only tests that do not require Qt:

```bash
uv run pytest -m "not qt"
```

Run only Qt-dependent controller, runner, and widget tests:

```bash
uv run pytest -m qt
```

The Qt tests use the offscreen platform automatically so they can run headlessly.

### Captured CLI fixtures

Capture sanitized output from the local CLI:

```bash
uv run python tools/capture_cli_fixtures.py linux-active --sync-state active
```

Run only tests backed by captured `jotta-cli` output:

```bash
uv run pytest -m captured
```

See `tests/fixtures/README.md` before committing captured fixtures.
