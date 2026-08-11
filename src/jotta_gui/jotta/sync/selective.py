from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jotta_gui.jotta.runner import JottaRunner


def list_selective_sync(runner: JottaRunner) -> None:
    """List top-level folders currently excluded by selective Sync.

    The captured 0.17.159692 help shows ``add``, ``rem`` and ``set`` as
    interactive commands with no documented positional folder argument. Those
    mutating operations are intentionally not wrapped until their interaction
    contract has been captured.
    """

    runner.run("sync_selective_list", ["sync", "selective", "list"])
