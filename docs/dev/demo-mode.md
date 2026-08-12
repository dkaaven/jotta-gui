# Demo mode

Jotta GUI has a deterministic demo mode for screenshots, UI development, and
presentations where real account data must not be shown.

Run from the repository:

```bash
uv run jotta-gui --demo
```

Run an installed Debian package:

```bash
jotta-gui --demo
```

## Safety boundary

Demo mode does not construct `JottaRunner` and does not invoke `jotta-cli`.
All displayed account, filesystem, version, configuration, Backup, and Sync data is
fixed dummy data under `/home/example`.

The demo controller implements the same user-intent methods consumed by
`MainWindow`, but mutations are performed only in memory. For example, changing a
configuration value or adding an ignore pattern changes the demo state until the
process exits.

## Screenshot convention

The sidebar displays `Demo mode · dummy data`, and the window title includes
`Demo`, so screenshots cannot easily be mistaken for a real Jottacloud account.

The data is intentionally deterministic rather than randomized. Re-running the app
therefore produces stable screenshots across documentation updates.
