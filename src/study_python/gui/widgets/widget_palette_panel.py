"""ウィジェットパレットパネル."""

from __future__ import annotations

import logging

from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDrag, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.dashboard_widget_frame import PALETTE_DRAG_MIME_TYPE
from study_python.services.dashboard_layout_service import WidgetMetadata


logger = logging.getLogger(__name__)


class PaletteItem(QFrame):
    """パレット内の個別ウィジェットアイテム.

    ドラッグ操作でグリッドに追加できる。

    Attributes:
        _metadata: ウィジェットメタデータ.
        _theme_manager: テーママネージャ.
        _drag_start_pos: ドラッグ開始位置.
    """

    def __init__(
        self,
        metadata: WidgetMetadata,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """PaletteItemを初期化する.

        Args:
            metadata: ウィジェットメタデータ.
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._metadata = metadata
        self._theme_manager = theme_manager
        self._drag_start_pos: QPoint | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("palette_item")
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        colors = self._theme_manager.get_colors()
        border = colors.get("border", "#45475A")
        bg_card = colors.get("bg_card", "#2A2A3C")
        text_color = colors.get("text", "#CDD6F4")

        self.setStyleSheet(
            f"QFrame#palette_item {{"
            f"  background-color: {bg_card};"
            f"  border: 1px solid {border};"
            f"  border-radius: 6px;"
            f"  color: {text_color};"
            f"}}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        icon_label = QLabel(self._metadata.icon)
        icon_label.setStyleSheet("font-size: 16px; border: none;")
        icon_label.setFixedWidth(24)
        layout.addWidget(icon_label)

        name_label = QLabel(self._metadata.display_name)
        name_label.setStyleSheet("font-size: 13px; font-weight: 600; border: none;")
        layout.addWidget(name_label)

        layout.addStretch()

    @property
    def widget_type(self) -> str:
        """ウィジェットタイプを返す."""
        return self._metadata.widget_type

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウスプレスイベントハンドラ.

        Args:
            event: マウスイベント.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # pragma: no cover
        """マウスムーブイベントハンドラ.

        Args:
            event: マウスイベント.
        """
        if (
            self._drag_start_pos is not None
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
            PALETTE_DRAG_MIME_TYPE,
            self._metadata.widget_type.encode("utf-8"),
        )
        drag.setMimeData(mime_data)

        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap.scaled(180, 48, Qt.AspectRatioMode.KeepAspectRatio))

        drag.exec(Qt.DropAction.CopyAction)
        logger.debug(f"Palette drag started: {self._metadata.widget_type}")


class WidgetPalettePanel(QFrame):
    """ウィジェットパレットパネル.

    編集モード時に表示され、未配置ウィジェットを一覧表示する。

    Attributes:
        _theme_manager: テーママネージャ.
        _items_layout: アイテム配置用レイアウト.
        _palette_items: 現在のPaletteItemリスト.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """WidgetPalettePanelを初期化する.

        Args:
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._palette_items: list[PaletteItem] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setObjectName("widget_palette_panel")
        self.setFixedWidth(220)

        colors = self._theme_manager.get_colors()
        bg = colors.get("bg", "#1E1E2E")
        border = colors.get("border", "#45475A")
        text_color = colors.get("text", "#CDD6F4")

        self.setStyleSheet(
            f"QFrame#widget_palette_panel {{"
            f"  background-color: {bg};"
            f"  border-left: 1px solid {border};"
            f"  color: {text_color};"
            f"}}"
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        header_label = QLabel("\U0001f9e9 パーツ")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; border: none;")
        main_layout.addWidget(header_label)

        self._items_layout = QVBoxLayout()
        self._items_layout.setSpacing(6)
        main_layout.addLayout(self._items_layout)

        main_layout.addStretch()

    def update_items(self, available: list[WidgetMetadata]) -> None:
        """パレットアイテムを更新する.

        Args:
            available: 追加可能なウィジェットのメタデータリスト.
        """
        # 既存アイテムをクリア
        for item in self._palette_items:
            self._items_layout.removeWidget(item)
            item.deleteLater()
        self._palette_items.clear()

        # 新しいアイテムを追加
        for meta in available:
            item = PaletteItem(meta, self._theme_manager)
            self._items_layout.addWidget(item)
            self._palette_items.append(item)

        logger.debug(f"Palette updated: {len(available)} items")

    @property
    def palette_items(self) -> list[PaletteItem]:
        """現在のパレットアイテムリストを返す."""
        return list(self._palette_items)
