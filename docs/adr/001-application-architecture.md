
# ADR-0001: Feature-oriented layered architecture

- Status: Accepted
- Date: 2026-08-09

## Context

Jotta GUI must coordinate PySide6 UI state, asynchronous `jotta-cli` commands, output parsing, and local system information.

Keeping this logic in pages or `MainWindow` would tightly couple presentation and Jottacloud behavior as the project grows.

## Decision

Use four clear layers:

```text
UI
 ↓
Application
 ↓
Jotta / System
```

### UI

`jotta_gui/ui/`

Renders state and emits user intent. It does not construct, execute, or parse Jotta commands.

### Application

`jotta_gui/application/`

Owns application-wide state and coordinates workflows such as startup, refresh, Sync start/stop, pending state, and error recovery.

### Jotta

`jotta_gui/jotta/`

Owns all Jottacloud-specific commands, parsing, models, and behavior. It is organized by feature.

A generic `JottaRunner` executes commands but does not understand feature semantics.

### System

`jotta_gui/system/`

Contains local OS functionality unrelated to Jottacloud.

## Consequences

### Positive

- predictable code locations
- smaller modules
- easier parser and behavior tests
- CLI changes have a limited blast radius
- UI remains independent of Jotta command syntax

### Trade-offs

- more files and modules
- simple workflows may require an application coordinator

## Rejected Alternatives

**CLI logic in pages:** couples UI to Jottacloud and makes testing harder.

**One large Jotta client class:** would accumulate unrelated Sync, Backup, status, and transfer behavior.

**Generic command framework:** unnecessary abstraction for the current project.
