from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from jotta_gui.application.controller import ApplicationController
from jotta_gui.application.state import ApplicationState
from jotta_gui.ui.components import ErrorBanner, Header, Sidebar
from jotta_gui.ui.pages import BackupPage, OverviewPage, SettingsPage, SyncPage

PAGE_INFO = {
    "overview": ("Overview", "Account, storage and protection at a glance"),
    "sync": ("Sync", "Continuous and triggered synchronization"),
    "backup": ("Backup", "Folders protected by continuous backup"),
    "settings": ("Settings", "Account and device information"),
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Jotta GUI")
        self.resize(1120, 780)
        self.setMinimumSize(920, 620)

        self.sidebar = Sidebar()
        self.header = Header()
        self.error_banner = ErrorBanner()
        self.pages = QStackedWidget()

        self.overview_page = OverviewPage()
        self.sync_page = SyncPage()
        self.backup_page = BackupPage()
        self.settings_page = SettingsPage()
        self.page_widgets: dict[str, QWidget] = {
            "overview": self.overview_page,
            "sync": self.sync_page,
            "backup": self.backup_page,
            "settings": self.settings_page,
        }
        for page in self.page_widgets.values():
            self.pages.addWidget(page)

        self.controller = ApplicationController(self)
        self._connect_signals()
        self._build_layout()
        self.change_page("overview")
        self.controller.start()

    def _connect_signals(self) -> None:
        self.controller.state_changed.connect(self.update_state)
        self.sidebar.page_selected.connect(self.change_page)
        self.header.refresh_requested.connect(self.controller.refresh)
        self.error_banner.dismissed.connect(self.controller.clear_error)

        self.sync_page.start_requested.connect(self.controller.start_sync)
        self.sync_page.force_start_requested.connect(
            lambda: self.controller.start_sync(force=True)
        )
        self.sync_page.stop_requested.connect(self.controller.stop_sync)
        self.sync_page.trigger_requested.connect(self.controller.trigger_sync)

    def _build_layout(self) -> None:
        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.header)
        content_layout.addWidget(self.error_banner)
        content_layout.addWidget(self.pages, stretch=1)

        central = QWidget()
        shell = QHBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        shell.addWidget(self.sidebar)
        shell.addWidget(content, stretch=1)
        self.setCentralWidget(central)

    def change_page(self, page_name: str) -> None:
        page = self.page_widgets.get(page_name)
        info = PAGE_INFO.get(page_name)
        if page is None or info is None:
            return
        self.pages.setCurrentWidget(page)
        self.header.set_page(*info)

    def update_state(self, state: ApplicationState) -> None:
        self.header.update_state(state)
        self.overview_page.update_state(state)
        self.sync_page.update_state(state)
        self.backup_page.update_state(state)
        self.settings_page.update_state(state)

        if state.error is None:
            self.error_banner.clear()
        else:
            self.error_banner.show_error(state.error.command, state.error.message)
