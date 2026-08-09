
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from jotta_gui.application.controller import ApplicationController
from jotta_gui.application.state import ApplicationState
from jotta_gui.ui.components import Header, Sidebar
from jotta_gui.ui.pages import BackupPage, OverviewPage, SettingsPage, SyncPage

PAGE_INFO = {
    "overview": ("Overview", "Your Jottacloud at a glance"),
    "sync": ("Sync", "Files synchronized with Jottacloud"),
    "backup": ("Backup", "Protected folders and backup status"),
    "settings": ("Settings", "Configure Jotta GUI"),
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Jotta GUI")
        self.resize(1100, 820)
        self.setMinimumSize(950, 650)

        self.sidebar = Sidebar()
        self.header = Header()
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
        self.controller.state_changed.connect(self.update_state)

        self.sidebar.page_selected.connect(self.change_page)
        self.sync_page.start_requested.connect(self.controller.start_sync)
        self.sync_page.stop_requested.connect(self.controller.stop_sync)
        self.sync_page.trigger_requested.connect(self.controller.trigger_sync)

        self._build_layout()
        self.change_page("overview")
        self.controller.start()

    def _build_layout(self) -> None:
        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.header)
        content_layout.addWidget(self.pages, stretch=1)

        central = QWidget()
        shell_layout = QHBoxLayout(central)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self.sidebar)
        shell_layout.addWidget(content, stretch=1)
        self.setCentralWidget(central)

    def change_page(self, page_name: str) -> None:
        page = self.page_widgets.get(page_name)
        page_info = PAGE_INFO.get(page_name)
        if page is None or page_info is None:
            return

        self.pages.setCurrentWidget(page)
        self.header.set_page(*page_info)

    def update_state(self, state: ApplicationState) -> None:
        self.header.update_state(state)
        self.overview_page.update_state(state)
        self.sync_page.update_state(state)
