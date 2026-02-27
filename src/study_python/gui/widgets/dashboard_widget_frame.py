"""ダッシュボードウィジェットフレーム."""

from __future__ import annotations

import logging

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager


logger = logging.getLogger(__name__)

DRAG_MIME_TYPE = "application/x-dashboard-widget-index"
PALETTE_DRAG_MIME_TYPE = "application/x-dashboard-widget-type"


class DashboardWidgetFrame(QFrame):
    """ダッシュボードウィジェットのラッパーフレーム.

    編集モード時にドラッグハンドル、リサイズ、削除ボタンを表示する。

    Signals:
        remove_requested: 削除リクエスト（ウィジェットインデックス）.
        resize_requested: リサイズリクエスト（ウィジェットインデックス）.

    Attributes:
        _theme_manager: テーママネージャ.
        _widget_index: ウィジェットのインデックス.
        _display_name: ウィジェットの表示名.
        _edit_mode: 編集モードかどうか.
        _header: ヘッダーウィジェット.
        _content_widget: 内包するウィジェット.
        _drag_start_pos: ドラッグ開始位置.
        _resizable: リサイズ可能かどうか.
    """

    remove_requested = Signal(int)
    resize_requested = Signal(int)

    def __init__(
        self,
        content_widget: QWidget,
        widget_index: int,
        display_name: str,
        theme_manager: ThemeManager,
        resizable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """DashboardWidgetFrameを初期化する.

        Args:
            content_widget: 内包するウィジェット.
            widget_index: ウィジェットのインデックス.
            display_name: ウィジェットの表示名.
            theme_manager: テーママネージャ.
            resizable: リサイズ可能かどうか.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._widget_index = widget_index
        self._display_name = display_name
        self._edit_mode = False
        self._content_widget = content_widget
        self._drag_start_pos: QPoint | None = None
        self._resizable = resizable
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("dashboard_widget_frame")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ヘッダーバー（編集モード時のみ表示）
        self._header = QWidget()
        self._header.setObjectName("dashboard_widget_header")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(8)

        # ドラッグハンドル
        self._drag_handle = QLabel("\u2630")
        self._drag_handle.setStyleSheet(
            "font-size: 14px; cursor: grab; padding: 0 4px;"
        )
        self._drag_handle.setCursor(Qt.CursorShape.OpenHandCursor)
        header_layout.addWidget(self._drag_handle)

        # ウィジェット名
        self._name_label = QLabel(self._display_name)
        self._name_label.setStyleSheet("font-size: 12px; font-weight: 600;")
        header_layout.addWidget(self._name_label)

        header_layout.addStretch()

        # リサイズボタン
        self._resize_button = QPushButton("\u2194")
        self._resize_button.setObjectName("secondary_button")
        self._resize_button.setFixedSize(28, 28)
        self._resize_button.setToolTip("\u30b5\u30a4\u30ba\u5207\u66ff")
        self._resize_button.clicked.connect(self._on_resize_clicked)
        self._resize_button.setVisible(self._resizable)
        header_layout.addWidget(self._resize_button)

        # 削除ボタン
        self._remove_button = QPushButton("\u2715")
        self._remove_button.setObjectName("danger_button")
        self._remove_button.setFixedSize(28, 28)
        self._remove_button.setToolTip("\u524a\u9664")
        self._remove_button.clicked.connect(self._on_remove_clicked)
        header_layout.addWidget(self._remove_button)

        self._header.setVisible(False)
        layout.addWidget(self._header)

        # コンテンツ
        layout.addWidget(self._content_widget)

    def _apply_style(self) -> None:
        """スタイルを適用する."""
        colors = self._theme_manager.get_colors()
        border = colors.get("border", "#45475A")
        bg_card = colors.get("bg_card", "#2A2A3C")

        if self._edit_mode:
            self.setStyleSheet(
                f"QFrame#dashboard_widget_frame {{"
                f"  border: 2px dashed {border};"
                f"  border-radius: 8px;"
                f"  background-color: {bg_card};"
                f"}}"
            )
        else:
            self.setStyleSheet(
                "QFrame#dashboard_widget_frame {"
                "  border: none;"
                "  background-color: transparent;"
                "}"
            )

    @property
    def widget_index(self) -> int:
        """ウィジェットのインデックスを返す."""
        return self._widget_index

    @widget_index.setter
    def widget_index(self, value: int) -> None:
        """ウィジェットのインデックスを設定する.

        Args:
            value: 新しいインデックス.
        """
        self._widget_index = value

    @property
    def content_widget(self) -> QWidget:
        """内包するウィジェットを返す."""
        return self._content_widget

    def set_edit_mode(self, enabled: bool) -> None:
        """編集モードを切り替える.

        Args:
            enabled: 編集モードを有効にするかどうか.
        """
        self._edit_mode = enabled
        self._header.setVisible(enabled)
        self._apply_style()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウスプレスイベントハンドラ.

        Args:
            event: マウスイベント.
        """
        if self._edit_mode and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # pragma: no cover
        """マウスムーブイベントハンドラ.

        Args:
            event: マウスイベント.
        """
        if (
            self._edit_mode
            and self._drag_start_pos is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            distance = (
                event.position().toPoint() - self._drag_start_pos
            ).manhattanLength()
            if distance >= 10:
                self._start_drag()
                self._drag_start_pos = None
                return
        super().mouseMoveEvent(event)

    def _start_drag(self) -> None:  # pragma: no cover
        """ドラッグを開始する."""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData(
            DRAG_MIME_TYPE,
            str(self._widget_index).encode("utf-8"),
        )
        drag.setMimeData(mime_data)

        # ドラッグ中のプレビュー画像
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio))

        drag.exec(Qt.DropAction.MoveAction)

    def _on_remove_clicked(self) -> None:
        """削除ボタンクリックハンドラ."""
        self.remove_requested.emit(self._widget_index)

    def _on_resize_clicked(self) -> None:
        """リサイズボタンクリックハンドラ."""
        self.resize_requested.emit(self._widget_index)
