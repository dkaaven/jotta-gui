from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from jotta_gui.application.state import (
    ApplicationState,
    SyncActivity,
    SyncMode,
    SyncOperation,
)
from jotta_gui.ui.components import MetricCard
from jotta_gui.ui.formatting import format_bytes


class SyncPage(QWidget):
    start_requested = Signal()
    stop_requested = Signal()
    trigger_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        root_title = QLabel("Sync folder")
        root_title.setObjectName("sectionTitle")
        self.root_path = QLabel("Loading…")
        self.root_path.setObjectName("syncRoot")

        root_header = QHBoxLayout()
        root_header.addWidget(root_title)
        root_header.addStretch()
        layout.addLayout(root_header)
        layout.addWidget(self.root_path)

        self.local_card = MetricCard("Local", "—", "Loading local sync data")
        self.remote_card = MetricCard("Cloud", "—", "Loading remote sync data")
        self.folder_card = MetricCard("Folders", "—", "Loading folder data")

        cards = QGridLayout()
        cards.setSpacing(16)
        cards.addWidget(self.local_card, 0, 0)
        cards.addWidget(self.remote_card, 0, 1)
        cards.addWidget(self.folder_card, 0, 2)
        for column in range(3):
            cards.setColumnStretch(column, 1)
        layout.addLayout(cards)

        controls_title = QLabel("Sync controls")
        controls_title.setObjectName("sectionTitle")

        self.runtime_status = QLabel("● Sync mode unknown")
        self.runtime_status.setObjectName("syncRuntimeStatus")

        self.start_button = QPushButton("Start sync")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.start_requested.emit)

        self.stop_button = QPushButton("Stop sync")
        self.stop_button.clicked.connect(self.stop_requested.emit)

        self.trigger_button = QPushButton("Sync now")
        self.trigger_button.clicked.connect(self.trigger_requested.emit)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.trigger_button)
        controls.addStretch()

        layout.addWidget(controls_title)
        layout.addWidget(self.runtime_status)
        layout.addLayout(controls)

        folders_title = QLabel("Synced folders")
        folders_title.setObjectName("sectionTitle")
        placeholder = QLabel("Selective sync folders will appear here.")
        placeholder.setObjectName("mutedText")

        layout.addWidget(folders_title)
        layout.addWidget(placeholder)
        layout.addStretch()

        scroll.setWidget(content)
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        self._set_controls(False, False, False)

    def update_state(self, state: ApplicationState) -> None:
        status = state.status
        if status is not None:
            sync = status.sync
            self.root_path.setText(sync.root_path)
            self.local_card.set_metric(
                f"{sync.local.files:,}",
                f"{format_bytes(sync.local.bytes)} locally",
            )
            self.remote_card.set_metric(
                f"{sync.remote.files:,}",
                f"{format_bytes(sync.remote.bytes)} in cloud",
            )
            self.folder_card.set_metric(f"{sync.folder_count:,}", "folders")

        self._update_runtime_label(state)
        self._update_controls(state)

    def _update_runtime_label(self, state: ApplicationState) -> None:
        if state.status is not None and not state.status.sync.enabled:
            text, color = "● Sync disabled", "#e66b6b"
        elif state.sync_operation == SyncOperation.STARTING:
            text, color = "● Starting sync…", "#6173e8"
        elif state.sync_operation == SyncOperation.STOPPING:
            text, color = "● Stopping sync…", "#6173e8"
        elif state.sync_operation == SyncOperation.TRIGGERING:
            text, color = "● Syncing now…", "#6173e8"
        elif state.sync_mode == SyncMode.AUTOMATIC:
            text, color = "● Automatic sync enabled", "#62c98a"
        elif state.sync_mode == SyncMode.TRIGGERED:
            text, color = "● Manual sync mode", "#e6a75f"
        else:
            text, color = "● Sync mode unknown", "#8b909a"

        if state.sync_activity_status:
            text = f"{text} — {state.sync_activity_status}"
        elif state.sync_activity == SyncActivity.LISTENING:
            text = f"{text} — listening for changes"

        self.runtime_status.setText(text)
        self.runtime_status.setStyleSheet(f"color: {color}; font-weight: 600;")

    def _update_controls(self, state: ApplicationState) -> None:
        status = state.status
        if not state.connected or status is None or not status.sync.enabled:
            self._set_controls(False, False, False)
            return

        if state.sync_operation != SyncOperation.IDLE:
            self._set_controls(False, False, False)
        elif state.sync_mode == SyncMode.AUTOMATIC:
            self._set_controls(False, True, False)
        elif state.sync_mode == SyncMode.TRIGGERED:
            self._set_controls(True, False, True)
        else:
            self._set_controls(False, False, False)

    def _set_controls(self, start: bool, stop: bool, trigger: bool) -> None:
        self.start_button.setEnabled(start)
        self.stop_button.setEnabled(stop)
        self.trigger_button.setEnabled(trigger)
