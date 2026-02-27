"""NotificationRepositoryのテスト."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from study_python.models.notification import Notification, NotificationType
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.notification_repository import NotificationRepository


@pytest.fixture
def repo(tmp_path: Path) -> NotificationRepository:
    """テスト用リポジトリ."""
    storage = JsonStorage(tmp_path / "notifications.json")
    return NotificationRepository(storage)


def _make_notification(
    *,
    title: str = "テスト",
    notification_type: NotificationType = NotificationType.ACHIEVEMENT,
    is_read: bool = False,
    dedup_key: str = "",
    created_at: datetime | None = None,
) -> Notification:
    return Notification(
        notification_type=notification_type,
        title=title,
        message=f"{title}のメッセージ",
        is_read=is_read,
        dedup_key=dedup_key,
        created_at=created_at or datetime.now(),
    )


class TestNotificationRepository:
    """NotificationRepositoryのテスト."""

    def test_get_all_empty(self, repo: NotificationRepository):
        assert repo.get_all() == []

    def test_add_and_get_all(self, repo: NotificationRepository):
        n = _make_notification(title="累計10時間達成！")
        repo.add(n)
        result = repo.get_all()
        assert len(result) == 1
        assert result[0].title == "累計10時間達成！"

    def test_get_all_sorted_desc(self, repo: NotificationRepository):
        now = datetime.now()
        n1 = _make_notification(title="古い", created_at=now - timedelta(hours=2))
        n2 = _make_notification(title="新しい", created_at=now)
        repo.add(n1)
        repo.add(n2)
        result = repo.get_all()
        assert result[0].title == "新しい"
        assert result[1].title == "古い"

    def test_get_by_id_found(self, repo: NotificationRepository):
        n = _make_notification(title="テスト通知")
        repo.add(n)
        result = repo.get_by_id(n.id)
        assert result is not None
        assert result.title == "テスト通知"

    def test_get_by_id_not_found(self, repo: NotificationRepository):
        assert repo.get_by_id("nonexistent") is None

    def test_get_unread(self, repo: NotificationRepository):
        n1 = _make_notification(title="未読", is_read=False)
        n2 = _make_notification(title="既読", is_read=True)
        repo.add(n1)
        repo.add(n2)
        result = repo.get_unread()
        assert len(result) == 1
        assert result[0].title == "未読"

    def test_get_unread_count(self, repo: NotificationRepository):
        n1 = _make_notification(is_read=False)
        n2 = _make_notification(is_read=False)
        n3 = _make_notification(is_read=True)
        repo.add(n1)
        repo.add(n2)
        repo.add(n3)
        assert repo.get_unread_count() == 2

    def test_get_unread_count_empty(self, repo: NotificationRepository):
        assert repo.get_unread_count() == 0

    def test_exists_by_dedup_key_true(self, repo: NotificationRepository):
        n = _make_notification(dedup_key="total_hours:10")
        repo.add(n)
        assert repo.exists_by_dedup_key("total_hours:10") is True

    def test_exists_by_dedup_key_false(self, repo: NotificationRepository):
        assert repo.exists_by_dedup_key("total_hours:999") is False

    def test_mark_as_read(self, repo: NotificationRepository):
        n = _make_notification(is_read=False)
        repo.add(n)
        assert repo.mark_as_read(n.id) is True
        result = repo.get_by_id(n.id)
        assert result is not None
        assert result.is_read is True

    def test_mark_as_read_not_found(self, repo: NotificationRepository):
        assert repo.mark_as_read("nonexistent") is False

    def test_mark_all_as_read(self, repo: NotificationRepository):
        n1 = _make_notification(is_read=False)
        n2 = _make_notification(is_read=False)
        n3 = _make_notification(is_read=True)
        repo.add(n1)
        repo.add(n2)
        repo.add(n3)
        count = repo.mark_all_as_read()
        assert count == 2
        assert repo.get_unread_count() == 0

    def test_mark_all_as_read_none_unread(self, repo: NotificationRepository):
        n = _make_notification(is_read=True)
        repo.add(n)
        assert repo.mark_all_as_read() == 0

    def test_delete(self, repo: NotificationRepository):
        n = _make_notification()
        repo.add(n)
        assert repo.delete(n.id) is True
        assert repo.get_all() == []

    def test_delete_not_found(self, repo: NotificationRepository):
        assert repo.delete("nonexistent") is False
