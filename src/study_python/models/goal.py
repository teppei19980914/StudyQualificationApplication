"""3W1H学習目標のデータモデル."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class WhenType(Enum):
    """When（いつまでに）の指定タイプ."""

    DATE = "date"
    PERIOD = "period"


# 目標に割り当てるデフォルトカラーパレット
GOAL_COLORS = [
    "#4A9EFF",  # Blue
    "#FF6B6B",  # Red
    "#51CF66",  # Green
    "#FFD43B",  # Yellow
    "#CC5DE8",  # Purple
    "#FF922B",  # Orange
    "#20C997",  # Teal
    "#F06595",  # Pink
]


@dataclass
class Goal:
    """3W1H学習目標モデル.

    Attributes:
        id: 一意識別子.
        why: なぜ学習するのか（動機・理由）.
        when_target: いつまでに（目標日付または期間の説明）.
        when_type: When指定タイプ（date or period）.
        what: 何を学習するのか.
        how: どうやって学習するのか.
        created_at: 作成日時.
        updated_at: 更新日時.
        color: 表示色（ガントチャート用）.
    """

    why: str
    when_target: str
    when_type: WhenType
    what: str
    how: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    color: str = GOAL_COLORS[0]

    def get_target_date(self) -> date | None:
        """when_typeがDATEの場合、目標日をdate型で返す.

        Returns:
            目標日。DATEタイプでない、またはパース不可の場合はNone.
        """
        if self.when_type != WhenType.DATE:
            return None
        try:
            return date.fromisoformat(self.when_target)
        except ValueError:
            return None

    def to_dict(self) -> dict[str, str]:
        """辞書に変換する（JSON保存用）.

        Returns:
            モデルの辞書表現.
        """
        return {
            "id": self.id,
            "why": self.why,
            "when_target": self.when_target,
            "when_type": self.when_type.value,
            "what": self.what,
            "how": self.how,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Goal:
        """辞書からGoalを生成する.

        Args:
            data: JSON由来の辞書データ.

        Returns:
            Goalインスタンス.
        """
        return cls(
            id=data["id"],
            why=data["why"],
            when_target=data["when_target"],
            when_type=WhenType(data["when_type"]),
            what=data["what"],
            how=data["how"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            color=data.get("color", GOAL_COLORS[0]),
        )
