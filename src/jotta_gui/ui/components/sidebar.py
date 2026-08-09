from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    page_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(6)

        title = QLabel("Jotta GUI")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)
        layout.addSpacing(24)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons: dict[str, QPushButton] = {}

        for key, label in (
            ("overview", "Overview"),
            ("sync", "Sync"),
            ("backup", "Backup"),
        ):
            layout.addWidget(self._create_button(key, label))

        layout.addStretch()
        layout.addWidget(self._create_button("settings", "Settings"))
        self.buttons["overview"].setChecked(True)

    def _create_button(self, key: str, label: str) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.clicked.connect(
            lambda checked=False, page=key: self.page_selected.emit(page)
        )

        self.group.addButton(button)
        self.buttons[key] = button
        return button
