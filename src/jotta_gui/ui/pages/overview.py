
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from jotta_gui.application.state import ApplicationState
from jotta_gui.ui.components import MetricCard
from jotta_gui.ui.formatting import format_bytes, format_percent


class OverviewPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()
        content.setObjectName("pageContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        scroll.setWidget(content)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(scroll)

        self.user_name = QLabel("Loading…")
        self.user_name.setObjectName("overviewUser")

        self.device_info = QLabel()
        self.device_info.setObjectName("mutedText")

        self.storage_card = MetricCard(
            "Storage", "—", "Loading account information"
        )
        self.sync_card = MetricCard("Sync", "—", "Loading sync status")
        self.backup_card = MetricCard("Backup", "—", "Loading backup status")
        self.disk_card = MetricCard(
            "Local disk", "—", "Loading disk information"
        )

        cards = QGridLayout()
        cards.setSpacing(16)
        cards.addWidget(self.storage_card, 0, 0)
        cards.addWidget(self.sync_card, 0, 1)
        cards.addWidget(self.backup_card, 0, 2)
        cards.addWidget(self.disk_card, 0, 3)
        for column in range(4):
            cards.setColumnStretch(column, 1)

        storage_title = QLabel("Storage")
        storage_title.setObjectName("sectionTitle")
        self.storage_description = QLabel("—")
        self.storage_description.setObjectName("mutedText")
        self.storage_progress = self._progress_bar("storageProgress")

        disk_title = QLabel("Local storage")
        disk_title.setObjectName("sectionTitle")
        self.disk_description = QLabel("—")
        self.disk_description.setObjectName("mutedText")
        self.disk_progress = self._progress_bar("diskProgress")

        backup_title = QLabel("Backup folders")
        backup_title.setObjectName("sectionTitle")
        self.backup_container = QVBoxLayout()
        self.backup_container.setSpacing(10)

        layout.addWidget(self.user_name)
        layout.addWidget(self.device_info)
        layout.addSpacing(8)
        layout.addLayout(cards)
        layout.addSpacing(12)
        layout.addWidget(storage_title)
        layout.addWidget(self.storage_description)
        layout.addWidget(self.storage_progress)
        layout.addSpacing(12)
        layout.addWidget(disk_title)
        layout.addWidget(self.disk_description)
        layout.addWidget(self.disk_progress)
        layout.addSpacing(12)
        layout.addWidget(backup_title)
        layout.addLayout(self.backup_container)
        layout.addStretch()

    def update_state(self, state: ApplicationState) -> None:
        status = state.status
        if status is None:
            if not state.connected:
                self.user_name.setText("Jottacloud unavailable")
            self._update_disk(state.disk_usage)
            return

        account = status.user.account
        sync = status.sync

        self.user_name.setText(status.user.fullname)
        self.device_info.setText(
            f"{status.user.hostname} · {account.subscription_name}"
        )

        self.storage_card.set_metric(
            format_bytes(account.usage),
            f"of {format_bytes(account.capacity)}",
        )
        self.sync_card.set_metric(
            f"{sync.local.files:,}",
            f"{format_bytes(sync.local.bytes)} synced",
        )

        backup_files = sum(backup.count.files for backup in status.backups)
        self.backup_card.set_metric(
            f"{backup_files:,}",
            f"{len(status.backups)} backup folders",
        )

        account_percent = _percentage(account.usage, account.capacity)
        self.storage_progress.setValue(round(account_percent))
        self.storage_description.setText(
            f"{format_bytes(account.usage)} used of "
            f"{format_bytes(account.capacity)} "
            f"({format_percent(account_percent)})"
        )

        self._update_disk(state.disk_usage)
        self._update_backups(status.backups)

    def _update_disk(self, disk) -> None:
        if disk is None:
            self.disk_card.set_metric("Unavailable", "Local disk information")
            self.disk_progress.setValue(0)
            self.disk_description.setText("Local disk information unavailable")
            return

        self.disk_card.set_metric(
            format_bytes(disk.free),
            f"free of {format_bytes(disk.total)}",
        )
        self.disk_progress.setValue(round(disk.used_percent))
        self.disk_description.setText(
            f"{format_bytes(disk.used)} used of {format_bytes(disk.total)} "
            f"({format_percent(disk.used_percent)}) · "
            f"{format_bytes(disk.free)} free"
        )

    def _update_backups(self, backups: list) -> None:
        self._clear_backup_container()

        if not backups:
            empty = QLabel("No backup folders configured.")
            empty.setObjectName("mutedText")
            self.backup_container.addWidget(empty)
            return

        for backup in backups:
            self.backup_container.addWidget(
                BackupRow(
                    name=backup.name,
                    path=backup.path,
                    files=backup.count.files,
                    size=backup.count.bytes,
                )
            )

    def _clear_backup_container(self) -> None:
        while self.backup_container.count():
            item = self.backup_container.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _progress_bar(object_name: str) -> QProgressBar:
        progress = QProgressBar()
        progress.setObjectName(object_name)
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setTextVisible(False)
        return progress


class BackupRow(QFrame):
    def __init__(
        self,
        name: str,
        path: str,
        files: int,
        size: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("backupRow")

        name_label = QLabel(name)
        name_label.setObjectName("backupName")

        path_label = QLabel(path)
        path_label.setObjectName("mutedText")

        stats_label = QLabel(f"{files:,} files · {format_bytes(size)}")
        stats_label.setObjectName("mutedText")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        layout.addWidget(name_label)
        layout.addWidget(path_label)
        layout.addWidget(stats_label)


def _percentage(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return min(max(value / total * 100, 0.0), 100.0)
