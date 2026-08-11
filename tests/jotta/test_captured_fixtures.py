from __future__ import annotations

import json
from pathlib import Path

import pytest

from jotta_gui.jotta.models import SyncActivity, SyncMode
from jotta_gui.jotta.snapshot import build_snapshot
from jotta_gui.jotta.status.parser import parse_status_output
from jotta_gui.jotta.sync.models import SyncRuntimeActivity
from jotta_gui.jotta.sync.parser import parse_sync_runtime_status

pytestmark = pytest.mark.captured

CAPTURED_ROOT = Path(__file__).parents[1] / "fixtures" / "captured"


def test_captured_status_and_runtime_contracts() -> None:
    fixture_dirs = _capture_dirs()
    if not fixture_dirs:
        pytest.skip(
            "No real jotta-cli captures committed yet; use tools/capture_cli_fixtures.py"
        )

    for fixture_dir in fixture_dirs:
        status = parse_status_output(
            (fixture_dir / "status.json").read_text(encoding="utf-8")
        )
        runtime = parse_sync_runtime_status(
            (fixture_dir / "runtime.txt").read_text(encoding="utf-8"),
            status.sync.root_path,
        )
        snapshot = build_snapshot(status, runtime)
        metadata = _metadata(fixture_dir)

        assert snapshot.account.email
        assert status.raw

        expected_mode = metadata.get("expected_sync_mode")
        if expected_mode is not None:
            assert snapshot.sync.mode == SyncMode(expected_mode), fixture_dir.name

        expected_runtime = metadata.get("expected_runtime_state")
        if expected_runtime is not None:
            assert runtime.activity == SyncRuntimeActivity(expected_runtime), fixture_dir.name
            assert snapshot.sync.activity == SyncActivity(expected_runtime), fixture_dir.name


def _metadata(fixture_dir: Path) -> dict:
    return json.loads((fixture_dir / "metadata.json").read_text(encoding="utf-8"))


def _capture_dirs() -> list[Path]:
    if not CAPTURED_ROOT.exists():
        return []

    return sorted(
        path
        for path in CAPTURED_ROOT.iterdir()
        if path.is_dir()
        and (path / "status.json").is_file()
        and (path / "runtime.txt").is_file()
        and (path / "metadata.json").is_file()
    )
