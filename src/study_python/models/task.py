"""ガントチャートタスクのデータモデル."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class TaskStatus(Enum):
    """タスクのステータス."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


BOOK_GANTT_GOAL_ID = "__books__"


@dataclass
class Task:
    """ガントチャートタスクモデル.

    Attributes:
        id: 一意識別子.
        goal_id: 紐づくGoalのID.
        title: タスク名.
        start_date: 開始日.
        end_date: 終了日.
        status: ステータス.
        progress: 進捗率（0-100）.
        memo: メモ.
        order: 表示順序.
        created_at: 作成日時.
        updated_at: 更新日時.
    """

    goal_id: str
    title: str
    start_date: date
    end_date: date
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.NOT_STARTED
    progress: int = 0
    memo: str = ""
    book_id: str = ""
    order: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """バリデーションを実行する.

        Raises:
            ValueError: 進捗率が範囲外、または終了日が開始日より前の場合.
        """
        if not 0 <= self.progress <= 100:
            msg = f"進捗率は0-100の範囲で指定してください: {self.progress}"
            raise ValueError(msg)
        if self.end_date < self.start_date:
            msg = f"終了日は開始日以降に設定してください: {self.start_date} > {self.end_date}"
            raise ValueError(msg)

    @property
    def duration_days(self) -> int:
        """タスクの日数を返す.

        Returns:
            開始日から終了日までの日数（両端含む）.
        """
        return (self.end_date - self.start_date).days + 1

    def to_dict(self) -> dict[str, str | int]:
        """辞書に変換する（JSON保存用）.

        Returns:
            モデルの辞書表現.
        """
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "title": self.title,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status.value,
            "progress": self.progress,
            "memo": self.memo,
            "book_id": self.book_id,
            "order": self.order,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int]) -> Task:
        """辞書からTaskを生成する.

        Args:
            data: JSON由来の辞書データ.

        Returns:
            Taskインスタンス.
        """
        return cls(
            id=str(data["id"]),
            goal_id=str(data["goal_id"]),
            title=str(data["title"]),
            start_date=date.fromisoformat(str(data["start_date"])),
            end_date=date.fromisoformat(str(data["end_date"])),
            status=TaskStatus(str(data["status"])),
            progress=int(data["progress"]),
            memo=str(data.get("memo", "")),
            book_id=str(data.get("book_id", "")),
            order=int(data.get("order", 0)),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            updated_at=datetime.fromisoformat(str(data["updated_at"])),
        )
