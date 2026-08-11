# Transfers and remote filesystem

## Remote roots

Official download documentation groups remote content under roots such as:

```text
Sync
Backup
Archive
```

Release notes also document Photos/Timeline support.

Do not hard-code the complete root set without testing the current account/version; remote availability can be account- or feature-dependent.

## Archive/upload

Basic upload:

```text
jotta-cli archive PATH
```

Destination under Archive:

```text
jotta-cli archive PATH --remote=folder/subfolder/name
```

Share immediately:

```text
jotta-cli archive PATH --share
jotta-cli archive PATH --share --clipboard
```

Disable terminal raw-mode UI:

```text
jotta-cli archive PATH --nogui
```

Archive stdin:

```text
echo "Hello" | jotta-cli archive -I --remote=hello.txt
```

Folder uploads are asynchronous after initial setup and can be listed/observed.

## List uploads

```text
jotta-cli list uploads
```

Current release notes state `--json` is supported for upload/download lists. Capture schema before creating parsers.

## Observe upload

```text
jotta-cli observe --uploadid=UPLOAD_ID
```

Streaming command.

## Download

Start:

```text
jotta-cli download REMOTE_PATH LOCAL_DESTINATION
```

Examples:

```text
jotta-cli download Archive/folder/subfolder ~/Downloads
jotta-cli download Backup/Device/Folder ~/Downloads
jotta-cli download Sync .
```

When `jotta-cli` controls a remote `jottad`, the local destination path is interpreted on the machine running jottad.

### Merge/update an existing local folder

```text
jotta-cli download REMOTE LOCAL --merge
```

Default merge verification checksums existing files.

Metadata-only verification:

```text
jotta-cli download REMOTE LOCAL --merge --mergemode=metadata
```

This uses filename, size, and modified time rather than checksumming according to official docs.

### Download to stdout

```text
jotta-cli download -O REMOTE_PATH
```

Suitable for piping/redirection. Do not parse progress UI from stdout in this mode without a dedicated fixture.

### Abort

```text
jotta-cli download --abort=DOWNLOAD_ID
```

Official docs say successfully downloaded files remain, while partial files are deleted.

Historical release notes also document `--abort=all`; verify current help before use.

### Retry

```text
jotta-cli download --retry=DOWNLOAD_ID
```

Retries failed files for a recorded download.

## List downloads

```text
jotta-cli list downloads
```

Only one download runs at a time according to official docs; additional downloads queue.

Failed downloads remain listed after completion until cleared.

## Download error information

Documentation is inconsistent on the exact subcommand spelling across versions/articles. Variants seen include:

```text
jotta-cli list downloadinfo --downloadid=ID
jotta-cli list downloadinformation --downloadid=ID
jotta-cli list downloaderrors --downloadid=ID
```

Some variants support `--json`.

**Never choose one from documentation alone. Capture installed 0.17.159692 help.**

## Observe downloads

```text
jotta-cli observe --downloads
jotta-cli observe --downloadid=DOWNLOAD_ID
```

Streaming commands.

## `ls`

Remote browsing:

```text
jotta-cli ls [REMOTE_PATH]
```

Shell completion can dynamically complete remote paths. Newer release notes document an `-a` option for more information.

## `share`

Top-level help describes generating a public URL for a single file, while release notes indicate later shared-file management was added.

Capture the full current help tree before implementing sharing.

## Trash

Release notes document:

```text
jotta-cli trash ls
jotta-cli trash restore ...
jotta-cli trash purge ...
```

`purge` is destructive. Require explicit confirmation in any future GUI.

Because backup-removal semantics changed in 0.17, Trash is relevant to Backup management as well as remote browsing.
