from __future__ import annotations

import logging
from pathlib import Path
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from jotta_gui.ui.main_window import MainWindow


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Jotta GUI")
    app.setDesktopFileName("jotta-gui")
    app.setStyle("Fusion")

    package_dir = Path(__file__).resolve().parent
    app.setWindowIcon(QIcon(str(package_dir / "resources" / "jotta-gui.svg")))
    app.setStyleSheet(
        (package_dir / "ui" / "styles" / "dark.qss").read_text(encoding="utf-8")
    )

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
