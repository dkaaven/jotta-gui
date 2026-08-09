

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class BackupPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("Backup")
        title.setObjectName("sectionTitle")

        placeholder = QLabel(
            "Backup folders and status will appear here."
        )
        placeholder.setObjectName("placeholderText")

        layout.addWidget(title)
        layout.addWidget(placeholder)
        layout.addStretch()
