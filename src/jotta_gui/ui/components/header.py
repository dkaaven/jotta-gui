from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from jotta_gui.application.state import (
    ApplicationState,
    SyncMode,
    SyncOperation,
)


class Header(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("header")

        self.title = QLabel("Jotta GUI")
        self.title.setObjectName("pageTitle")

        self.subtitle = QLabel("Your Jottacloud at a glance")
        self.subtitle.setObjectName("pageSubtitle")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.addWidget(self.title)
        text_layout.addWidget(self.subtitle)

        self.connection = QLabel("● Disconnected")
        self.connection.setObjectName("connectionStatus")

        self.sync_status = QLabel("● Sync mode unknown")
        self.sync_status.setObjectName("syncStatus")

        status_layout = QVBoxLayout()
        status_layout.setSpacing(4)
        status_layout.addWidget(
            self.connection,
            alignment=Qt.AlignmentFlag.AlignRight,
        )
        status_layout.addWidget(
            self.sync_status,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 18, 32, 18)
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addLayout(status_layout)

    def set_page(self, title: str, subtitle: str) -> None:
        self.title.setText(title)
        self.subtitle.setText(subtitle)

    def update_state(self, state: ApplicationState) -> None:
        if state.connected:
            self._set_status_label(self.connection, "● Connected", "#62c98a")
        else:
            self._set_status_label(self.connection, "● Disconnected", "#e66b6b")

        text, color = _sync_label(state)
        self._set_status_label(self.sync_status, text, color)

    @staticmethod
    def _set_status_label(label: QLabel, text: str, color: str) -> None:
        label.setText(text)
        label.setStyleSheet(f"color: {color}; font-weight: 600;")


def _sync_label(state: ApplicationState) -> tuple[str, str]:
    pending = {
        SyncOperation.STARTING: ("● Starting sync…", "#6173e8"),
        SyncOperation.STOPPING: ("● Stopping sync…", "#6173e8"),
        SyncOperation.TRIGGERING: ("● Syncing now…", "#6173e8"),
    }
    if state.sync_operation in pending:
        return pending[state.sync_operation]

    if state.status is not None and not state.status.sync.enabled:
        return "● Sync disabled", "#e66b6b"

    modes = {
        SyncMode.AUTOMATIC: ("● Automatic sync", "#62c98a"),
        SyncMode.TRIGGERED: ("● Manual sync", "#e6a75f"),
        SyncMode.UNKNOWN: ("● Sync mode unknown", "#8b909a"),
    }
    return modes[state.sync_mode]
