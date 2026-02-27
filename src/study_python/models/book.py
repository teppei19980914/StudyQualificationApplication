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
        start_date: 読書開始予定日（ガントチャート用）.
        end_date: 読書終了予定日（ガントチャート用）.
        progress: 読書進捗率（0-100）.
        created_at: 作成日時.
        updated_at: 更新日時.
    """

    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: BookStatus = BookStatus.UNREAD
    summary: str = ""
    impressions: str = ""
    completed_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    progress: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """バリデーションを実行する.

        Raises:
            ValueError: タイトルが空、進捗率が範囲外、終了日が開始日より前の場合.
        """
        if not self.title.strip():
            msg = "書籍名は必須です"
            raise ValueError(msg)
        if not 0 <= self.progress <= 100:
            msg = f"進捗率は0-100の範囲で指定してください: {self.progress}"
            raise ValueError(msg)
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            msg = "終了日は開始日以降に設定してください"
            raise ValueError(msg)

    @property
    def has_schedule(self) -> bool:
        """スケジュールが設定されているかどうかを返す.

        Returns:
            start_dateとend_dateが両方設定されている場合True.
        """
        return self.start_date is not None and self.end_date is not None

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
            "start_date": (self.start_date.isoformat() if self.start_date else None),
            "end_date": (self.end_date.isoformat() if self.end_date else None),
            "progress": self.progress,
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
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")
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
            start_date=(
                date.fromisoformat(str(start_date_str)) if start_date_str else None
            ),
            end_date=(date.fromisoformat(str(end_date_str)) if end_date_str else None),
            progress=int(data.get("progress", 0)),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            updated_at=datetime.fromisoformat(str(data["updated_at"])),
        )
