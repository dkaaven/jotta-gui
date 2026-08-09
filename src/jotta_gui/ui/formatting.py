
def format_bytes(value: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    size = float(value)

    for unit in units:
        if size < 1000:
            precision = 0 if unit == "B" else 1
            return f"{size:.{precision}f} {unit}"
        size /= 1000

    return f"{size:.1f} EB"


def format_percent(value: float) -> str:
    return f"{value:.1f}%"
