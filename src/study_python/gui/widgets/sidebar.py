"""サイドバーナビゲーションウィジェット."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class SidebarButton(QPushButton):
    """サイドバーのナビゲーションボタン."""

    def __init__(
        self, icon_text: str, label: str, parent: QWidget | None = None
    ) -> None:
        """SidebarButtonを初期化する.

        Args:
            icon_text: アイコン文字（絵文字）.
            label: ボタンのテキスト.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self.setObjectName("sidebar_button")
        self.setCheckable(True)
        self.setText(f"  {icon_text}  {label}")
        self.setFixedHeight(44)


class Sidebar(QWidget):
    """サイドバーナビゲーション.

    Signals:
        page_changed: ページ変更時に発行するシグナル（ページインデックス）.
    """

    page_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Sidebarを初期化する.

        Args:
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._buttons: list[SidebarButton] = []

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

        self._nav_pages: list[tuple[str, str]] = [
            ("\U0001f3af", "3W1H \u76ee\u6a19"),
            ("\U0001f4ca", "\u30ac\u30f3\u30c8\u30c1\u30e3\u30fc\u30c8"),
        ]
        for i, (icon, label) in enumerate(self._nav_pages):
            btn = SidebarButton(icon, label)
            self._button_group.addButton(btn, i)
            self._buttons.append(btn)
            self._layout.addWidget(btn)
            btn.clicked.connect(lambda _checked, idx=i: self._on_button_clicked(idx))

        self._layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # テーマ切替ボタン
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("secondary_button")
        self.theme_button.setFixedHeight(36)
        self._update_theme_button_text(is_dark=True)
        self._layout.addWidget(self.theme_button)

        # 最初のボタンを選択
        if self._buttons:
            self._buttons[0].setChecked(True)

    def _on_button_clicked(self, index: int) -> None:
        """ボタンクリック時のハンドラ.

        Args:
            index: ページインデックス.
        """
        self.page_changed.emit(index)

    def _update_theme_button_text(self, is_dark: bool) -> None:
        """テーマボタンのテキストを更新する.

        Args:
            is_dark: ダークテーマかどうか.
        """
        if is_dark:
            self.theme_button.setText(
                "\u2600\ufe0f  \u30e9\u30a4\u30c8\u30e2\u30fc\u30c9"
            )
        else:
            self.theme_button.setText(
                "\U0001f319  \u30c0\u30fc\u30af\u30e2\u30fc\u30c9"
            )

    def set_theme_indicator(self, is_dark: bool) -> None:
        """テーマインジケーターを更新する.

        Args:
            is_dark: ダークテーマかどうか.
        """
        self._update_theme_button_text(is_dark)
