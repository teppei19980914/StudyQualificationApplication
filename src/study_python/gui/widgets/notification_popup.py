"""通知ポップアップダイアログ."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.notification import Notification, NotificationType
from study_python.services.notification_service import NotificationService


logger = logging.getLogger(__name__)

# 通知タイプごとのアイコン
_TYPE_ICONS: dict[NotificationType, str] = {
    NotificationType.SYSTEM: "\U0001f4e2",
    NotificationType.ACHIEVEMENT: "\u2728",
}


class _ClickableFrame(QFrame):
    """クリック可能なQFrame.

    Attributes:
        clicked: クリック時に発火するシグナル.
    """

    clicked = Signal()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """マウスクリック時にclickedシグナルを発火する.

        Args:
            event: マウスイベント.
        """
        super().mousePressEvent(event)
        self.clicked.emit()


class NotificationPopup(QDialog):
    """通知一覧を表示するポップアップダイアログ.

    Attributes:
        _notification_service: 通知サービス.
        _theme_manager: テーママネージャ.
        _notification_items: 通知アイテムウィジェットのリスト.
    """

    def __init__(
        self,
        notification_service: NotificationService,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """NotificationPopupを初期化する.

        Args:
            notification_service: 通知サービス.
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._notification_service = notification_service
        self._theme_manager = theme_manager
        self._notification_items: list[QWidget] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setWindowTitle("通知")
        self.setMinimumWidth(380)
        self.setMinimumHeight(300)
        self.setMaximumHeight(500)

        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        text_color = colors.get("text", "#CDD6F4")
        border = colors.get("border", "#45475A")

        self.setStyleSheet(
            f"QDialog {{ background-color: {bg_card}; color: {text_color}; }}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # ヘッダー
        header_layout = QHBoxLayout()
        title_icon = QLabel("\U0001f514")
        title_icon.setStyleSheet("font-size: 18px;")
        header_layout.addWidget(title_icon)

        title_label = QLabel("通知")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self._mark_all_button = QPushButton("全て既読")
        self._mark_all_button.setObjectName("mark_all_read_button")
        self._mark_all_button.setFixedHeight(28)
        self._mark_all_button.setStyleSheet(
            f"QPushButton {{ background-color: {border}; border: none; "
            f"border-radius: 6px; padding: 4px 12px; font-size: 11px; }}"
        )
        self._mark_all_button.clicked.connect(self._on_mark_all_read)
        header_layout.addWidget(self._mark_all_button)

        layout.addLayout(header_layout)

        # 区切り線
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {border};")
        layout.addWidget(separator)

        # スクロール可能な通知リスト
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setSpacing(4)
        self._list_layout.setContentsMargins(0, 0, 0, 0)

        self._populate_list()

        self._list_layout.addStretch()
        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, 1)

        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.setFixedHeight(32)
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet(
            f"QPushButton {{ background-color: {border}; border: none; "
            f"border-radius: 6px; padding: 4px 16px; }}"
        )
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

    def _populate_list(self) -> None:
        """通知リストを構築する."""
        colors = self._theme_manager.get_colors()
        notifications = self._notification_service.get_all_notifications()
        if notifications:
            for notification in notifications:
                item = self._create_notification_item(notification, colors)
                self._list_layout.addWidget(item)
                self._notification_items.append(item)
        else:
            empty_label = QLabel("通知はありません")
            empty_label.setObjectName("empty_notification_label")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("font-size: 13px; padding: 20px;")
            self._list_layout.addWidget(empty_label)
            self._notification_items.append(empty_label)

    def _create_notification_item(
        self, notification: Notification, colors: dict[str, str]
    ) -> QWidget:
        """通知アイテムウィジェットを生成する.

        Args:
            notification: 通知データ.
            colors: テーマカラーパレット.

        Returns:
            通知アイテムウィジェット.
        """
        border = colors.get("border", "#45475A")
        accent = colors.get("accent", "#89B4FA")
        bg_hover = colors.get("bg_hover", "#45475A")
        text_muted = colors.get("text_muted", "#6C7086")

        item = _ClickableFrame()
        item.setObjectName("notification_item")
        item.setCursor(Qt.CursorShape.PointingHandCursor)
        item.setProperty("notification_id", notification.id)
        read_style = (
            f"QFrame#notification_item {{ border: 1px solid {border}; "
            f"border-radius: 8px; padding: 8px; }}"
        )
        unread_style = (
            f"QFrame#notification_item {{ border: 1px solid {accent}; "
            f"border-radius: 8px; padding: 8px; "
            f"background-color: {bg_hover}; }}"
        )
        if notification.is_read:
            item.setStyleSheet(read_style)
        else:
            item.setStyleSheet(unread_style)
        item.clicked.connect(
            lambda n=notification: self._on_item_clicked(n)
        )

        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(8, 6, 8, 6)
        item_layout.setSpacing(8)

        # アイコン
        icon = _TYPE_ICONS.get(notification.notification_type, "\U0001f514")
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        icon_label.setFixedWidth(24)
        item_layout.addWidget(icon_label)

        # テキスト部分
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(notification.title)
        title_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        title_label.setWordWrap(True)
        text_layout.addWidget(title_label)

        message_label = QLabel(notification.message)
        message_label.setStyleSheet(f"font-size: 11px; color: {text_muted};")
        message_label.setWordWrap(True)
        text_layout.addWidget(message_label)

        time_label = QLabel(notification.created_at.strftime("%m/%d %H:%M"))
        time_label.setStyleSheet(f"font-size: 10px; color: {text_muted};")
        text_layout.addWidget(time_label)

        item_layout.addLayout(text_layout, 1)

        # 未読インジケータ
        if not notification.is_read:
            dot = QLabel("\u25cf")
            dot.setStyleSheet(f"font-size: 10px; color: {accent};")
            dot.setFixedWidth(12)
            item_layout.addWidget(dot)

        return item

    def _on_item_clicked(self, notification: Notification) -> None:
        """個別通知クリック時のハンドラ.

        Args:
            notification: クリックされた通知.
        """
        if not notification.is_read:
            self._notification_service.mark_as_read(notification.id)
        self._show_detail_dialog(notification)
        self._rebuild_list()

    def _show_detail_dialog(self, notification: Notification) -> None:
        """通知詳細ダイアログを表示する.

        Args:
            notification: 表示する通知.
        """
        from study_python.gui.dialogs.notification_detail_dialog import (  # noqa: PLC0415
            NotificationDetailDialog,
        )

        dialog = NotificationDetailDialog(
            notification, self._theme_manager, parent=self
        )
        dialog.exec()

    def _on_mark_all_read(self) -> None:
        """全て既読ボタンのハンドラ."""
        self._notification_service.mark_all_as_read()
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        """通知リストを再構築する."""
        for item in self._notification_items:
            self._list_layout.removeWidget(item)
            item.deleteLater()
        self._notification_items.clear()
        self._populate_list()
