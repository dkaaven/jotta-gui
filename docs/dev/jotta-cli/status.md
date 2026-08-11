# Status output and state semantics

`status` is the primary read model for Jotta GUI.

## Commands

```text
jotta-cli status
jotta-cli status -v
jotta-cli status --json
```

Official documentation says `-v` includes details about files that could not be backed up.

## Human-readable status

Typical sections are:

```text
Account
Usage
Device

Sync:
  Path
  Files
  Mode
  Status

Backups:
  Path
  Files
  Status
```

### Important observed limitation

**Observed on 0.17.159692:** the human output does not reliably include the configured Sync root.

During Jotta GUI testing, both of these states were captured with a human-readable `status` containing only a backup path under the `Sync` heading and no actual Sync root block:

- JSON `Sync.Automatic == true`
- JSON `Sync.Automatic == null`

Therefore:

- absence of the Sync root in human output does **not** mean Sync is stopped;
- absence does **not** mean Sync is idle;
- a parser must return an unknown/no-observation state rather than inventing semantics.

## JSON status

Jotta GUI should prefer `status --json` for configured state and counts.

Observed Sync excerpt:

```json
{
  "Enabled": true,
  "Automatic": true,
  "RootPath": "/home/example/Jotta",
  "SyncState": 1
}
```

Observed triggered/manual configuration:

```json
{
  "Enabled": true,
  "Automatic": null,
  "RootPath": "/home/example/Jotta",
  "SyncState": 1
}
```

## `Sync.Automatic`

Observed mapping on 0.17.159692:

| JSON value | Jotta GUI meaning | Confidence |
|---|---|---|
| `true` | automatic/continuous Sync configured | Observed |
| `null` / missing | triggered/manual Sync configuration after `sync stop` | Observed |
| other | unknown | Unknown |

This mapping was verified by command behaviour:

- when `Automatic == true`, `sync trigger` rejects the operation because active Sync is enabled;
- after `sync stop`, `Automatic` becomes null and a triggered sync is permitted;
- after a successful one-shot trigger, `Automatic` remains null.

## `Sync.SyncState`

Observed value `1` occurred in both automatic and triggered/manual configurations.

**Do not assign semantics to the integer without additional evidence.** It must not be used to infer automatic vs triggered mode.

## Runtime/activity observations

Human-readable values observed include:

```text
Mode: listening to events
Mode: manually triggered
Status: Checking for changes...
```

These values describe runtime/activity evidence, not the configured mode source of truth.

A useful internal separation is:

```text
Configured mode  <- JSON Sync.Automatic
Activity          <- human status when a matching Sync root is present
Pending operation <- application workflow (starting/stopping/triggering)
```

## Captured fixtures

Captured status fixtures should preserve both outputs because the commands are separate and therefore not atomic:

```text
status.json   <- jotta-cli status --json
runtime.txt   <- jotta-cli status
metadata.json <- expected semantics / scenario
```

A state can change between the two commands. Fixture names describe the intended scenario but metadata and captured output are the evidence.
