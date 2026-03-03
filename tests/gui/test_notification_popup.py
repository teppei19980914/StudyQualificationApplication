"""NotificationPopupのテスト."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.notification_popup import (
    NotificationPopup,
    _ClickableFrame,
)
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

    def test_click_notification_marks_as_read(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """個別の通知をクリックすると既読になる."""
        notification = Notification(
            notification_type=NotificationType.ACHIEVEMENT,
            title="累計5時間達成！",
            message="テストメッセージ",
        )
        notification_service._repo.add(notification)
        assert notification_service.get_unread_count() == 1

        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)

        with patch.object(popup, "_show_detail_dialog"):
            popup._on_item_clicked(notification)
        assert notification_service.get_unread_count() == 0

    def test_click_notification_rebuilds_list(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """個別クリック後にリストが再構築される."""
        n1 = Notification(
            notification_type=NotificationType.ACHIEVEMENT,
            title="通知1",
            message="msg1",
        )
        n2 = Notification(
            notification_type=NotificationType.ACHIEVEMENT,
            title="通知2",
            message="msg2",
        )
        notification_service._repo.add(n1)
        notification_service._repo.add(n2)

        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)

        # n1をクリックして既読にする
        with patch.object(popup, "_show_detail_dialog"):
            popup._on_item_clicked(n1)

        # n1は既読、n2は未読
        all_notifications = notification_service.get_all_notifications()
        read_ids = {n.id for n in all_notifications if n.is_read}
        assert n1.id in read_ids
        assert n2.id not in read_ids

    def test_notification_item_has_cursor(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """通知アイテムにポインティングハンドカーソルが設定される."""
        notification_service._repo.add(
            Notification(
                notification_type=NotificationType.ACHIEVEMENT,
                title="テスト",
                message="msg",
            )
        )
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)

        frames = popup.findChildren(_ClickableFrame, "notification_item")
        assert len(frames) == 1
        assert frames[0].cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_notification_item_has_notification_id_property(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """通知アイテムにnotification_idプロパティが設定される."""
        notification = Notification(
            notification_type=NotificationType.SYSTEM,
            title="テスト",
            message="msg",
        )
        notification_service._repo.add(notification)
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)

        frames = popup.findChildren(_ClickableFrame, "notification_item")
        assert len(frames) == 1
        assert frames[0].property("notification_id") == notification.id

    def test_click_notification_opens_detail_dialog(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """個別通知クリック時に詳細ダイアログが開かれる."""
        notification = Notification(
            notification_type=NotificationType.ACHIEVEMENT,
            title="テスト通知",
            message="テストメッセージ",
        )
        notification_service._repo.add(notification)
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)

        with patch.object(popup, "_show_detail_dialog") as mock_show:
            popup._on_item_clicked(notification)
            mock_show.assert_called_once_with(notification)

    def test_click_read_notification_opens_detail_dialog(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """既読通知クリック時にも詳細ダイアログが開かれる."""
        notification = Notification(
            notification_type=NotificationType.SYSTEM,
            title="既読通知",
            message="msg",
            is_read=True,
        )
        notification_service._repo.add(notification)
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)

        with patch.object(popup, "_show_detail_dialog") as mock_show:
            popup._on_item_clicked(notification)
            mock_show.assert_called_once_with(notification)

    def test_click_read_notification_does_not_call_mark_as_read(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """既読通知クリック時にmark_as_readは呼ばれない."""
        notification = Notification(
            notification_type=NotificationType.SYSTEM,
            title="テスト",
            message="msg",
            is_read=True,
        )
        notification_service._repo.add(notification)
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)

        with (
            patch.object(popup, "_show_detail_dialog"),
            patch.object(notification_service, "mark_as_read") as mock_mark,
        ):
            popup._on_item_clicked(notification)
            mock_mark.assert_not_called()

    def test_read_notification_item_is_clickable(
        self,
        qtbot,
        theme_manager: ThemeManager,
        notification_service: NotificationService,
    ):
        """既読通知アイテムもクリック可能である."""
        notification = Notification(
            notification_type=NotificationType.ACHIEVEMENT,
            title="既読通知",
            message="msg",
            is_read=True,
        )
        notification_service._repo.add(notification)
        popup = NotificationPopup(notification_service, theme_manager)
        qtbot.addWidget(popup)

        frames = popup.findChildren(_ClickableFrame, "notification_item")
        assert len(frames) == 1
        assert frames[0].cursor().shape() == Qt.CursorShape.PointingHandCursor


class TestClickableFrame:
    """_ClickableFrameのテスト."""

    def test_clicked_signal_emitted(self, qtbot):
        """クリック時にclickedシグナルが発火する."""
        frame = _ClickableFrame()
        qtbot.addWidget(frame)
        with qtbot.waitSignal(frame.clicked, timeout=1000):
            qtbot.mouseClick(frame, Qt.MouseButton.LeftButton)
