import json
from pathlib import Path

import pytest

from jotta_gui.application.state import SyncMode, sync_mode_from_automatic
from jotta_gui.jotta.status.parser import parse_status_output
from jotta_gui.jotta.sync.models import SyncRuntimeState
from jotta_gui.jotta.sync.parser import parse_sync_runtime_status

pytestmark = pytest.mark.captured

CAPTURED_ROOT = Path(__file__).parents[1] / "fixtures" / "captured"


def test_captured_status_fixtures_parse() -> None:
    fixture_dirs = _capture_dirs()
    if not fixture_dirs:
        pytest.skip("No captured jotta-cli fixtures yet")

    for fixture_dir in fixture_dirs:
        output = (fixture_dir / "status.json").read_text(encoding="utf-8")
        status = parse_status_output(output)
        metadata = _metadata(fixture_dir)

        assert status.user.email
        assert status.user.hostname
        assert status.sync.root_path

        expected = metadata.get("expected_sync_mode")
        if expected is not None:
            assert sync_mode_from_automatic(status.sync.automatic) == SyncMode(expected), fixture_dir.name


def test_captured_runtime_fixtures_parse() -> None:
    fixture_dirs = _capture_dirs()
    if not fixture_dirs:
        pytest.skip("No captured jotta-cli fixtures yet")

    for fixture_dir in fixture_dirs:
        status = parse_status_output(
            (fixture_dir / "status.json").read_text(encoding="utf-8")
        )
        runtime = parse_sync_runtime_status(
            (fixture_dir / "runtime.txt").read_text(encoding="utf-8"),
            status.sync.root_path,
        )
        metadata = _metadata(fixture_dir)

        assert isinstance(runtime.state, SyncRuntimeState)

        expected = metadata.get("expected_runtime_state")
        if expected is not None:
            assert runtime.state == SyncRuntimeState(expected), fixture_dir.name


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
