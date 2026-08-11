from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from jotta_gui.application.state import ApplicationState

from .status import StatusPill


class Header(QWidget):
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("header")

        self.title = QLabel("Overview")
        self.title.setObjectName("pageTitle")

        self.subtitle = QLabel("Your Jottacloud at a glance")
        self.subtitle.setObjectName("pageSubtitle")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.addWidget(self.title)
        text_layout.addWidget(self.subtitle)

        self.connection = StatusPill("Disconnected", "danger")

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 16, 28, 16)
        layout.setSpacing(12)
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(self.connection)
        layout.addWidget(self.refresh_button)

    def set_page(self, title: str, subtitle: str) -> None:
        self.title.setText(title)
        self.subtitle.setText(subtitle)

    def update_state(self, state: ApplicationState) -> None:
        if state.refreshing:
            self.connection.set_status("Refreshing…", "info")
        elif state.connected:
            self.connection.set_status("Connected", "success")
        else:
            self.connection.set_status("Disconnected", "danger")

        self.refresh_button.setEnabled(not state.refreshing and not state.sync_busy)
