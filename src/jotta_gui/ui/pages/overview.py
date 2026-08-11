from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from jotta_gui.application.state import ApplicationState
from jotta_gui.jotta.models import SyncActivity, SyncMode
from jotta_gui.ui.components import MetricCard, StatusPill
from jotta_gui.ui.formatting import format_bytes, format_count, format_percent, percentage

from ._shared import make_scroll_page


class OverviewPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        _, layout = make_scroll_page(self)

        self.account_name = QLabel("Loading Jottacloud…")
        self.account_name.setObjectName("heroTitle")
        self.account_meta = QLabel("Waiting for account information")
        self.account_meta.setObjectName("mutedText")

        hero_status = QGridLayout()
        hero_status.setSpacing(10)
        self.sync_pill = StatusPill("Sync unknown", "neutral")
        hero_status.addWidget(self.sync_pill, 0, 0)
        hero_status.setColumnStretch(1, 1)

        layout.addWidget(self.account_name)
        layout.addWidget(self.account_meta)
        layout.addLayout(hero_status)

        self.storage_card = MetricCard("Cloud storage", "—", "Account usage")
        self.sync_card = MetricCard("Sync", "—", "Local files")
        self.backup_card = MetricCard("Backup", "—", "Configured folders")
        self.disk_card = MetricCard("Local disk", "—", "Available space")

        cards = QGridLayout()
        cards.setSpacing(14)
        for column, card in enumerate(
            (self.storage_card, self.sync_card, self.backup_card, self.disk_card)
        ):
            cards.addWidget(card, 0, column)
            cards.setColumnStretch(column, 1)
        layout.addLayout(cards)

        storage_title = QLabel("Storage")
        storage_title.setObjectName("sectionTitle")
        self.storage_description = QLabel("No account data yet")
        self.storage_description.setObjectName("mutedText")
        self.storage_progress = _progress_bar()
        layout.addWidget(storage_title)
        layout.addWidget(self.storage_description)
        layout.addWidget(self.storage_progress)

        sync_title = QLabel("Sync overview")
        sync_title.setObjectName("sectionTitle")
        self.sync_description = QLabel("No Sync data yet")
        self.sync_description.setObjectName("mutedText")
        self.sync_description.setWordWrap(True)
        layout.addWidget(sync_title)
        layout.addWidget(self.sync_description)
        layout.addStretch()

    def update_state(self, state: ApplicationState) -> None:
        snapshot = state.snapshot
        if snapshot is None:
            self.account_name.setText(
                "Jottacloud unavailable" if not state.connected else "Loading Jottacloud…"
            )
            self.account_meta.setText("No account snapshot available")
            self._update_disk(state)
            self.sync_pill.set_status("Sync unknown", "neutral")
            return

        account = snapshot.account
        sync = snapshot.sync

        self.account_name.setText(account.fullname or account.email or "Jottacloud account")
        meta = [part for part in (account.hostname, account.subscription_name) if part]
        self.account_meta.setText(" · ".join(meta) if meta else "Account details unavailable")

        self.storage_card.set_metric(
            format_bytes(account.usage),
            f"of {format_bytes(account.capacity)}" if account.capacity is not None else "Capacity unknown",
        )
        self.sync_card.set_metric(
            format_count(sync.local.files),
            f"{format_bytes(sync.local.bytes)} locally",
        )

        backup_files = _sum_known(backup.count.files for backup in snapshot.backups)
        self.backup_card.set_metric(
            format_count(backup_files),
            f"{len(snapshot.backups)} configured folder{'s' if len(snapshot.backups) != 1 else ''}",
        )

        account_percent = percentage(account.usage, account.capacity)
        if account_percent is None:
            self.storage_progress.setRange(0, 0)
            self.storage_description.setText(
                f"{format_bytes(account.usage)} used · total capacity unknown"
            )
        else:
            self.storage_progress.setRange(0, 100)
            self.storage_progress.setValue(round(account_percent))
            self.storage_description.setText(
                f"{format_bytes(account.usage)} used of {format_bytes(account.capacity)} "
                f"({format_percent(account_percent)})"
            )

        label, tone = _sync_status(sync.mode, sync.activity)
        self.sync_pill.set_status(label, tone)
        root = str(sync.root_path) if sync.root_path is not None else "Sync root unknown"
        activity = sync.activity_text or _activity_text(sync.activity)
        self.sync_description.setText(f"{root} · {activity}")

        self._update_disk(state)

    def _update_disk(self, state: ApplicationState) -> None:
        disk = state.disk_usage
        if disk is None:
            self.disk_card.set_metric("—", "Disk information unavailable")
            return
        self.disk_card.set_metric(format_bytes(disk.free), f"free of {format_bytes(disk.total)}")


def _progress_bar() -> QProgressBar:
    progress = QProgressBar()
    progress.setObjectName("storageProgress")
    progress.setRange(0, 100)
    progress.setValue(0)
    progress.setTextVisible(False)
    return progress


def _sum_known(values) -> int | None:
    known = [value for value in values if value is not None]
    return sum(known) if known else None


def _sync_status(mode: SyncMode, activity: SyncActivity) -> tuple[str, str]:
    if mode == SyncMode.DISABLED:
        return "Sync disabled", "danger"
    if mode == SyncMode.AUTOMATIC:
        return "Automatic Sync", "success"
    if mode == SyncMode.TRIGGERED:
        return "Manual Sync", "warning"
    if activity == SyncActivity.LISTENING:
        return "Sync listening", "info"
    return "Sync unknown", "neutral"


def _activity_text(activity: SyncActivity) -> str:
    if activity == SyncActivity.LISTENING:
        return "Listening for changes"
    if activity == SyncActivity.TRIGGERED:
        return "Triggered Sync observed"
    return "Runtime activity unknown"
