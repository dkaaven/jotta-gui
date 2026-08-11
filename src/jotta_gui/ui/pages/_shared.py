from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget


def make_scroll_page(parent: QWidget) -> tuple[QWidget, QVBoxLayout]:
    scroll = QScrollArea()
    scroll.setObjectName("pageScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    content = QWidget()
    content.setObjectName("pageContent")
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(28, 28, 28, 28)
    content_layout.setSpacing(18)
    scroll.setWidget(content)

    page_layout = QVBoxLayout(parent)
    page_layout.setContentsMargins(0, 0, 0, 0)
    page_layout.setSpacing(0)
    page_layout.addWidget(scroll)
    return content, content_layout
