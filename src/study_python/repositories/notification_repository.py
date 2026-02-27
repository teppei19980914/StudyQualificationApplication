"""通知のリポジトリ."""

from __future__ import annotations

import logging

from study_python.models.notification import Notification
from study_python.repositories.json_storage import JsonStorage


logger = logging.getLogger(__name__)


class NotificationRepository:
    """NotificationのCRUD操作を提供するリポジトリ.

    Attributes:
        storage: JSON永続化ストレージ.
    """

    def __init__(self, storage: JsonStorage) -> None:
        """NotificationRepositoryを初期化する.

        Args:
            storage: JSON永続化ストレージ.
        """
        self.storage = storage

    def get_all(self) -> list[Notification]:
        """全Notificationを取得する（作成日時降順）.

        Returns:
            通知のリスト.
        """
        data = self.storage.load()
        notifications = [Notification.from_dict(d) for d in data]
        notifications.sort(key=lambda n: n.created_at, reverse=True)
        return notifications

    def get_by_id(self, notification_id: str) -> Notification | None:
        """IDでNotificationを取得する.

        Args:
            notification_id: 通知ID.

        Returns:
            Notificationインスタンス。見つからない場合はNone.
        """
        for n in self.get_all():
            if n.id == notification_id:
                return n
        return None

    def get_unread(self) -> list[Notification]:
        """未読通知を取得する.

        Returns:
            未読通知のリスト.
        """
        return [n for n in self.get_all() if not n.is_read]

    def get_unread_count(self) -> int:
        """未読通知数を返す.

        Returns:
            未読通知の件数.
        """
        data = self.storage.load()
        return sum(1 for d in data if not d.get("is_read", False))

    def exists_by_dedup_key(self, dedup_key: str) -> bool:
        """重複防止キーで存在チェックする.

        Args:
            dedup_key: 重複防止キー.

        Returns:
            存在する場合True.
        """
        data = self.storage.load()
        return any(d.get("dedup_key") == dedup_key for d in data)

    def add(self, notification: Notification) -> None:
        """Notificationを追加する.

        Args:
            notification: 追加する通知.
        """
        data = self.storage.load()
        data.append(notification.to_dict())
        self.storage.save(data)
        logger.info(f"Added notification: {notification.title}")

    def mark_as_read(self, notification_id: str) -> bool:
        """通知を既読にする.

        Args:
            notification_id: 通知ID.

        Returns:
            成功した場合True.
        """
        data = self.storage.load()
        for d in data:
            if d["id"] == notification_id:
                d["is_read"] = True
                self.storage.save(data)
                logger.debug(f"Marked notification as read: {notification_id}")
                return True
        return False

    def mark_all_as_read(self) -> int:
        """全通知を既読にする.

        Returns:
            更新した件数.
        """
        data = self.storage.load()
        count = 0
        for d in data:
            if not d.get("is_read", False):
                d["is_read"] = True
                count += 1
        if count > 0:
            self.storage.save(data)
            logger.info(f"Marked {count} notifications as read")
        return count

    def delete(self, notification_id: str) -> bool:
        """Notificationを削除する.

        Args:
            notification_id: 通知ID.

        Returns:
            削除した場合True.
        """
        data = self.storage.load()
        original_len = len(data)
        data = [d for d in data if d["id"] != notification_id]
        if len(data) < original_len:
            self.storage.save(data)
            logger.info(f"Deleted notification: {notification_id}")
            return True
        return False
