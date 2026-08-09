
# Jotta GUI Architecture

## Purpose

Jotta GUI is a PySide6 desktop interface for `jotta-cli`.

The project keeps UI, application workflows, Jottacloud integration, and OS integration separate.

## Layers

```text
UI
 ↓
Application
 ↓
Jotta / System
```

### UI — `jotta_gui/ui/`

Responsible for:

- rendering state
- collecting user intent
- navigation and reusable widgets

Must not execute or parse `jotta-cli` commands.

### Application — `jotta_gui/application/`

Responsible for:

- application-wide state
- command workflows
- pending states
- refresh and error handling

`MainWindow` should remain focused on window layout and navigation.

### Jotta — `jotta_gui/jotta/`

Owns all Jottacloud-specific behavior.

Organized by feature:

```text
jotta/
├── runner.py
├── status/
├── sync/
├── backup/
└── transfers/
```

Feature modules use these conventions:

- `control.py` — commands that change state
- `status.py` / `query.py` — read-only queries
- `parser.py` — CLI output to models
- `models.py` — dataclasses and value objects

`runner.py` only executes commands and returns stdout, stderr, and result state.

### System — `jotta_gui/system/`

OS functionality unrelated to Jottacloud, such as disk usage.

## Project Structure

```text
src/jotta_gui/
├── application/
│   ├── controller.py
│   └── state.py
├── jotta/
│   ├── runner.py
│   ├── status/
│   ├── sync/
│   ├── backup/
│   └── transfers/
├── system/
├── ui/
│   ├── components/
│   ├── pages/
│   └── styles/
└── resources/

tests/
├── fixtures/
├── jotta/
└── system/
```

## Rules

- UI emits intent; it does not know CLI syntax.
- Jotta modules never depend on UI modules.
- Global state belongs in the application layer, not widgets.
- CLI operations must not block the Qt GUI thread.
- Long-running operations must show a pending state.
- A completed command does not necessarily mean the requested state is reached; verify when needed.
- Undocumented Jotta values must not be given assumed semantics.
- Prefer small feature modules over one large Jotta client class.

## Testing

Prioritize tests for parsers and Jotta behavior using captured CLI output.

GUI tests can be added where widget behavior itself is important.
