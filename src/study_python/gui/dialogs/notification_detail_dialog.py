"""通知詳細ダイアログ."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.notification import Notification, NotificationType


logger = logging.getLogger(__name__)

# 通知タイプごとのアイコン
_TYPE_ICONS: dict[NotificationType, str] = {
    NotificationType.SYSTEM: "\U0001f4e2",
    NotificationType.ACHIEVEMENT: "\u2728",
}

# 通知タイプごとのラベル
_TYPE_LABELS: dict[NotificationType, str] = {
    NotificationType.SYSTEM: "システム通知",
    NotificationType.ACHIEVEMENT: "実績達成",
}


class NotificationDetailDialog(QDialog):
    """通知詳細を表示するダイアログ.

    Attributes:
        _notification: 表示する通知.
        _theme_manager: テーママネージャ.
        _icon_label: 種別アイコンラベル.
        _title_label: タイトルラベル.
        _type_label: 種別ラベル.
        _time_label: 日時ラベル.
        _status_label: 状態ラベル.
        _message_label: メッセージラベル.
    """

    def __init__(
        self,
        notification: Notification,
        theme_manager: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        """NotificationDetailDialogを初期化する.

        Args:
            notification: 表示する通知.
            theme_manager: テーママネージャ.
            parent: 親ウィジェット.
        """
        super().__init__(parent)
        self._notification = notification
        self._theme_manager = theme_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setWindowTitle("通知詳細")
        self.setMinimumWidth(400)

        colors = self._theme_manager.get_colors()
        bg_card = colors.get("bg_card", "#2A2A3C")
        text_color = colors.get("text", "#CDD6F4")
        text_muted = colors.get("text_muted", "#6C7086")
        border = colors.get("border", "#45475A")
        accent = colors.get("accent", "#89B4FA")

        self.setStyleSheet(
            f"QDialog {{ background-color: {bg_card}; color: {text_color}; }}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        # ヘッダー（アイコンとタイトル）
        header_layout = QHBoxLayout()
        icon = _TYPE_ICONS.get(
            self._notification.notification_type, "\U0001f514"
        )
        self._icon_label = QLabel(icon)
        self._icon_label.setStyleSheet("font-size: 20px;")
        self._icon_label.setFixedWidth(28)
        header_layout.addWidget(self._icon_label)

        self._title_label = QLabel(self._notification.title)
        self._title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._title_label.setWordWrap(True)
        header_layout.addWidget(self._title_label, 1)
        layout.addLayout(header_layout)

        # 区切り線
        self._add_separator(layout, border)

        # 種別
        type_label_text = _TYPE_LABELS.get(
            self._notification.notification_type, "不明"
        )
        self._type_label = self._add_meta_row(
            layout, "種別", type_label_text, text_muted, text_color
        )

        # 日時
        time_text = self._notification.created_at.strftime("%Y/%m/%d %H:%M")
        self._time_label = self._add_meta_row(
            layout, "日時", time_text, text_muted, text_color
        )

        # 既読・未読の状態
        if self._notification.is_read:
            status_text = "既読"
            status_color = text_muted
        else:
            status_text = "未読"
            status_color = accent
        self._status_label = self._add_meta_row(
            layout, "状態", status_text, text_muted, status_color
        )

        # 区切り線
        self._add_separator(layout, border)

        # メッセージセクション
        message_header = QLabel("メッセージ")
        message_header.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {text_muted};"
        )
        layout.addWidget(message_header)

        self._message_label = QLabel(self._notification.message)
        self._message_label.setStyleSheet("font-size: 13px;")
        self._message_label.setWordWrap(True)
        self._message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self._message_label)

        layout.addStretch()

        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.setObjectName("close_button")
        close_button.setFixedHeight(32)
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {border};"
            f"  border: none;"
            f"  border-radius: 6px;"
            f"  padding: 4px 16px;"
            f"}}"
        )
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

        logger.debug(
            f"NotificationDetailDialog created: "
            f"id={self._notification.id}, "
            f"type={self._notification.notification_type.value}"
        )

    def _add_separator(self, layout: QVBoxLayout, border_color: str) -> None:
        """区切り線を追加する.

        Args:
            layout: 追加先レイアウト.
            border_color: 線の色.
        """
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {border_color};")
        layout.addWidget(separator)

    def _add_meta_row(
        self,
        layout: QVBoxLayout,
        label_text: str,
        value_text: str,
        label_color: str,
        value_color: str,
    ) -> QLabel:
        """メタ情報行を追加する.

        Args:
            layout: 追加先レイアウト.
            label_text: ラベルテキスト.
            value_text: 値テキスト.
            label_color: ラベル色.
            value_color: 値の色.

        Returns:
            値ラベル（テスト用にアクセス可能）.
        """
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"font-size: 12px; color: {label_color};")
        label.setFixedWidth(40)
        row.addWidget(label)

        value_label = QLabel(value_text)
        value_label.setStyleSheet(f"font-size: 13px; color: {value_color};")
        row.addWidget(value_label)
        row.addStretch()

        layout.addLayout(row)
        return value_label
