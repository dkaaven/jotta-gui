"""Jottacloud integration layer for Jotta GUI.

The package keeps raw CLI observations separate from normalized domain state.
"""

from .models import JottaSnapshot
from .snapshot import build_snapshot

__all__ = ["JottaSnapshot", "build_snapshot"]
