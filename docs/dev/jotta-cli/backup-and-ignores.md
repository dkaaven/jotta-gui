# Backup and ignore rules

## Continuous backup

Add a backup root:

```text
jotta-cli add PATH
```

Remove a backup root:

```text
jotta-cli rem PATH
```

Trigger backup scans:

```text
jotta-cli scan ...
```

Use installed help capture for exact `scan` argument forms.

## Important `rem` documentation conflict

Older/current help-center text says removing a folder from backup does not delete it from Jottacloud.

However, release 0.17.158308 notes state:

> When removing a backup folder it is placed in trash on the server.

Jotta GUI targets 0.17.159692, so `rem` must be treated as potentially destructive to the remote backup set. Verify current binary/help/behaviour before exposing removal in the GUI.

## Pause and resume

Global:

```text
jotta-cli pause DURATION
jotta-cli resume
```

Documented duration examples:

```text
5m
6h30m
```

Release notes added per-backup pause/resume using `--backup`. Capture current syntax before implementing.

## Scan interval

The `scaninterval` config controls periodic backup scanning. Official docs say a value of `0` enables filesystem-event/realtime triggering.

The exact 0.17 config command syntax must come from installed help because older docs use the removed `config set` form.

## Ignore rules

### Add

Backup-specific:

```text
jotta-cli ignores add --pattern PATTERN --backup BACKUP
```

Global to all backups:

```text
jotta-cli ignores add --pattern PATTERN
```

### Remove

```text
jotta-cli ignores rem --pattern PATTERN --backup BACKUP
```

Capture whether global removal is supported/what it means before assuming omission of `--backup` is valid for `rem`.

### List

```text
jotta-cli ignores list --backup BACKUP
jotta-cli ignores list
```

Without `--backup`, official docs say rules for all backups are listed.

### Test

```text
jotta-cli ignores test --pattern PATTERN --path PATH
```

Use quotes around glob patterns so the shell does not expand them before the CLI receives them.

## Pattern semantics

Official pattern rules:

```text
*    matches everything except /
**   matches everything
**/  matches zero or more directories
```

Examples:

```text
**.png
*.png
foo/*.png
foo/**.png
**/foo/**.png
**/.ignoreme
```

Patterns are relative to the backup root. Leading `/`, leading/trailing whitespace, and trailing slashes are normalized/ignored according to official documentation.

Some built-in patterns cannot be removed. Documented examples include `.DS_Store`, `.Thumbs.db`, and `.desktop.ini` patterns.

## Jotta GUI rule editor

Implemented design:

- Jotta's actual ignore list is the source of truth;
- presets are convenience groups, not hidden rules;
- shipped presets live in `src/jotta_gui/config/backup_ignore_presets.toml`;
- show the concrete pattern created by every preset;
- support adding/removing preset patterns and exact custom patterns;
- re-list rules from Jotta after every successful mutation;
- do not maintain a separate database of active ignore state.

The exact stdout format of `jotta-cli ignores list` has not yet been captured. Until
that happens, the GUI deliberately displays the command output verbatim rather than
guessing a parser contract. Capture real output before replacing it with structured
rule rows. `ignores test` remains a planned follow-up once that workflow is added to
the application layer.

Initial useful development presets:

```text
**/.git
**/.venv
**/__pycache__
**/.pytest_cache
**/.ruff_cache
**/node_modules
```

Only the first three have been explicitly discussed/used during Jotta GUI development; the others are proposed convenience presets and should remain opt-in.

## Logging ignored files

Official config option `logscanignores` causes jottad to log why scanned files were ignored. This will be useful for the future Diagnostics page.
