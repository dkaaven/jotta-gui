import pytest

from jotta_gui.ui.formatting import format_bytes, format_count, percentage


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "—"),
        (0, "0 B"),
        (999, "999 B"),
        (1_000, "1.0 KB"),
        (1_500_000, "1.5 MB"),
    ],
)
def test_format_bytes(value, expected) -> None:
    assert format_bytes(value) == expected


def test_format_count_preserves_unknown() -> None:
    assert format_count(None) == "—"
    assert format_count(1234) == "1,234"


def test_percentage_preserves_unknown() -> None:
    assert percentage(None, 100) is None
    assert percentage(10, None) is None
    assert percentage(10, 0) is None
    assert percentage(25, 100) == 25.0
