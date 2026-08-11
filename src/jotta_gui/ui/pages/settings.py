from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
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

from jotta_gui.application.state import ApplicationState, ConfigOperation

from ._shared import make_scroll_page


@dataclass(frozen=True, slots=True)
class _SettingSpec:
    key: str
    label: str
    description: str
    kind: str = "text"


_SETTING_GROUPS: tuple[tuple[str, tuple[_SettingSpec, ...]], ...] = (
    (
        "Transfer & performance",
        (
            _SettingSpec(
                "downloadrate",
                "Download rate",
                "Bandwidth limit. Use 0 for unlimited, or values such as 5m or 512k.",
            ),
            _SettingSpec(
                "uploadrate",
                "Upload rate",
                "Bandwidth limit. Use 0 for unlimited, or values such as 5m or 512k.",
            ),
            _SettingSpec(
                "checksumreadrate",
                "Checksum read rate",
                "Limits disk bandwidth used while checksumming files before upload.",
            ),
            _SettingSpec(
                "maxdownloads",
                "Concurrent downloads",
                "Maximum number of simultaneous downloads. The CLI validates the range.",
            ),
            _SettingSpec(
                "maxuploads",
                "Concurrent uploads",
                "Maximum number of simultaneous uploads. The CLI validates the range.",
            ),
        ),
    ),
    (
        "Backup scanning",
        (
            _SettingSpec(
                "scaninterval",
                "Scan interval",
                "Examples: 30m, 2h, 1h30m. Use 0 for filesystem-triggered realtime backup.",
            ),
            _SettingSpec(
                "ignorehiddenfiles",
                "Ignore hidden files",
                "Exclude hidden files from backup and folder archive operations.",
                "bool",
            ),
            _SettingSpec(
                "slowmomode",
                "Slowmo mode",
                "Reduce CPU and disk pressure while scanning. Jotta documents values from 0 to 50.",
            ),
        ),
    ),
    (
        "Diagnostics logging",
        (
            _SettingSpec(
                "logscanignores",
                "Log ignored files",
                "Write the reason each scanned file was ignored to the jottad logfile.",
                "bool",
            ),
            _SettingSpec(
                "logtransfers",
                "Log transfers",
                "Log results for upload/download HTTP requests, not only transfer errors.",
                "bool",
            ),
        ),
    ),
)


