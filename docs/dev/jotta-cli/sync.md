# Sync

## Setup

Official setup command:

```text
jotta-cli sync setup --root ROOT_FOLDER
```

Setup is interactive and includes:

- disclaimer confirmation;
- reporting mode selection (`full`, `stackonly`, or `off` in official documentation);
- absolute root confirmation;
- optional selective-sync setup.

Selective sync can be configured later. Capture exact current subcommands before implementing it in Jotta GUI.

## Modes and operations

### Continuous / automatic Sync

```text
jotta-cli sync start
```

Officially, local and cloud changes are then synchronized continuously.

Observed JSON:

```text
Sync.Automatic = true
```

### Stop continuous Sync

```text
jotta-cli sync stop
```

Observed JSON after stop:

```text
Sync.Enabled   = true
Sync.Automatic = null
Sync.SyncState = 1
```

This does not disable Sync setup; it changes it out of continuous mode.

### One-shot / triggered Sync

```text
jotta-cli sync trigger
```

Officially, this performs one synchronization and can only run while active continuous Sync is not enabled.

Observed on 0.17.159692:

- with `Automatic == true`, trigger exits with an error saying Sync is not set up as triggered and instructs the user to run `sync stop`;
- after `sync stop`, trigger is accepted;
- successful trigger can be long-running (observed ~49 seconds);
- a successful trigger printed a timestamp followed by `:: Finished` and exited 0;
- `Automatic` remained null after completion.

**GUI requirement:** do not use a short timeout for `sync trigger`. Run asynchronously and represent a pending operation.

## Runtime output

Observed runtime modes:

```text
Mode: listening to events
Mode: manually triggered
```

Only map values with verified semantics. Unknown strings remain unknown.

Human status can omit the actual Sync root entirely, so runtime parsing must match on `RootPath` and return unknown if the root is not present.

## Logs

Official commands:

```text
jotta-cli sync log -nN
jotta-cli sync log --watch
```

Observed caveat:

```text
ERROR  syncapp: not setup
```

was returned in a state where JSON still contained Sync configuration. Treat this command's availability as runtime-dependent.

## Observe transfers

```text
jotta-cli observe --sync
```

Streams individual Sync uploads/downloads and is long-running.

## Move root

```text
jotta-cli sync move NEW_ROOT_FOLDER
```

Use the CLI operation rather than manually moving the directory. Official documentation warns that manual moves can be interpreted as deletions and mirrored remotely.

## Reset

```text
jotta-cli sync reset
```

Officially clears local Sync configuration and stops Sync operation without deleting the local or remote Sync folder.

Treat this as a destructive configuration action and require explicit confirmation in any future GUI.

## Pausing Sync

Official documentation describes a `syncpaused` config setting, but documentation still shows the pre-0.16 `config set` syntax. Verify current config syntax against 0.17.159692 help before implementation.

## Observed failure: local database timeout

After `sync stop`, repeated `sync trigger` attempts initially failed after approximately 10 seconds. jottad logged:

```text
jottad.sync.setup-check: .../.jottad/sync/root
Could not load selective sync data: .../selective.dat: no such file or directory
Error opening database timeout
```

Restarting the per-user jottad service removed the database timeout and allowed the trigger operation to proceed.

Classification: **observed**, cause not established.

Do not encode "restart jottad" as an automatic repair without more evidence.

## Observed failure: case collision

After the daemon restart, triggered Sync failed with:

```text
already exists with different case: Case Collision in tree
```

The CLI then generated/uploaded diagnostics before returning, making the command appear stalled for a while.

After the conflicting filename was corrected, `sync trigger` completed successfully with exit code 0.

This error should eventually feed the Diagnostics page and Linux filesystem checks.

Release notes also mention prior fixes for Sync becoming stuck when local/remote items differed only by case. This reinforces that case handling is a known Sync concern, but the exact current collision semantics should remain evidence-driven.
