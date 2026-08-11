from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FileStats:
    """Normalized file count/size pair.

    ``None`` means the CLI did not provide the fact. It is intentionally different
    from a reported value of zero.
    """

    files: int | None = None
    bytes: int | None = None
