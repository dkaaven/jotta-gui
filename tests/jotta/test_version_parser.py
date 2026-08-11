import pytest

from jotta_gui.jotta.version import VersionInfo, parse_version_output


CAPTURED_UPDATE_OUTPUT = """
-------------------------------------------
 A new version of Jotta Cli is available.
 Please update from 0.17.159692 to version 0.17.176206
-------------------------------------------
jottad version    : 0.17.159692
remote version    : 0.17.176206
jotta-cli version : 0.17.159692
release notes     : https://docs.jottacloud.com/articles/1461561
-------------------------------------------
"""

CURRENT_UP_TO_DATE_OUTPUT = """
-------------------------------------------
jottad executable : /usr/bin/jottad
jottad appdata    : /home/example/.jottad
jottad logfile    : /home/example/.jottad/jottabackup.log
jottad version    : 0.17.176206
jotta-cli version : 0.17.176206
release notes     : https://docs.jottacloud.com/articles/1461561
-------------------------------------------
"""


def test_parse_version_output_from_captured_shape() -> None:
    version = parse_version_output(CAPTURED_UPDATE_OUTPUT)

    assert version == VersionInfo(
        cli_version="0.17.159692",
        daemon_version="0.17.159692",
        remote_version="0.17.176206",
        release_notes_url="https://docs.jottacloud.com/articles/1461561",
    )
    assert version.update_available is True


def test_parse_current_output_without_remote_version_is_up_to_date() -> None:
    version = parse_version_output(CURRENT_UP_TO_DATE_OUTPUT)

    assert version == VersionInfo(
        cli_version="0.17.176206",
        daemon_version="0.17.176206",
        remote_version=None,
        release_notes_url="https://docs.jottacloud.com/articles/1461561",
    )
    assert version.update_available is False


def test_update_available_is_false_when_versions_match() -> None:
    version = VersionInfo(
        cli_version="0.17.176206",
        remote_version="0.17.176206",
    )

    assert version.update_available is False


def test_update_available_is_false_when_local_is_newer() -> None:
    version = VersionInfo(
        cli_version="0.17.180000",
        remote_version="0.17.176206",
    )

    assert version.update_available is False


def test_unknown_version_format_is_not_interpreted() -> None:
    version = VersionInfo(
        cli_version="0.17-dev",
        remote_version="0.17.176206",
    )

    assert version.update_available is None


def test_missing_remote_does_not_hide_unknown_installed_format() -> None:
    version = VersionInfo(cli_version="0.17-dev", remote_version=None)

    assert version.update_available is None


def test_parser_rejects_output_without_version_fields() -> None:
    with pytest.raises(ValueError, match="no recognized version fields"):
        parse_version_output("something unexpected")
