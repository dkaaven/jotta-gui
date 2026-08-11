from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from jotta_gui.application.state import ApplicationState, SyncOperation
from jotta_gui.jotta.models import SyncActivity, SyncMode
from jotta_gui.ui.components import MetricCard, StatusPill
from jotta_gui.ui.formatting import format_bytes, format_count

from ._shared import make_scroll_page


class SyncPage(QWidget):
    start_requested = Signal()
    force_start_requested = Signal()
    stop_requested = Signal()
    trigger_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        _, layout = make_scroll_page(self)

        status_card = QFrame()
        status_card.setObjectName("featureCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(20, 18, 20, 18)
        status_layout.setSpacing(8)

        status_header = QHBoxLayout()
        self.status_pill = StatusPill("Sync unknown", "neutral")
        status_header.addWidget(self.status_pill)
        status_header.addStretch()
        status_layout.addLayout(status_header)

        self.root_path = QLabel("Sync root unavailable")
        self.root_path.setObjectName("featureTitle")
        self.root_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.activity_text = QLabel("Waiting for Sync state")
        self.activity_text.setObjectName("mutedText")
        self.activity_text.setWordWrap(True)
        status_layout.addWidget(self.root_path)
        status_layout.addWidget(self.activity_text)
        layout.addWidget(status_card)

        self.local_card = MetricCard("Local", "—", "Files in Sync")
        self.remote_card = MetricCard("Cloud", "—", "Remote count")
        self.folder_card = MetricCard("Folders", "—", "Folder count")

        cards = QGridLayout()
        cards.setSpacing(14)
        for column, card in enumerate((self.local_card, self.remote_card, self.folder_card)):
            cards.addWidget(card, 0, column)
            cards.setColumnStretch(column, 1)
        layout.addLayout(cards)

        controls_title = QLabel("Controls")
        controls_title.setObjectName("sectionTitle")
        controls_help = QLabel(
            "Continuous Sync can be stopped into triggered mode. In triggered mode, "
            "you can start continuous Sync again or run one synchronization now."
        )
        controls_help.setObjectName("mutedText")
        controls_help.setWordWrap(True)
        layout.addWidget(controls_title)
        layout.addWidget(controls_help)

        self.start_button = QPushButton("Start continuous Sync")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.start_requested.emit)

        self.stop_button = QPushButton("Stop continuous Sync")
        self.stop_button.clicked.connect(self.stop_requested.emit)

        self.trigger_button = QPushButton("Sync now")
        self.trigger_button.clicked.connect(self.trigger_requested.emit)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.trigger_button)
        controls.addStretch()
        layout.addLayout(controls)

        self.force_start_button = QPushButton("Force start after critical Sync error")
        self.force_start_button.setObjectName("linkButton")
        self.force_start_button.clicked.connect(self.force_start_requested.emit)
        self.force_start_button.setVisible(False)
        layout.addWidget(self.force_start_button)

        detail_title = QLabel("CLI evidence")
        detail_title.setObjectName("sectionTitle")
        self.evidence = QLabel("No Sync snapshot available")
        self.evidence.setObjectName("mutedText")
        self.evidence.setWordWrap(True)
        layout.addWidget(detail_title)
        layout.addWidget(self.evidence)
        layout.addStretch()

        self._set_controls(False, False, False, False)

    def update_state(self, state: ApplicationState) -> None:
        snapshot = state.snapshot
        if snapshot is None:
            self.status_pill.set_status("Sync unknown", "neutral")
            self.root_path.setText("Sync root unavailable")
            self.activity_text.setText("No Jottacloud snapshot available")
            self.force_start_button.setVisible(False)
            self._set_controls(False, False, False, False)
            return

        sync = snapshot.sync
        self.root_path.setText(str(sync.root_path) if sync.root_path else "Sync root unknown")
        self.local_card.set_metric(format_count(sync.local.files), format_bytes(sync.local.bytes))
        self.remote_card.set_metric(format_count(sync.remote.files), format_bytes(sync.remote.bytes))
        self.folder_card.set_metric(format_count(sync.folder_count), "folders")

        text, tone = _status_label(state, sync.mode)
        self.status_pill.set_status(text, tone)

        activity = sync.activity_text or _activity_label(sync.activity)
        if state.refreshing:
            activity = f"Refreshing state… · {activity}"
        self.activity_text.setText(activity)

        raw_mode = sync.runtime_mode_text or "not observed"
        cli_state = "missing" if sync.cli_sync_state is None else str(sync.cli_sync_state)
        self.evidence.setText(
            f"Configured mode: {sync.mode.value} · Runtime mode text: {raw_mode} · "
            f"CLI SyncState: {cli_state}"
        )

        force_available = (
            state.error is not None
            and state.error.command == "sync_start"
        )

        self.force_start_button.setVisible(force_available)
        self._update_controls(state, sync.mode, force_available)

    def _update_controls(
        self,
        state: ApplicationState,
        mode: SyncMode,
        force_available: bool,
    ) -> None:
        if not state.connected or state.sync_busy or state.refreshing:
            self._set_controls(False, False, False, False)
            return

        if mode == SyncMode.AUTOMATIC:
            self._set_controls(False, True, False, force_available)
        elif mode == SyncMode.TRIGGERED:
            self._set_controls(True, False, True, force_available)
        else:
            self._set_controls(False, False, False, False)

    def _set_controls(
        self,
        start: bool,
        stop: bool,
        trigger: bool,
        force: bool,
    ) -> None:
        self.start_button.setEnabled(start)
        self.stop_button.setEnabled(stop)
        self.trigger_button.setEnabled(trigger)
        self.force_start_button.setEnabled(force)


def _status_label(state: ApplicationState, mode: SyncMode) -> tuple[str, str]:
    pending = {
        SyncOperation.STARTING: ("Starting continuous Sync…", "info"),
        SyncOperation.STOPPING: ("Stopping continuous Sync…", "info"),
        SyncOperation.TRIGGERING: ("Syncing now…", "info"),
    }
    if state.sync_operation in pending:
        return pending[state.sync_operation]
    if mode == SyncMode.AUTOMATIC:
        return "Automatic Sync", "success"
    if mode == SyncMode.TRIGGERED:
        return "Triggered mode", "warning"
    if mode == SyncMode.DISABLED:
        return "Sync disabled", "danger"
    return "Sync mode unknown", "neutral"


def _activity_label(activity: SyncActivity) -> str:
    if activity == SyncActivity.LISTENING:
        return "Listening for filesystem changes"
    if activity == SyncActivity.TRIGGERED:
        return "Triggered Sync activity observed"
    return "Runtime activity was not observed"
