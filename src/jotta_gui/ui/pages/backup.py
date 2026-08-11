from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from jotta_gui.application.state import ApplicationState
from jotta_gui.jotta.models import BackupStatus
from jotta_gui.ui.components import MetricCard
from jotta_gui.ui.formatting import format_bytes, format_count, format_timestamp_ms

from ._shared import make_scroll_page


class BackupPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        _, layout = make_scroll_page(self)

        intro = QLabel("Continuous backup")
        intro.setObjectName("heroTitle")
        self.summary = QLabel("Waiting for backup information")
        self.summary.setObjectName("mutedText")
        layout.addWidget(intro)
        layout.addWidget(self.summary)

        self.folder_card = MetricCard("Backup folders", "—", "Configured")
        self.file_card = MetricCard("Files", "—", "Known file count")
        self.size_card = MetricCard("Data", "—", "Known backup size")

        cards = QGridLayout()
        cards.setSpacing(14)
        for column, card in enumerate((self.folder_card, self.file_card, self.size_card)):
            cards.addWidget(card, 0, column)
            cards.setColumnStretch(column, 1)
        layout.addLayout(cards)

        title = QLabel("Configured folders")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.rows = QVBoxLayout()
        self.rows.setSpacing(10)
        layout.addLayout(self.rows)
        layout.addStretch()

    def update_state(self, state: ApplicationState) -> None:
        self._clear_rows()
        snapshot = state.snapshot
        if snapshot is None:
            self.summary.setText("No backup snapshot available")
            self.folder_card.set_metric("—", "Configured")
            self.file_card.set_metric("—", "Known file count")
            self.size_card.set_metric("—", "Known backup size")
            self._add_empty("Backup information is unavailable.")
            return

        backups = snapshot.backups
        self.summary.setText(
            f"{len(backups)} backup folder{'s' if len(backups) != 1 else ''} reported by jottad"
        )
        self.folder_card.set_metric(str(len(backups)), "configured")
        self.file_card.set_metric(format_count(_sum_known(b.count.files for b in backups)), "known files")
        self.size_card.set_metric(format_bytes(_sum_known(b.count.bytes for b in backups)), "known data")

        if not backups:
            self._add_empty("No backup folders are configured.")
            return

        for backup in backups:
            self.rows.addWidget(BackupRow(backup))

    def _add_empty(self, text: str) -> None:
        label = QLabel(text)
        label.setObjectName("mutedText")
        self.rows.addWidget(label)

    def _clear_rows(self) -> None:
        while self.rows.count():
            item = self.rows.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


class BackupRow(QFrame):
    def __init__(self, backup: BackupStatus, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("backupRow")

        name = QLabel(backup.name or "Unnamed backup")
        name.setObjectName("rowTitle")
        path = QLabel(str(backup.path) if backup.path else "Path unknown")
        path.setObjectName("mutedText")
        path.setWordWrap(True)

        files = QLabel(f"{format_count(backup.count.files)} files")
        files.setObjectName("rowMetric")
        size = QLabel(format_bytes(backup.count.bytes))
        size.setObjectName("rowMetric")
        updated = QLabel(f"Updated {format_timestamp_ms(backup.last_update_ms)}")
        updated.setObjectName("mutedText")

        stats = QGridLayout()
        stats.setHorizontalSpacing(20)
        stats.addWidget(files, 0, 0)
        stats.addWidget(size, 0, 1)
        stats.addWidget(updated, 0, 2)
        stats.setColumnStretch(3, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(5)
        layout.addWidget(name)
        layout.addWidget(path)
        layout.addLayout(stats)


def _sum_known(values) -> int | None:
    known = [value for value in values if value is not None]
    return sum(known) if known else None
