"""ナビゲーションドロワーウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


logger = logging.getLogger(__name__)

# 設定ページのインデックス
SETTINGS_PAGE_INDEX = 5


class DrawerOverlay(QWidget):
    """ドロワーの背景オーバーレイ（半透明）.

    ドロワー表示中にメインコンテンツを覆い、クリックでドロワーを閉じる。

    Signals:
        clicked: オーバーレイクリック時に発火.
    """

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """DrawerOverlayを初期化する.

        Args:
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self.setObjectName("drawer_overlay")
        self.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
        self.hide()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """マウスクリック時にclickedシグナルを発火する.

        Args:
            event: マウスイベント.
        """
        self.clicked.emit()
        super().mousePressEvent(event)


class NavigationDrawer(QFrame):
    """スライドインナビゲーションドロワー.

    ハンバーガーメニューからスライドインするナビゲーション。
    5ページ＋設定メニューを含む。

    Attributes:
        _button_group: ボタングループ（排他選択）.
        _buttons: ナビゲーションボタンのリスト.

    Signals:
        nav_item_clicked: ナビ項目クリック時に発火（ページインデックス）.
        settings_clicked: 設定クリック時に発火.
    """

    nav_item_clicked = Signal(int)
    settings_clicked = Signal()

    DRAWER_WIDTH = 260

    def __init__(self, parent: QWidget | None = None) -> None:
        """NavigationDrawerを初期化する.

        Args:
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self.setObjectName("navigation_drawer")
        self.setFixedWidth(self.DRAWER_WIDTH)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._buttons: list[QPushButton] = []

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 16, 12, 16)
        self._layout.setSpacing(4)

        # アプリタイトル
        title = QLabel("Study Planner")
        title.setObjectName("section_title")
        title.setStyleSheet(
            "font-size: 18px; font-weight: 700; padding: 8px 4px 16px 4px;"
        )
        self._layout.addWidget(title)

        # ナビゲーション項目
        nav_pages: list[tuple[str, str]] = [
            ("\U0001f3e0", "\u30c0\u30c3\u30b7\u30e5\u30dc\u30fc\u30c9"),
            ("\U0001f3af", "3W1H \u76ee\u6a19"),
            ("\U0001f4ca", "\u30ac\u30f3\u30c8\u30c1\u30e3\u30fc\u30c8"),
            ("\U0001f4da", "\u66f8\u7c4d"),
            ("\U0001f4c8", "\u7d71\u8a08"),
        ]
        for i, (icon, label) in enumerate(nav_pages):
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("sidebar_button")
            btn.setCheckable(True)
            btn.setFixedHeight(44)
            self._button_group.addButton(btn, i)
            self._buttons.append(btn)
            self._layout.addWidget(btn)
            btn.clicked.connect(lambda _checked, idx=i: self.nav_item_clicked.emit(idx))

        self._layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # 設定ボタン
        self._settings_button = QPushButton("  \u2699\ufe0f  \u8a2d\u5b9a")
        self._settings_button.setObjectName("sidebar_button")
        self._settings_button.setCheckable(True)
        self._settings_button.setFixedHeight(44)
        self._button_group.addButton(self._settings_button, SETTINGS_PAGE_INDEX)
        self._buttons.append(self._settings_button)
        self._layout.addWidget(self._settings_button)
        self._settings_button.clicked.connect(
            lambda _checked: self.settings_clicked.emit()
        )

        # 最初のボタンを選択
        if self._buttons:
            self._buttons[0].setChecked(True)

        self.hide()
        logger.debug("NavigationDrawer created")

    def set_checked_button(self, index: int) -> None:
        """指定インデックスのボタンをチェック状態にする.

        Args:
            index: ボタンインデックス.
        """
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)
