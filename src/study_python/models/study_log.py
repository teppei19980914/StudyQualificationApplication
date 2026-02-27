"""学習ログのデータモデル."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class StudyLog:
    """学習ログモデル.

    タスクごとの学習記録を表す。

    Attributes:
        task_id: 紐づくTaskのID.
        study_date: 学習実施日.
        duration_minutes: 学習時間（分単位）.
        id: 一意識別子.
        memo: メモ.
        task_name: タスク名（記録時に保存、削除後も表示用）.
        created_at: 作成日時.
    """

    task_id: str
    study_date: date
    duration_minutes: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memo: str = ""
    task_name: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """バリデーションを実行する.

        Raises:
            ValueError: 学習時間が0以下の場合.
        """
        if self.duration_minutes <= 0:
            msg = f"学習時間は1分以上で指定してください: {self.duration_minutes}"
            raise ValueError(msg)

    @property
    def duration_hours(self) -> float:
        """学習時間を時間単位で返す.

        Returns:
            学習時間（時間）.
        """
        return self.duration_minutes / 60.0

    def to_dict(self) -> dict[str, str | int]:
        """辞書に変換する（JSON保存用）.

        Returns:
            モデルの辞書表現.
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "study_date": self.study_date.isoformat(),
            "duration_minutes": self.duration_minutes,
            "memo": self.memo,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int]) -> StudyLog:
        """辞書からStudyLogを生成する.

        Args:
            data: JSON由来の辞書データ.

        Returns:
            StudyLogインスタンス.
        """
        return cls(
            id=str(data["id"]),
            task_id=str(data["task_id"]),
            study_date=date.fromisoformat(str(data["study_date"])),
            duration_minutes=int(data["duration_minutes"]),
            memo=str(data.get("memo", "")),
            task_name=str(data.get("task_name", "")),
            created_at=datetime.fromisoformat(str(data["created_at"])),
        )
