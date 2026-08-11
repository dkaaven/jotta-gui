from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from jotta_gui.application.state import (
    ApplicationState,
    BackupIgnoreOperation,
)
from jotta_gui.config import IgnorePreset, load_ignore_presets
from jotta_gui.jotta.models import BackupStatus
from jotta_gui.ui.components import MetricCard
from jotta_gui.ui.formatting import format_bytes, format_count, format_timestamp_ms

from ._shared import make_scroll_page


class BackupPage(QWidget):
    rules_requested = Signal(str)
    ignore_add_requested = Signal(str, str)
    ignore_remove_requested = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.presets = load_ignore_presets()
        self._backup_names: tuple[str, ...] = ()
        self._last_state = ApplicationState()
        self._load_on_available = False

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

        layout.addWidget(self._build_ignore_rules())
        layout.addStretch()

    def _build_ignore_rules(self) -> QFrame:
        card = QFrame()
        card.setObjectName("featureCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel("Ignore rules")
        title.setObjectName("sectionTitle")
        help_text = QLabel(
            "Rules shown here come directly from jotta-cli. Presets are only shortcuts "
            "for adding common patterns; Jotta remains the source of truth."
        )
        help_text.setObjectName("mutedText")
        help_text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(help_text)

        selector_row = QHBoxLayout()
        self.backup_selector = QComboBox()
        self.backup_selector.setObjectName("backupSelector")
        self.backup_selector.currentTextChanged.connect(self._backup_selected)
        self.refresh_rules_button = QPushButton("Refresh rules")
        self.refresh_rules_button.setObjectName("secondaryButton")
        self.refresh_rules_button.clicked.connect(self._request_current_rules)
        selector_row.addWidget(self.backup_selector, stretch=1)
        selector_row.addWidget(self.refresh_rules_button)
        layout.addLayout(selector_row)

        self.rules_status = QLabel("Choose a backup to inspect its ignore rules.")
        self.rules_status.setObjectName("mutedText")
        layout.addWidget(self.rules_status)

        self.current_rules = QPlainTextEdit()
        self.current_rules.setObjectName("ruleOutput")
        self.current_rules.setReadOnly(True)
        self.current_rules.setMaximumHeight(170)
        self.current_rules.setPlainText("Rules have not been loaded yet.")
        layout.addWidget(self.current_rules)

        preset_title = QLabel("Common rules")
        preset_title.setObjectName("rowTitle")
        layout.addWidget(preset_title)

        self.preset_buttons: dict[str, QPushButton] = {}
        self.preset_remove_buttons: dict[str, QPushButton] = {}
        for preset in self.presets:
            layout.addWidget(self._preset_row(preset))

        custom_title = QLabel("Custom pattern")
        custom_title.setObjectName("rowTitle")
        layout.addWidget(custom_title)

        custom_row = QHBoxLayout()
        self.custom_pattern = QLineEdit()
        self.custom_pattern.setPlaceholderText("Example: **/.cache")
        self.custom_pattern.returnPressed.connect(self._add_custom_pattern)
        self.custom_add_button = QPushButton("Add rule")
        self.custom_add_button.setObjectName("primaryButton")
        self.custom_add_button.clicked.connect(self._add_custom_pattern)
        self.custom_remove_button = QPushButton("Remove rule")
        self.custom_remove_button.clicked.connect(self._remove_custom_pattern)
        custom_row.addWidget(self.custom_pattern, stretch=1)
        custom_row.addWidget(self.custom_add_button)
        custom_row.addWidget(self.custom_remove_button)
        layout.addLayout(custom_row)

        return card

    def _preset_row(self, preset: IgnorePreset) -> QFrame:
        row = QFrame()
        row.setObjectName("ignorePresetRow")
        layout = QGridLayout(row)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(3)

        label = QLabel(preset.label)
        label.setObjectName("rowTitle")
        pattern = QLabel(preset.pattern)
        pattern.setObjectName("patternText")
        description = QLabel(preset.description)
        description.setObjectName("mutedText")
        description.setWordWrap(True)
        add_button = QPushButton("Add")
        add_button.clicked.connect(
            lambda checked=False, value=preset.pattern: self._emit_add(value)
        )
        remove_button = QPushButton("Remove")
        remove_button.setObjectName("secondaryButton")
        remove_button.clicked.connect(
            lambda checked=False, value=preset.pattern: self._emit_remove(value)
        )
        self.preset_buttons[preset.id] = add_button
        self.preset_remove_buttons[preset.id] = remove_button

        actions = QHBoxLayout()
        actions.setSpacing(6)
        actions.addWidget(add_button)
        actions.addWidget(remove_button)

        layout.addWidget(label, 0, 0)
        layout.addWidget(pattern, 0, 1)
        layout.addLayout(actions, 0, 2, 2, 1)
        layout.addWidget(description, 1, 0, 1, 2)
        layout.setColumnStretch(1, 1)
        return row

    def activate(self) -> None:
        """Refresh rules when the Backup page becomes the active page."""

        self._load_on_available = True
        self._maybe_load_on_available()

    def update_state(self, state: ApplicationState) -> None:
        self._last_state = state
        self._clear_rows()
        snapshot = state.snapshot
        if snapshot is None:
            self.summary.setText("No backup snapshot available")
            self.folder_card.set_metric("—", "Configured")
            self.file_card.set_metric("—", "Known file count")
            self.size_card.set_metric("—", "Known backup size")
            self._add_empty("Backup information is unavailable.")
            self._set_backup_names(())
            self._update_rule_controls(state)
            return

        backups = snapshot.backups
        self.summary.setText(
            f"{len(backups)} backup folder{'s' if len(backups) != 1 else ''} reported by jottad"
        )
        self.folder_card.set_metric(str(len(backups)), "configured")
        self.file_card.set_metric(
            format_count(_sum_known(b.count.files for b in backups)), "known files"
        )
        self.size_card.set_metric(
            format_bytes(_sum_known(b.count.bytes for b in backups)), "known data"
        )

        if not backups:
            self._add_empty("No backup folders are configured.")
        else:
            for backup in backups:
                self.rows.addWidget(BackupRow(backup))

        self._set_backup_names(
            tuple(backup.name for backup in backups if backup.name)
        )
        self._update_rule_controls(state)
        self._maybe_load_on_available()

    def _set_backup_names(self, names: tuple[str, ...]) -> None:
        if names == self._backup_names:
            return

        previous = self.backup_selector.currentText()
        blocker = QSignalBlocker(self.backup_selector)
        self.backup_selector.clear()
        self.backup_selector.addItems(names)
        if previous in names:
            self.backup_selector.setCurrentText(previous)
        del blocker
        self._backup_names = names

    def _update_rule_controls(self, state: ApplicationState) -> None:
        selected = self.backup_selector.currentText()
        ignore_state = state.backup_ignores
        matching = bool(selected) and ignore_state.backup_name == selected
        busy = matching and ignore_state.busy

        if not selected:
            self.rules_status.setText("No named backup is available for ignore rules.")
            self.current_rules.setPlainText("No backup selected.")
        elif not matching:
            self.rules_status.setText("Rules have not been loaded for this backup yet.")
            self.current_rules.setPlainText("Select Refresh rules to query jotta-cli.")
        elif ignore_state.operation == BackupIgnoreOperation.LOADING:
            self.rules_status.setText(f"Loading rules for {selected}…")
        elif ignore_state.operation == BackupIgnoreOperation.ADDING:
            self.rules_status.setText(f"Adding rule to {selected}…")
        elif ignore_state.operation == BackupIgnoreOperation.REMOVING:
            self.rules_status.setText(f"Removing rule from {selected}…")
        else:
            self.rules_status.setText(f"Current rules for {selected}")

        if matching and ignore_state.output is not None:
            self.current_rules.setPlainText(
                ignore_state.output or "(jotta-cli returned no rule output on stdout or stderr)"
            )

        enabled = bool(selected) and state.connected and not busy
        self.backup_selector.setEnabled(bool(self._backup_names) and not busy)
        self.refresh_rules_button.setEnabled(enabled)
        self.custom_pattern.setEnabled(enabled)
        self.custom_add_button.setEnabled(enabled)
        self.custom_remove_button.setEnabled(enabled)
        for button in self.preset_buttons.values():
            button.setEnabled(enabled)
        for button in self.preset_remove_buttons.values():
            button.setEnabled(enabled)

    def _backup_selected(self, backup_name: str) -> None:
        self._load_on_available = False
        self._update_rule_controls(self._last_state)
        if backup_name:
            self.rules_requested.emit(backup_name)

    def _maybe_load_on_available(self) -> None:
        backup_name = self.backup_selector.currentText()
        if not self._load_on_available or not backup_name:
            return
        self._load_on_available = False
        self.rules_requested.emit(backup_name)

    def _request_current_rules(self) -> None:
        backup_name = self.backup_selector.currentText()
        if backup_name:
            self.rules_requested.emit(backup_name)

    def _emit_add(self, pattern: str) -> None:
        backup_name = self.backup_selector.currentText()
        if backup_name and pattern:
            self.ignore_add_requested.emit(backup_name, pattern)

    def _emit_remove(self, pattern: str) -> None:
        backup_name = self.backup_selector.currentText()
        if backup_name and pattern:
            self.ignore_remove_requested.emit(backup_name, pattern)

    def _add_custom_pattern(self) -> None:
        pattern = self.custom_pattern.text().strip()
        if not pattern:
            return
        self._emit_add(pattern)
        self.custom_pattern.clear()

    def _remove_custom_pattern(self) -> None:
        pattern = self.custom_pattern.text().strip()
        if not pattern:
            return
        self._emit_remove(pattern)
        self.custom_pattern.clear()

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
