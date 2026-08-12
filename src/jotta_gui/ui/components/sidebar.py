from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QLabel, QPushButton, QVBoxLayout, QWidget


class Sidebar(QWidget):
    page_selected = Signal(str)

    PAGES = (
        ("overview", "Overview"),
        ("sync", "Sync"),
        ("backup", "Backup"),
        ("settings", "Settings"),
    )

    def __init__(self, parent: QWidget | None = None, *, demo_mode: bool = False) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(210)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 22, 14, 14)
        layout.setSpacing(5)

        brand = QLabel("Jotta GUI")
        brand.setObjectName("sidebarTitle")
        layout.addWidget(brand)

        self.caption = QLabel("Demo mode · dummy data" if demo_mode else "Desktop client")
        self.caption.setObjectName("sidebarCaption")
        layout.addWidget(self.caption)
        layout.addSpacing(22)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons: dict[str, QPushButton] = {}

        for key, label in self.PAGES[:-1]:
            layout.addWidget(self._create_button(key, label))

        layout.addStretch()
        layout.addWidget(self._create_button(*self.PAGES[-1]))
        self.buttons["overview"].setChecked(True)

    def _create_button(self, key: str, label: str) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.clicked.connect(lambda checked=False, page=key: self.page_selected.emit(page))
        self.group.addButton(button)
        self.buttons[key] = button
        return button
