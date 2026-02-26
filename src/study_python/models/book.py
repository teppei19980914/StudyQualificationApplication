"""書籍のデータモデル."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class BookStatus(Enum):
    """書籍のステータス."""

    UNREAD = "unread"
    READING = "reading"
    COMPLETED = "completed"


@dataclass
class Book:
    """書籍モデル.

    書籍の登録・読了記録を管理する。

    Attributes:
        title: 書籍名.
        id: 一意識別子.
        status: ステータス.
        summary: 要約（読了時に記入）.
        impressions: 感想（読了時に記入）.
        completed_date: 読了日.
        created_at: 作成日時.
        updated_at: 更新日時.
    """

    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: BookStatus = BookStatus.UNREAD
    summary: str = ""
    impressions: str = ""
    completed_date: date | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """バリデーションを実行する.

        Raises:
            ValueError: タイトルが空の場合.
        """
        if not self.title.strip():
            msg = "書籍名は必須です"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, str | None]:
        """辞書に変換する（JSON保存用）.

        Returns:
            モデルの辞書表現.
        """
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "summary": self.summary,
            "impressions": self.impressions,
            "completed_date": (
                self.completed_date.isoformat() if self.completed_date else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> Book:
        """辞書からBookを生成する.

        Args:
            data: JSON由来の辞書データ.

        Returns:
            Bookインスタンス.
        """
        completed_date_str = data.get("completed_date")
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            status=BookStatus(str(data["status"])),
            summary=str(data.get("summary", "")),
            impressions=str(data.get("impressions", "")),
            completed_date=(
                date.fromisoformat(str(completed_date_str))
                if completed_date_str
                else None
            ),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            updated_at=datetime.fromisoformat(str(data["updated_at"])),
        )
