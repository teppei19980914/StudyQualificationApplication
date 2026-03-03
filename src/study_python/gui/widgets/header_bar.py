"""ヘッダーバーウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


logger = logging.getLogger(__name__)


class HeaderBar(QWidget):
    """アプリケーションのヘッダーバー.

    ハンバーガーボタンとページタイトルを表示する。

    Attributes:
        _hamburger_button: ハンバーガーメニューボタン.
        _title_label: ページタイトルラベル.

    Signals:
        hamburger_clicked: ハンバーガーボタンクリック時に発火.
    """

    hamburger_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """HeaderBarを初期化する.

        Args:
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self.setObjectName("header_bar")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)

        self._hamburger_button = QPushButton("\u2630")
        self._hamburger_button.setObjectName("hamburger_button")
        self._hamburger_button.setFixedSize(36, 36)
        self._hamburger_button.clicked.connect(self.hamburger_clicked.emit)
        layout.addWidget(self._hamburger_button)

        self._title_label = QLabel("\u30c0\u30c3\u30b7\u30e5\u30dc\u30fc\u30c9")
        self._title_label.setObjectName("header_title")
        layout.addWidget(self._title_label)

        layout.addStretch()

        logger.debug("HeaderBar created")

    def set_title(self, title: str) -> None:
        """ヘッダータイトルを設定する.

        Args:
            title: ページタイトル.
        """
        self._title_label.setText(title)
