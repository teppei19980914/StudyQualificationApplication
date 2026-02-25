"""Goal（3W1H学習目標）のリポジトリ."""

from __future__ import annotations

import logging

from study_python.models.goal import Goal
from study_python.repositories.json_storage import JsonStorage


logger = logging.getLogger(__name__)


class GoalRepository:
    """GoalのCRUD操作を提供するリポジトリ.

    Attributes:
        storage: JSON永続化ストレージ.
    """

    def __init__(self, storage: JsonStorage) -> None:
        """GoalRepositoryを初期化する.

        Args:
            storage: JSON永続化ストレージ.
        """
        self.storage = storage

    def get_all(self) -> list[Goal]:
        """全Goalを取得する.

        Returns:
            Goalのリスト.
        """
        data = self.storage.load()
        return [Goal.from_dict(d) for d in data]

    def get_by_id(self, goal_id: str) -> Goal | None:
        """IDでGoalを取得する.

        Args:
            goal_id: 取得するGoalのID.

        Returns:
            該当するGoal。見つからない場合はNone.
        """
        goals = self.get_all()
        for goal in goals:
            if goal.id == goal_id:
                return goal
        return None

    def add(self, goal: Goal) -> None:
        """Goalを追加する.

        Args:
            goal: 追加するGoal.
        """
        data = self.storage.load()
        data.append(goal.to_dict())
        self.storage.save(data)
        logger.info(f"Added goal: {goal.id} - {goal.what}")

    def update(self, goal: Goal) -> bool:
        """Goalを更新する.

        Args:
            goal: 更新するGoal.

        Returns:
            更新に成功した場合True.
        """
        data = self.storage.load()
        for i, d in enumerate(data):
            if d["id"] == goal.id:
                data[i] = goal.to_dict()
                self.storage.save(data)
                logger.info(f"Updated goal: {goal.id}")
                return True
        logger.warning(f"Goal not found for update: {goal.id}")
        return False

    def delete(self, goal_id: str) -> bool:
        """Goalを削除する.

        Args:
            goal_id: 削除するGoalのID.

        Returns:
            削除に成功した場合True.
        """
        data = self.storage.load()
        original_len = len(data)
        data = [d for d in data if d["id"] != goal_id]
        if len(data) < original_len:
            self.storage.save(data)
            logger.info(f"Deleted goal: {goal_id}")
            return True
        logger.warning(f"Goal not found for delete: {goal_id}")
        return False
