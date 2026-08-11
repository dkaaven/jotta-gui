import pytest

from jotta_gui.jotta.config import ConfigEntry, JottaConfig, parse_config_output


CURRENT_CONFIG_OUTPUT = """
downloadrate : unlimited
uploadrate : unlimited
checksumreadrate : 52.43MB/s
ignorehiddenfiles : false
maxuploads : 12
maxdownloads : 12
scaninterval : 1h0m0s
webhookstatusinterval : 6h0m0s
logscanignores : false
slowmomode : 0
logtransfers : false
screenshotscapture : false
checksumthreads : 4
""".strip()


def test_parse_config_output_preserves_values_and_unknown_settings() -> None:
    config = parse_config_output(CURRENT_CONFIG_OUTPUT)

    assert config.get("downloadrate") == "unlimited"
    assert config.get("maxuploads") == "12"
    assert config.get("checksumthreads") == "4"
    assert config.get("missing") is None
    assert config.raw_output == CURRENT_CONFIG_OUTPUT


def test_parse_config_output_is_case_insensitive_for_lookup() -> None:
    config = JottaConfig(
        entries=(ConfigEntry("ScanInterval", "30m"),),
        raw_output="ScanInterval : 30m",
    )

    assert config.get("scaninterval") == "30m"


def test_parse_config_output_ignores_non_setting_noise() -> None:
    config = parse_config_output(
        "heading\n----------------\ndownloadrate : 5m\nfooter"
    )

    assert config.entries == (ConfigEntry("downloadrate", "5m"),)


def test_parse_config_output_rejects_unrecognized_output() -> None:
    with pytest.raises(ValueError, match="no recognized settings"):
        parse_config_output("unexpected output")
