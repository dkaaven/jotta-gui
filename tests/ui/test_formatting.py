import pytest

from jotta_gui.ui.formatting import format_bytes, format_percent


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0 B"),
        (999, "999 B"),
        (1_000, "1.0 KB"),
        (1_500_000, "1.5 MB"),
        (2_000_000_000, "2.0 GB"),
    ],
)
def test_format_bytes(value: int, expected: str) -> None:
    assert format_bytes(value) == expected


def test_format_percent() -> None:
    assert format_percent(12.345) == "12.3%"
