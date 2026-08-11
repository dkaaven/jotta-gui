# Configuration and runtime

## Components

The command-line client consists of:

```text
jottad     daemon: filesystem work, transfers, auth, state
jotta-cli  command interface to jottad
```

`jotta-cli` commands often return information supplied by the long-running daemon rather than performing all work inside the CLI process.

## Version

```text
jotta-cli version
```

Observed 0.17.159692 output fields:

```text
jottad executable
jottad appdata
jottad logfile
jottad version
jotta-cli version
release notes
```

Use this for Diagnostics/About and to associate captured behaviour with a version.

## Linux service

Current Debian documentation installs jottad into a user systemd slice. Common developer operations include:

```text
systemctl --user status jottad
systemctl --user restart jottad
```

Package setup uses `run_jottad` to enable/start the user daemon. `loginctl enable-linger USER` can keep a user session/service available from boot without an interactive login.

Jotta GUI should not restart jottad automatically unless a future explicit repair workflow is designed.

## Config

Current release notes say version 0.16.126924 removed separate `config set` and `config get`, combining both tasks in `config`.

This means older/current web examples using `config set` are not trustworthy syntax for 0.17.159692.

Run:

```text
jotta-cli config --help
jotta-cli config
```

against the installed binary before adding config commands to Jotta GUI.

### Documented settings

Official configuration docs/release notes have documented at least:

```text
downloadrate
uploadrate
checksumreadrate
checksumthreads
ignorehiddenfiles
maxuploads
maxdownloads
scaninterval
webhookstatusinterval
logscanignores
slowmomode
logtransfers
screenshotscapture
timeformat
usesiunits
sharecapturedscreenshots
proxy
syncpaused
photosmonthastext
```

Not all settings are guaranteed to exist on every current platform/version. `jotta-cli config` output from the target binary is authoritative.

### Rates

Documented rate examples:

```text
512k
1m
10m
0       unlimited
```

`checksumreadrate` throttles disk reading for checksumming.

### Concurrent transfers

Older configuration docs describe `maxuploads` and `maxdownloads` as 1–6, while 0.17 release notes say the maximum changed from 6 to 12 in 0.17.148769. Treat release/version-specific values as authoritative and validate CLI errors rather than hard-coding old limits.

### Hidden files

`ignorehiddenfiles=true` excludes hidden files from backup. Official docs say hidden files inside an archived directory are also skipped, while a hidden path explicitly selected for archive can still be uploaded.

Release notes state Sync always includes hidden files, so do not assume the backup setting applies identically to Sync despite older release-note wording.

### `logscanignores`

Useful for Diagnostics. When enabled, jottad logs reasons for ignored files during scans.

### `slowmomode`

Reduces scanning resource pressure. Older docs state range 0–50; confirm current validation before building a slider.

### `logtransfers`

When enabled, logs transfer HTTP results rather than only transfer errors.

## Logfile

Print path:

```text
jotta-cli logfile
```

Stream through CLI:

```text
jotta-cli tail
```

Observed Linux appdata/log path for the development setup was under `~/.jottad/`, but Jotta GUI should discover paths through CLI/runtime information rather than hard-code them.

## Diagnostics log model

Future Diagnostics page should:

- locate the active logfile;
- show errors only / warnings / full log;
- group surrounding context lines;
- identify subsystem (`sync`, `backup`, transfers, auth, etc.) when possible;
- correlate path errors with filesystem diagnostics;
- never treat every line containing words like `Ignored` as an error.

## Login/logout

```text
jotta-cli login
jotta-cli logout
```

Login is interactive and uses a Personal Login Token according to official docs.

Logout clears credentials/stops backup according to command help; treat it as a significant account action.

## Remote daemon control

Global options:

```text
--host HOST
--port PORT
```

Default host is loopback and default port is 14443 in official command help.

A remote jottad must be configured to listen on a reachable interface. This expands the daemon's network exposure and should not be automatically enabled by Jotta GUI.

## Shell completion

Supported/documented generators:

```text
jotta-cli completion bash
jotta-cli completion zsh
jotta-cli completion fish
```

PowerShell support was added in release notes; verify current help.

Completion can dynamically expose remote paths, backups, and transfer IDs, making it useful for manual exploration during development.

## Webhooks

Official commands:

```text
jotta-cli webhook add URL
jotta-cli webhook rem URL
```

Official docs describe messages for daemon start, stop, and periodic status. Webhook status interval is configurable.

## `dump`

`jotta-cli dump` is described in release notes as a simplified JSON representation of the backup set. It is potentially useful for Diagnostics or deeper backup modelling, but the schema must be captured before use.
