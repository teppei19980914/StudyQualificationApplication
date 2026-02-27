"""Notificationモデルのテスト."""

from datetime import datetime

from study_python.models.notification import Notification, NotificationType


class TestNotificationType:
    """NotificationTypeのテスト."""

    def test_system_value(self):
        assert NotificationType.SYSTEM.value == "system"

    def test_achievement_value(self):
        assert NotificationType.ACHIEVEMENT.value == "achievement"

    def test_from_string(self):
        assert NotificationType("system") == NotificationType.SYSTEM
        assert NotificationType("achievement") == NotificationType.ACHIEVEMENT


class TestNotification:
    """Notificationのテスト."""

    def test_create_notification(self):
        n = Notification(
            notification_type=NotificationType.ACHIEVEMENT,
            title="累計10時間達成！",
            message="累計学習時間が10時間に到達しました！",
            dedup_key="total_hours:10",
        )
        assert n.notification_type == NotificationType.ACHIEVEMENT
        assert n.title == "累計10時間達成！"
        assert n.message == "累計学習時間が10時間に到達しました！"
        assert n.dedup_key == "total_hours:10"

    def test_default_values(self):
        n = Notification(
            notification_type=NotificationType.SYSTEM,
            title="テスト",
            message="テストメッセージ",
        )
        assert len(n.id) > 0
        assert n.is_read is False
        assert n.dedup_key == ""
        assert isinstance(n.created_at, datetime)

    def test_to_dict(self):
        dt = datetime(2026, 2, 27, 10, 30, 0)
        n = Notification(
            id="test-id",
            notification_type=NotificationType.ACHIEVEMENT,
            title="累計10時間達成！",
            message="テストメッセージ",
            is_read=True,
            created_at=dt,
            dedup_key="total_hours:10",
        )
        d = n.to_dict()
        assert d["id"] == "test-id"
        assert d["notification_type"] == "achievement"
        assert d["title"] == "累計10時間達成！"
        assert d["message"] == "テストメッセージ"
        assert d["is_read"] is True
        assert d["created_at"] == "2026-02-27T10:30:00"
        assert d["dedup_key"] == "total_hours:10"

    def test_from_dict(self):
        d = {
            "id": "test-id",
            "notification_type": "system",
            "title": "お知らせ",
            "message": "バージョン1.0リリース",
            "is_read": False,
            "created_at": "2026-02-27T10:30:00",
            "dedup_key": "system:v1.0",
        }
        n = Notification.from_dict(d)
        assert n.id == "test-id"
        assert n.notification_type == NotificationType.SYSTEM
        assert n.title == "お知らせ"
        assert n.message == "バージョン1.0リリース"
        assert n.is_read is False
        assert n.created_at == datetime(2026, 2, 27, 10, 30, 0)
        assert n.dedup_key == "system:v1.0"

    def test_from_dict_missing_optional(self):
        d = {
            "id": "test-id",
            "notification_type": "achievement",
            "title": "テスト",
            "message": "メッセージ",
            "created_at": "2026-02-27T10:30:00",
        }
        n = Notification.from_dict(d)
        assert n.is_read is False
        assert n.dedup_key == ""

    def test_roundtrip(self):
        original = Notification(
            notification_type=NotificationType.ACHIEVEMENT,
            title="学習7日達成！",
            message="学習日数が7日に到達しました！",
            dedup_key="study_days:7",
        )
        restored = Notification.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.notification_type == original.notification_type
        assert restored.title == original.title
        assert restored.message == original.message
        assert restored.is_read == original.is_read
        assert restored.dedup_key == original.dedup_key
