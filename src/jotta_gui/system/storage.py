
from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True, slots=True)
class DiskUsage:
    total: int
    used: int
    free: int

    @property
    def used_percent(self) -> float:
        if self.total == 0:
            return 0.0
        return self.used / self.total * 100


def get_disk_usage(path: str | Path) -> DiskUsage:
    usage = shutil.disk_usage(path)
    return DiskUsage(total=usage.total, used=usage.used, free=usage.free)
