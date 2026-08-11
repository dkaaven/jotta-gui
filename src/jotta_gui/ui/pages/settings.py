from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from jotta_gui.application.state import ApplicationState

from ._shared import make_scroll_page


class SettingsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        _, layout = make_scroll_page(self)

        title = QLabel("Account & device")
        title.setObjectName("heroTitle")
        help_text = QLabel(
            "This page currently reflects information reported by jottad. "
            "Configuration controls can be added once their application workflows are modelled."
        )
        help_text.setObjectName("mutedText")
        help_text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(help_text)

        card = QFrame()
        card.setObjectName("featureCard")
        grid = QGridLayout(card)
        grid.setContentsMargins(18, 16, 18, 16)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(12)

        self.values: dict[str, QLabel] = {}
        fields = (
            ("Email", "email"),
            ("Device", "device"),
            ("Hostname", "hostname"),
            ("Brand", "brand"),
            ("Subscription", "subscription"),
            ("Product", "product"),
        )
        for row, (label_text, key) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            value = QLabel("—")
            value.setObjectName("fieldValue")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.values[key] = value
            grid.addWidget(label, row, 0)
            grid.addWidget(value, row, 1)
        grid.setColumnStretch(1, 1)

        layout.addWidget(card)
        layout.addStretch()

    def update_state(self, state: ApplicationState) -> None:
        snapshot = state.snapshot
        if snapshot is None:
            for value in self.values.values():
                value.setText("—")
            return

        account = snapshot.account
        mapping = {
            "email": account.email,
            "device": account.device_name,
            "hostname": account.hostname,
            "brand": account.brand,
            "subscription": account.subscription_name,
            "product": account.product_name,
        }
        for key, value in mapping.items():
            self.values[key].setText(value or "—")