class SettingsPage(QWidget):
    config_requested = Signal()
    config_set_requested = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._last_config_signature: tuple[tuple[str, str], ...] | None = None

        _, layout = make_scroll_page(self)

        title = QLabel("Settings")
        title.setObjectName("heroTitle")
        intro = QLabel(
            "Jotta GUI reads these values directly from jottad. Changes are sent "
            "through jotta-cli and then read back before the GUI considers them saved."
        )
        intro.setObjectName("mutedText")
        intro.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(intro)

        layout.addWidget(self._build_runtime_card())

        config_header = QHBoxLayout()
        config_title = QLabel("Jottad configuration")
        config_title.setObjectName("sectionTitle")
        self.refresh_config_button = QPushButton("Refresh configuration")
        self.refresh_config_button.setObjectName("secondaryButton")
        self.refresh_config_button.clicked.connect(self.config_requested.emit)
        config_header.addWidget(config_title)
        config_header.addStretch()
        config_header.addWidget(self.refresh_config_button)
        layout.addLayout(config_header)

        self.config_status = QLabel("Configuration has not been loaded yet.")
        self.config_status.setObjectName("mutedText")
        self.config_status.setWordWrap(True)
        layout.addWidget(self.config_status)

        self.setting_inputs: dict[str, QLineEdit | QComboBox] = {}
        self.setting_apply_buttons: dict[str, QPushButton] = {}
        for group_title, specs in _SETTING_GROUPS:
            layout.addWidget(self._build_setting_group(group_title, specs))

        raw_title = QLabel("Raw configuration")
        raw_title.setObjectName("sectionTitle")
        raw_help = QLabel(
            "Complete output from jotta-cli config. Settings that Jotta adds in a future "
            "release remain visible here even before dedicated controls are added."
        )
        raw_help.setObjectName("mutedText")
        raw_help.setWordWrap(True)
        self.raw_config = QPlainTextEdit()
        self.raw_config.setObjectName("configOutput")
        self.raw_config.setReadOnly(True)
        self.raw_config.setMaximumHeight(220)
        self.raw_config.setPlainText("Configuration has not been loaded yet.")
        layout.addWidget(raw_title)
        layout.addWidget(raw_help)
        layout.addWidget(self.raw_config)
        layout.addStretch()

    def _build_runtime_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("featureCard")
        grid = QGridLayout(card)
        grid.setContentsMargins(18, 16, 18, 16)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)

        title = QLabel("Jotta runtime")
        title.setObjectName("sectionTitle")
        grid.addWidget(title, 0, 0, 1, 2)

        self.runtime_values: dict[str, QLabel] = {}
        fields = (
            ("Account", "email"),
            ("Device", "device"),
            ("Hostname", "hostname"),
            ("Jotta CLI", "cli_version"),
            ("jottad", "daemon_version"),
            ("Executable", "daemon_executable"),
            ("Sync root", "sync_root"),
            ("App data", "appdata"),
            ("Logfile", "logfile"),
        )
        for row, (label_text, key) in enumerate(fields, start=1):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            value = QLabel("—")
            value.setObjectName("fieldValue")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setWordWrap(True)
            self.runtime_values[key] = value
            grid.addWidget(label, row, 0)
            grid.addWidget(value, row, 1)
        grid.setColumnStretch(1, 1)
        return card

    def _build_setting_group(
        self,
        title_text: str,
        specs: tuple[_SettingSpec, ...],
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("featureCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("rowTitle")
        layout.addWidget(title)

        for spec in specs:
            row = QFrame()
            row.setObjectName("settingRow")
            grid = QGridLayout(row)
            grid.setContentsMargins(0, 8, 0, 8)
            grid.setHorizontalSpacing(14)
            grid.setVerticalSpacing(3)

            label = QLabel(spec.label)
            label.setObjectName("fieldValue")
            description = QLabel(spec.description)
            description.setObjectName("mutedText")
            description.setWordWrap(True)

            if spec.kind == "bool":
                editor: QLineEdit | QComboBox = QComboBox()
                editor.addItems(("false", "true"))
            else:
                editor = QLineEdit()
                editor.setPlaceholderText("—")
            editor.setObjectName("settingInput")

            apply_button = QPushButton("Apply")
            apply_button.setObjectName("secondaryButton")
            apply_button.clicked.connect(
                lambda checked=False, key=spec.key: self._apply_setting(key)
            )

            self.setting_inputs[spec.key] = editor
            self.setting_apply_buttons[spec.key] = apply_button

            grid.addWidget(label, 0, 0)
            grid.addWidget(editor, 0, 1)
            grid.addWidget(apply_button, 0, 2)
            grid.addWidget(description, 1, 0, 1, 3)
            grid.setColumnStretch(1, 1)
            layout.addWidget(row)

        return card

    def activate(self) -> None:
        """Refresh configuration when Settings becomes the active page."""

        self.config_requested.emit()

    def update_state(self, state: ApplicationState) -> None:
        self._update_runtime(state)
        self._update_config(state)

    def _update_runtime(self, state: ApplicationState) -> None:
        snapshot = state.snapshot
        version = state.version

        account = snapshot.account if snapshot is not None else None
        sync = snapshot.sync if snapshot is not None else None
        mapping = {
            "email": account.email if account else None,
            "device": account.device_name if account else None,
            "hostname": account.hostname if account else None,
            "cli_version": version.cli_version if version else None,
            "daemon_version": version.daemon_version if version else None,
            "daemon_executable": version.daemon_executable if version else None,
            "sync_root": str(sync.root_path) if sync and sync.root_path else None,
            "appdata": version.appdata_path if version else None,
            "logfile": version.logfile_path if version else None,
        }
        for key, value in mapping.items():
            self.runtime_values[key].setText(value or "—")

    def _update_config(self, state: ApplicationState) -> None:
        config = state.config
        operation = state.config_operation
        busy = state.config_busy

        if state.config_error:
            self.config_status.setText(f"Configuration error: {state.config_error}")
        elif operation == ConfigOperation.LOADING:
            self.config_status.setText("Loading configuration from jottad…")
        elif operation == ConfigOperation.SAVING:
            setting = state.config_saving_setting or "setting"
            self.config_status.setText(f"Saving {setting}…")
        elif config is not None:
            self.config_status.setText("Configuration loaded from jottad.")
        else:
            self.config_status.setText("Configuration has not been loaded yet.")

        self.refresh_config_button.setEnabled(not busy)
        for button in self.setting_apply_buttons.values():
            button.setEnabled(not busy and config is not None)
        for editor in self.setting_inputs.values():
            editor.setEnabled(not busy and config is not None)

        if config is None:
            if not busy:
                self.raw_config.setPlainText("Configuration has not been loaded yet.")
            return

        signature = tuple((entry.name, entry.value) for entry in config.entries)
        if signature != self._last_config_signature:
            self._last_config_signature = signature
            for key, editor in self.setting_inputs.items():
                value = config.get(key)
                if value is None:
                    editor.setEnabled(False)
                    self.setting_apply_buttons[key].setEnabled(False)
                    if isinstance(editor, QLineEdit):
                        editor.clear()
                    continue

                if isinstance(editor, QComboBox):
                    normalized = value.casefold()
                    if normalized in {"true", "false"}:
                        editor.setCurrentText(normalized)
                    else:
                        editor.setEnabled(False)
                        self.setting_apply_buttons[key].setEnabled(False)
                else:
                    editor.setText(value)

            self.raw_config.setPlainText(config.raw_output)

    def _apply_setting(self, key: str) -> None:
        editor = self.setting_inputs[key]
        if isinstance(editor, QComboBox):
            value = editor.currentText()
        else:
            value = editor.text().strip()
        if key in {"downloadrate", "uploadrate", "checksumreadrate"} and value.casefold() == "unlimited":
            value = "0"
        if value:
            self.config_set_requested.emit(key, value)
