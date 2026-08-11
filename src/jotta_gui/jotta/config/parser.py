from __future__ import annotations

import re

from .models import ConfigEntry, JottaConfig


_CONFIG_LINE = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$")


def parse_config_output(output: str) -> JottaConfig:
    """Parse ``jotta-cli config`` output without inventing setting semantics.

    Current Jottacloud documentation and captured CLI help use ``name : value``.
    Unknown setting names are preserved so newer CLI versions remain inspectable.
    """

    entries: list[ConfigEntry] = []
    seen: set[str] = set()

    for line in output.splitlines():
        match = _CONFIG_LINE.match(line)
        if match is None:
            continue

        name, value = match.groups()
        normalized = name.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        entries.append(ConfigEntry(name=name, value=value))

    if not entries:
        raise ValueError("jotta-cli config output contained no recognized settings")

    return JottaConfig(entries=tuple(entries), raw_output=output.strip())
