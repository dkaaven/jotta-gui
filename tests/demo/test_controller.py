import pytest

pytest.importorskip("PySide6")

from jotta_gui.demo.controller import DemoController
from jotta_gui.jotta.models import SyncMode

pytestmark = pytest.mark.qt


def test_demo_controller_never_constructs_a_runner(qt_app) -> None:
    controller = DemoController()

    assert not hasattr(controller, "runner")


def test_demo_controller_updates_sync_in_memory(qt_app) -> None:
    controller = DemoController()

    controller.stop_sync()
    assert controller.state.snapshot is not None
    assert controller.state.snapshot.sync.mode == SyncMode.TRIGGERED

    controller.start_sync()
    assert controller.state.snapshot.sync.mode == SyncMode.AUTOMATIC


def test_demo_controller_updates_config_in_memory(qt_app) -> None:
    controller = DemoController()

    controller.set_config("scaninterval", "30m")

    assert controller.state.config is not None
    assert controller.state.config.get("scaninterval") == "30m"
    assert "scaninterval : 30m" in controller.state.config.raw_output


def test_demo_controller_updates_ignore_rules_in_memory(qt_app) -> None:
    controller = DemoController()

    controller.add_backup_ignore("Documents", "**/.pytest_cache")
    assert "**/.pytest_cache" in (controller.state.backup_ignores.output or "")

    controller.remove_backup_ignore("Documents", "**/.pytest_cache")
    assert "**/.pytest_cache" not in (controller.state.backup_ignores.output or "")
