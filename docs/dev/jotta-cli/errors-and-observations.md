# Errors and observed behaviour

This file records concrete behaviour encountered during Jotta GUI development. It is intentionally separate from the normative command reference.

## Version under observation

```text
jottad version    : 0.17.159692
jotta-cli version : 0.17.159692
```

Linux, August 2026.

## Sync trigger rejected in automatic mode

State:

```json
{
  "Enabled": true,
  "Automatic": true,
  "SyncState": 1
}
```

Command:

```text
jotta-cli sync trigger
```

Observed error:

```text
ERROR  sync is not setup as triggered. run 'jotta-cli sync stop' and then retry
```

Exit code: 1.

Interpretation: consistent with official rule that one-shot trigger is only permitted when continuous Sync is not enabled.

## `sync stop` changes `Automatic`

Before:

```text
Automatic: true
```

After `jotta-cli sync stop`:

```text
Automatic: null
```

`Enabled` remained true and `SyncState` remained `1`.

Therefore `Enabled` is not equivalent to automatic mode and `SyncState == 1` is not sufficient to distinguish automatic vs triggered configuration.

## Human status can omit actual Sync root

Captured states with both `Automatic: true` and `Automatic: null` produced human-readable output containing only a configured backup path, not the JSON Sync `RootPath`.

Parser rule: no matching Sync root -> unknown runtime activity.

## Trigger database timeout before daemon restart

Observed sequence in jottad log:

```text
jottad.sync.setup-check: .../.jottad/sync/root
Could not load selective sync data: .../selective.dat: no such file or directory
Error opening database timeout
```

CLI returned `ERROR timeout` after roughly 10 seconds.

After `systemctl --user restart jottad`, the database timeout no longer occurred.

Do not assume missing `selective.dat` is the cause; selective sync is optional according to official setup docs.

## Trigger case collision

After daemon restart, trigger reached actual Sync scanning and failed with an error of the form:

```text
Could not perform triggered sync: ... already exists with different case: Case Collision in tree
```

The daemon then uploaded diagnostics. The CLI call took substantially longer before returning, even though the underlying Sync error had already been found.

Implications:

- trigger is legitimately long-running;
- stderr should be retained even for long operations;
- diagnostics upload can extend completion time;
- a future Diagnostics page should detect case-collision errors and offer a local case-insensitive collision scan.

## Successful triggered Sync

After correcting the conflicting image name:

```text
jotta-cli sync trigger
2026-08-10 20:18:12.048 +0200 CEST :: Finished
exit=0
```

Observed duration: about 49 seconds.

After completion:

```text
Automatic: null
```

This is the reference successful one-shot trigger behaviour currently captured as `linux-triggered`.

## `sync log` availability

At one point:

```text
jotta-cli sync log -n20
ERROR  syncapp: not setup
```

while JSON still reported Sync configuration. Treat `sync log` as dependent on internal/runtime setup, not merely presence of `Sync.RootPath`.

## Backup scan noise vs errors

Observed jottad backup logs included many lines such as:

```text
Ignored .../.venv/bin/python : not regular file (mode: Lrwxrwxrwx)
```

These describe symlinks/special-file handling and are not necessarily failures.

Diagnostics should classify log records by severity/context rather than grepping every `Ignored` line as an error.

## Known documentation conflicts

### Config syntax

Release 0.16.126924 removed `config set/get`, but some official pages still show those forms.

### Backup removal

Older help-center text says `rem` does not remove the remote folder. Release 0.17.158308 says removing a backup folder places it in server Trash.

### Download information command name

Official materials across versions use multiple names (`downloadinfo`, `downloadinformation`, historically `downloaderrors`).

Resolution rule: capture the installed binary help and record the version.
