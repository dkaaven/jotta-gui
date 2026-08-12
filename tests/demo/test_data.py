from jotta_gui.demo.data import DEMO_IGNORE_RULES, build_demo_state
from jotta_gui.jotta.models import SyncMode


def test_demo_state_is_deterministic_and_sanitized() -> None:
    state = build_demo_state()

    assert state.connected is True
    assert state.snapshot is not None
    assert state.snapshot.account.email == "user@example.com"
    assert state.snapshot.account.hostname == "jotta-demo"
    assert str(state.snapshot.sync.root_path) == "/home/example/Jotta"
    assert state.snapshot.sync.mode == SyncMode.AUTOMATIC
    assert state.version is not None
    assert state.version.update_available is False
    assert state.config is not None
    assert state.config.get("scaninterval") == "1h"
    assert state.backup_ignores.backup_name == "Documents"
    assert "**/.git" in (state.backup_ignores.output or "")


def test_demo_rules_cover_all_demo_backups() -> None:
    state = build_demo_state()
    assert state.snapshot is not None

    names = {backup.name for backup in state.snapshot.backups}
    assert names == set(DEMO_IGNORE_RULES)
