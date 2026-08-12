from __future__ import annotations

import argparse
from importlib import resources
import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from jotta_gui.application.controller import ApplicationController
from jotta_gui.demo.controller import DemoController
from jotta_gui.ui.main_window import MainWindow


def package_resource(*parts: str):
    """Return a resource bundled inside the ``jotta_gui`` package.

    Package resources must not be resolved relative to ``__main__.__file__``.
    PyInstaller freezes the entry script outside the package while package data
    remains under ``jotta_gui`` inside the bundle.
    """

    return resources.files("jotta_gui").joinpath(*parts)


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        prog="jotta-gui",
        description="Graphical desktop client for jotta-cli.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with deterministic dummy data without invoking jotta-cli.",
    )
    return parser.parse_known_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    args, qt_arguments = parse_args(sys.argv[1:] if argv is None else argv)
    application_arguments = [sys.argv[0], *qt_arguments]

    app = QApplication(application_arguments)
    app.setApplicationName("Jotta GUI")
    app.setDesktopFileName("jotta-gui")
    app.setStyle("Fusion")

    icon = package_resource("resources", "jotta-gui.svg")
    with resources.as_file(icon) as icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    app.setStyleSheet(
        package_resource("ui", "styles", "dark.qss").read_text(encoding="utf-8")
    )

    controller_factory = DemoController if args.demo else ApplicationController
    window = MainWindow(controller_factory=controller_factory, demo_mode=args.demo)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
