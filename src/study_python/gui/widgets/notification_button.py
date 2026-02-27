"""通知ベルアイコンボタンウィジェット."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.notification_popup import NotificationPopup
from study_python.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


class NotificationButton(QPushButton):
    """通知ベルアイコンボタン.

    ベルアイコンと未読バッジを表示する。クリックでNotificationPopupを開く。

    Attributes:
        _theme_manager: テーママネージャ.
        _notification_service: 通知サービス.
        _badge_label: 未読バッジラベル.
        _unread_count: 未読通知数.
    """

    def __init__(
        self,
        theme_manager: ThemeManager,
        notification_service: NotificationService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """NotificationButtonを初期化する.

        Args:
            theme_manager: テーママネージャ.
            notification_service: 通知サービス.
            parent: 親ウィジェット.
        """
        super().__init__("\U0001f514 通知", parent)
        self._theme_manager = theme_manager
        self._notification_service = notification_service
        self._unread_count = 0
        self.setObjectName("secondary_button")
        self.setFixedHeight(36)
        self.setToolTip("通知")
        self.clicked.connect(self._on_clicked)
        self._setup_badge()

    def _setup_badge(self) -> None:
        """未読バッジを構築する."""
        self._badge_label = QLabel(self)
        self._badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge_label.setFixedSize(18, 18)
        self._badge_label.setVisible(False)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """リサイズ時にバッジ位置を更新する.

        Args:
            event: リサイズイベント.
        """
        super().resizeEvent(event)
        self._position_badge()

    def _position_badge(self) -> None:
        """バッジをボタン右上に配置する."""
        x = self.width() - 20
        y = 2
        self._badge_label.move(x, y)

    def update_badge(self, count: int) -> None:
        """未読バッジを更新する.

        Args:
            count: 未読通知数.
        """
        self._unread_count = count
        if count > 0:
            display = str(count) if count <= 99 else "99+"
            self._badge_label.setText(display)
            self._badge_label.setVisible(True)
            self._update_badge_style()
        else:
            self._badge_label.setVisible(False)
        logger.debug(f"Notification badge updated: {count}")

    def _update_badge_style(self) -> None:
        """バッジのスタイルを更新する."""
        colors = self._theme_manager.get_colors()
        error_color = colors.get("error", "#F38BA8")
        self._badge_label.setStyleSheet(
            f"QLabel {{"
            f"  background-color: {error_color};"
            f"  color: white;"
            f"  font-size: 10px;"
            f"  font-weight: bold;"
            f"  border-radius: 9px;"
            f"  min-width: 18px;"
            f"  min-height: 18px;"
            f"}}"
        )

    def _on_clicked(self) -> None:  # pragma: no cover
        """ベルボタンクリック時にポップアップを表示する."""
        if self._notification_service is None:
            return
        popup = NotificationPopup(
            self._notification_service,
            self._theme_manager,
            parent=self,
        )
        popup.exec()
        # ポップアップ閉じた後にバッジを再取得
        new_count = self._notification_service.get_unread_count()
        self.update_badge(new_count)
