# Command reference

## Global form

```text
jotta-cli [command]
```

Known global flags:

```text
-h, --help
--host string   jottad host, default 127.0.0.1
--port string   jottad port, default 14443
```

`jotta-cli --host HOST ...` can operate against another `jottad` instance if that daemon is configured to listen on an address reachable from the CLI host.

The exact command and flag tree for an installed version should be captured with `tools/capture_cli_reference.py`. Help output from the installed binary is the syntax authority for Jotta GUI.

## Top-level command inventory

The official command list currently contains 26 top-level commands:

| Command | Purpose | Jotta GUI relevance |
|---|---|---|
| `add` | Add a folder to continuous backup | Backup page |
| `archive` | Upload file/folder to Archive | Future transfers/archive |
| `completion` | Generate shell completion | Dev/user convenience |
| `config` | Read/change daemon configuration | Settings |
| `download` | Download remote file/folder | Future transfers |
| `dump` | Dump simplified local backup database as JSON | Diagnostics/dev |
| `help` | Command help | Dev reference |
| `ignores` | Manage backup ignore rules | Backup page |
| `list` | List transfers / completed-transfer information | Future transfers |
| `logfile` | Print jottad logfile location | Diagnostics |
| `login` | Authenticate and create/configure device | Future onboarding |
| `logout` | Clear credentials and stop backups | Account/settings |
| `ls` | Browse remote filesystem | Future remote browser |
| `observe` | Observe active transfers | Activity/diagnostics |
| `pause` | Pause daemon or backup | Backup/global controls |
| `rem` | Stop backing up a folder | Backup page |
| `resume` | Resume daemon or backup | Backup/global controls |
| `scan` | Trigger backup scan | Backup page |
| `share` | Manage/generate public links | Future sharing |
| `status` | Current system state | Core GUI |
| `sync` | Manage Sync folder | Sync page |
| `tail` | Stream jottad log | Diagnostics |
| `trash` | Manage remote trash | Future remote management |
| `version` | Show CLI/daemon version information | About/diagnostics |
| `web` | Open Jottacloud website | Optional UI action |
| `webhook` | Manage webhook endpoints | Advanced settings |

## `add`

Officially documented basic form:

```text
jotta-cli add PATH
```

Adds a folder to continuous backup.

Historical/current-release notes also document a Linux recovery flag for a previously-added path whose filesystem ID changed:

```text
jotta-cli add PATH --confirmexisting
```

Verify this flag against the installed help tree before exposing it in the GUI.

## `archive`

Known forms:

```text
jotta-cli archive PATH
jotta-cli archive PATH --remote=REMOTE_PATH
jotta-cli archive PATH --share
jotta-cli archive PATH --share --clipboard
jotta-cli archive PATH --nogui
echo DATA | jotta-cli archive -I --remote=REMOTE_PATH
```

Folder uploads can be followed using `list uploads` and `observe --uploadid=...`.

## `completion`

Officially supported shells include:

```text
jotta-cli completion bash
jotta-cli completion zsh
jotta-cli completion fish
```

Release notes also document PowerShell completion. Confirm availability in the installed help tree.

## `config`

Current release notes state that the separate `config set` and `config get` subcommands were removed in 0.16.126924 and both operations were combined into `config`.

Therefore examples in older/current help-center articles using:

```text
jotta-cli config set KEY VALUE
jotta-cli config get
```

must not be copied into Jotta GUI without checking installed `jotta-cli config --help`.

See [configuration-and-runtime.md](configuration-and-runtime.md).

## `download`

Officially documented forms include:

```text
jotta-cli download REMOTE_PATH LOCAL_DESTINATION
jotta-cli download REMOTE_PATH LOCAL_DESTINATION --merge
jotta-cli download REMOTE_PATH LOCAL_DESTINATION --merge --mergemode=metadata
jotta-cli download --abort=DOWNLOAD_ID
jotta-cli download --retry=DOWNLOAD_ID
jotta-cli download -O REMOTE_PATH
```

See [transfers-and-remote.md](transfers-and-remote.md).

## `dump`

