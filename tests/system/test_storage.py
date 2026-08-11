from types import SimpleNamespace

import jotta_gui.system.storage as storage_module
from jotta_gui.system.storage import DiskUsage, get_disk_usage


def test_used_percent() -> None:
    usage = DiskUsage(total=1_000, used=250, free=750)

    assert usage.used_percent == 25.0


def test_used_percent_with_zero_total() -> None:
    usage = DiskUsage(total=0, used=0, free=0)

    assert usage.used_percent == 0.0


def test_get_disk_usage_maps_shutil_result(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        storage_module.shutil,
        "disk_usage",
        lambda path: SimpleNamespace(total=100, used=40, free=60),
    )

    usage = get_disk_usage(tmp_path)

    assert usage == DiskUsage(total=100, used=40, free=60)
