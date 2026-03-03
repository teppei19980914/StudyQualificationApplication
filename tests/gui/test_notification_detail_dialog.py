"""NotificationDetailDialogのテスト."""

from datetime import datetime
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from study_python.gui.dialogs.notification_detail_dialog import (
    NotificationDetailDialog,
)
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.notification import Notification, NotificationType


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


@pytest.fixture
def system_notification() -> Notification:
    return Notification(
        notification_type=NotificationType.SYSTEM,
        title="システムメンテナンスのお知らせ",
        message="2026年3月10日にメンテナンスを実施します。",
        created_at=datetime(2026, 3, 3, 10, 30),
    )


@pytest.fixture
def achievement_notification() -> Notification:
    return Notification(
        notification_type=NotificationType.ACHIEVEMENT,
        title="累計10時間達成！",
        message="累計学習時間が10時間に到達しました！",
        is_read=True,
        created_at=datetime(2026, 2, 27, 21, 7),
    )


class TestNotificationDetailDialog:
    """NotificationDetailDialogのテスト."""

    def test_create_dialog(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """ダイアログが正常に生成される."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert dialog is not None

    def test_window_title(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """ウィンドウタイトルが正しい."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "通知詳細"

    def test_shows_notification_title(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """通知タイトルが表示される."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert dialog._title_label.text() == "システムメンテナンスのお知らせ"

    def test_shows_notification_message(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """通知メッセージが表示される."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert dialog._message_label.text() == "2026年3月10日にメンテナンスを実施します。"

    def test_shows_system_type_label(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """システム通知の種別ラベルが表示される."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert dialog._type_label.text() == "システム通知"

    def test_shows_achievement_type_label(
        self,
        qtbot,
        theme_manager: ThemeManager,
        achievement_notification: Notification,
    ):
        """実績達成の種別ラベルが表示される."""
        dialog = NotificationDetailDialog(achievement_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert dialog._type_label.text() == "実績達成"

    def test_shows_system_icon(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """システム通知に📢アイコンが表示される."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert "\U0001f4e2" in dialog._icon_label.text()

    def test_shows_achievement_icon(
        self,
        qtbot,
        theme_manager: ThemeManager,
        achievement_notification: Notification,
    ):
        """実績達成に✨アイコンが表示される."""
        dialog = NotificationDetailDialog(achievement_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert "\u2728" in dialog._icon_label.text()

    def test_shows_created_time(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """作成日時が表示される."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert dialog._time_label.text() == "2026/03/03 10:30"

    def test_shows_unread_status(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """未読状態が表示される."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert dialog._status_label.text() == "未読"

    def test_shows_read_status(
        self,
        qtbot,
        theme_manager: ThemeManager,
        achievement_notification: Notification,
    ):
        """既読状態が表示される."""
        dialog = NotificationDetailDialog(achievement_notification, theme_manager)
        qtbot.addWidget(dialog)
        assert dialog._status_label.text() == "既読"

    def test_close_button_exists(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """閉じるボタンが存在する."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        buttons = dialog.findChildren(QPushButton, "close_button")
        assert len(buttons) == 1
        assert buttons[0].text() == "閉じる"

    def test_message_is_selectable(
        self,
        qtbot,
        theme_manager: ThemeManager,
        system_notification: Notification,
    ):
        """メッセージテキストが選択可能である."""
        dialog = NotificationDetailDialog(system_notification, theme_manager)
        qtbot.addWidget(dialog)
        flags = dialog._message_label.textInteractionFlags()
        assert flags & Qt.TextInteractionFlag.TextSelectableByMouse