Release notes describe `dump` as a simplified JSON dump of the local backup set/database:

```text
jotta-cli dump
```

Treat the schema as undocumented until captured and tested.

## `help`

```text
jotta-cli help
jotta-cli COMMAND --help
```

Used by the CLI-reference capture tool.

## `ignores`

Known subcommands:

```text
jotta-cli ignores add --pattern PATTERN [--backup BACKUP]
jotta-cli ignores rem --pattern PATTERN [--backup BACKUP]
jotta-cli ignores list [--backup BACKUP]
jotta-cli ignores test --pattern PATTERN --path PATH
```

See [backup-and-ignores.md](backup-and-ignores.md).

## `list`

Known forms from official transfer documentation and release notes:

```text
jotta-cli list uploads
jotta-cli list downloads
jotta-cli list downloadinfo --downloadid=DOWNLOAD_ID [--json]
```

Documentation has used both `downloadinfo`, `downloadinformation`, and historically `downloaderrors`. The installed help tree is authoritative for 0.17.159692.

Current release notes also state that `--json` exists for `list uploads` and `list downloads`.

## `logfile`

```text
jotta-cli logfile
```

Prints the active jottad logfile path.

## `login`

```text
jotta-cli login
```

Interactive login uses a Personal Login Token and device setup.

## `logout`

```text
jotta-cli logout
```

Official top-level help describes this as resetting credentials and stopping backups. Treat destructive/account consequences as significant and require explicit user intent before exposing it in the GUI.

## `ls`

```text
jotta-cli ls [REMOTE_PATH]
```

Used to browse remote `Sync`, `Backup`, `Archive`, and photo/timeline paths. Release notes document `-a` for additional information in newer releases. Capture exact flags before implementing a remote browser.

## `observe`

Known selectors:

```text
jotta-cli observe --sync
jotta-cli observe --downloads
jotta-cli observe --downloadid=DOWNLOAD_ID
jotta-cli observe --uploadid=UPLOAD_ID
```

This is a streaming/long-running command.

## `pause` / `resume`

Global pause:

```text
jotta-cli pause DURATION
jotta-cli resume
```

Release notes document per-backup variants using `--backup`; capture exact current syntax before implementation.

## `rem`

```text
jotta-cli rem PATH
```

Stops continuous backup for a path. Behaviour changed in 0.17.158308: release notes state that removing a backup folder now places it in Trash on the server. This is materially different from older help-center text saying it does not delete remote content. Treat installed-version behaviour as potentially destructive and verify before exposing it.

## `scan`

```text
jotta-cli scan ...
```

Triggers scan of one or more backup folders. Exact positional/flag syntax must come from the installed help capture.

## `share`

Top-level help describes public URL generation for a file. Release notes added broader shared-file management in 0.8. Capture current subcommands/options before implementing.

## `status`

```text
jotta-cli status
jotta-cli status -v
jotta-cli status --json
```

`--json` is heavily used by Jotta GUI. See [status.md](status.md).

## `sync`

Known commands:

```text
jotta-cli sync setup --root ROOT
jotta-cli sync start
jotta-cli sync stop
jotta-cli sync trigger
jotta-cli sync log -nN
jotta-cli sync log --watch
jotta-cli sync move NEW_ROOT
jotta-cli sync reset
```

Selective-sync subcommands/options must be captured from installed help. See [sync.md](sync.md).

## `tail`

```text
jotta-cli tail
```

Streams the jottad logfile until interrupted.

## `trash`

Release notes document at least:

```text
jotta-cli trash ls
jotta-cli trash restore ...
jotta-cli trash purge ...
```

Exact path/item syntax must come from the installed help tree.

## `version`

Observed on 0.17.159692:

```text
jotta-cli version
```

Output includes jottad executable, appdata path, logfile, jottad version, jotta-cli version, and release-notes URL.

## `web`

Opens the Jottacloud website in a browser. Exact options are low priority for Jotta GUI.

## `webhook`

Officially documented:

```text
jotta-cli webhook add URL
jotta-cli webhook rem URL
```

See [configuration-and-runtime.md](configuration-and-runtime.md).
