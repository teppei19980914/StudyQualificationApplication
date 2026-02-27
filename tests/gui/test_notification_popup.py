"""NotificationPopupのテスト."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QLabel, QPushButton

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.notification_popup import NotificationPopup
from study_python.models.notification import Notification, NotificationType
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.notification_repository import NotificationRepository
from study_python.services.notification_service import NotificationService


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


@pytest.fixture
def notification_service(tmp_path: Path) -> NotificationService:
    storage = JsonStorage(tmp_path / "notifications.json")
    repo = NotificationRepository(storage)
    return NotificationService(repo)


class TestNotificationPopup:
    """NotificationPopupのテスト."""

    def test_create_popup(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)
        assert popup is not None

    def test_window_title(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)
        assert popup.windowTitle() == "通知"

    def test_shows_empty_message(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """通知がない場合は空メッセージが表示される."""
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)
        empty_labels = popup.findChildren(QLabel, "empty_notification_label")
        assert len(empty_labels) == 1
        assert "通知はありません" in empty_labels[0].text()

    def test_shows_notifications(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """通知がある場合はアイテムが表示される."""
        notification_service._repo.add(
            Notification(
                notification_type=NotificationType.ACHIEVEMENT,
                title="累計10時間達成！",
                message="テストメッセージ",
            )
        )
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)

        # 空メッセージは表示されない
        empty_labels = popup.findChildren(QLabel, "empty_notification_label")
        assert len(empty_labels) == 0

        # 通知アイテムがある
        assert len(popup._notification_items) == 1

    def test_shows_multiple_notifications(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """複数の通知が表示される."""
        for i in range(3):
            notification_service._repo.add(
                Notification(
                    notification_type=NotificationType.ACHIEVEMENT,
                    title=f"通知{i}",
                    message=f"メッセージ{i}",
                )
            )
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)
        assert len(popup._notification_items) == 3

    def test_mark_all_read_button_exists(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """全て既読ボタンが存在する."""
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)
        buttons = popup.findChildren(QPushButton, "mark_all_read_button")
        assert len(buttons) == 1
        assert buttons[0].text() == "全て既読"

    def test_mark_all_read(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """全て既読ボタンで全通知が既読になる."""
        notification_service._repo.add(
            Notification(
                notification_type=NotificationType.SYSTEM,
                title="テスト",
                message="msg",
            )
        )
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)
        popup._on_mark_all_read()
        assert notification_service.get_unread_count() == 0

    def test_system_notification_icon(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """システム通知に📢アイコンが表示される."""
        notification_service._repo.add(
            Notification(
                notification_type=NotificationType.SYSTEM,
                title="お知らせ",
                message="テスト",
            )
        )
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)
        labels = popup.findChildren(QLabel)
        texts = [label.text() for label in labels]
        assert any("\U0001f4e2" in text for text in texts)

    def test_achievement_notification_icon(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """実績通知に✨アイコンが表示される."""
        notification_service._repo.add(
            Notification(
                notification_type=NotificationType.ACHIEVEMENT,
                title="達成",
                message="テスト",
            )
        )
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)
        labels = popup.findChildren(QLabel)
        texts = [label.text() for label in labels]
        assert any("\u2728" in text for text in texts)
