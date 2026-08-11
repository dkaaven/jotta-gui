from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class StatusPill(QLabel):
    """Small semantic status label styled through a dynamic property."""

    def __init__(
        self,
        text: str = "Unknown",
        tone: str = "neutral",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.setObjectName("statusPill")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status(text, tone)

    def set_status(self, text: str, tone: str = "neutral") -> None:
        self.setText(text)
        if self.property("tone") != tone:
            self.setProperty("tone", tone)
            self.style().unpolish(self)
            self.style().polish(self)


class ErrorBanner(QFrame):
    dismissed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("errorBanner")
        self.setVisible(False)

        self.message = QLabel()
        self.message.setObjectName("errorText")
        self.message.setWordWrap(True)

        dismiss = QPushButton("Dismiss")
        dismiss.setObjectName("bannerButton")
        dismiss.clicked.connect(self.dismissed.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self.message, stretch=1)
        layout.addWidget(dismiss)

    def show_error(self, command: str, message: str) -> None:
        label = command.replace("_", " ")
        self.message.setText(f"{label}: {message}")
        self.setVisible(True)

    def clear(self) -> None:
        self.message.clear()
        self.setVisible(False)
