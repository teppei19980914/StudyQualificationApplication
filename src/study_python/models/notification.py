"""通知のデータモデル."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class NotificationType(Enum):
    """通知の種類.

    Attributes:
        SYSTEM: システム通知（運営からのお知らせ）.
        ACHIEVEMENT: 実績達成通知.
    """

    SYSTEM = "system"
    ACHIEVEMENT = "achievement"


@dataclass
class Notification:
    """通知モデル.

    Attributes:
        notification_type: 通知種別.
        title: 通知タイトル.
        message: 通知メッセージ.
        id: 一意識別子.
        is_read: 既読フラグ.
        created_at: 作成日時.
        dedup_key: 重複防止キー（実績通知: "total_hours:100" など）.
    """

    notification_type: NotificationType
    title: str
    message: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    dedup_key: str = ""

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換する（JSON保存用）.

        Returns:
            モデルの辞書表現.
        """
        return {
            "id": self.id,
            "notification_type": self.notification_type.value,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "dedup_key": self.dedup_key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Notification:
        """辞書からNotificationを生成する.

        Args:
            data: JSON由来の辞書データ.

        Returns:
            Notificationインスタンス.
        """
        return cls(
            id=str(data["id"]),
            notification_type=NotificationType(str(data["notification_type"])),
            title=str(data["title"]),
            message=str(data["message"]),
            is_read=bool(data.get("is_read", False)),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            dedup_key=str(data.get("dedup_key", "")),
        )
