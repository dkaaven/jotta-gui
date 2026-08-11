# Capturing an installed CLI reference

Official web documentation is useful for semantics, but it can lag behind the installed binary. Jotta GUI therefore keeps a version-specific snapshot of the CLI's own help tree.

## Tool

```text
tools/capture_cli_reference.py
```

The tool only invokes help/version commands; it does not mutate Sync, Backup, configuration, credentials, remote data, or transfers.

## Run

From the repository root:

```bash
uv run python tools/capture_cli_reference.py
```

Default output:

```text
tests/fixtures/cli-reference/<version>/
```

Expected files:

```text
metadata.json
version.txt
help/
  root.txt
  add.txt
  archive.txt
  ...
  sync.txt
  sync__log.txt
  ...
```

The script discovers nested commands recursively from each command's `Available Commands:` section.

## Review before commit

Although help output should not contain account data, `jotta-cli version` prints local paths. The capture utility sanitizes the current home directory to `$HOME` before writing it.

Review all generated files before committing them.

## After a CLI upgrade

1. Run `jotta-cli version`.
2. Capture a new help tree.
3. Keep the old version snapshot for historical parser/behaviour context.
4. Diff the two references.
5. Update command wrappers/tests before relying on changed syntax.

Example:

```bash
diff -ru \
  tests/fixtures/cli-reference/0.17.159692 \
  tests/fixtures/cli-reference/NEW_VERSION
```

## Behaviour captures are separate

The help tree documents syntax, not runtime semantics.

Continue to use sanitized real-output fixtures for behaviour such as:

```text
status --json
status
sync transitions
errors
```

Do not execute mutating commands automatically from the reference-capture tool.
