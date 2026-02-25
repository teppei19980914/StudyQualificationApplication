"""3W1H学習目標のビジネスロジック."""

from __future__ import annotations

import logging
from datetime import datetime

from study_python.models.goal import GOAL_COLORS, Goal, WhenType
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.task_repository import TaskRepository


logger = logging.getLogger(__name__)


class GoalService:
    """Goalのビジネスロジックを提供するサービス.

    Attributes:
        goal_repo: Goalリポジトリ.
        task_repo: Taskリポジトリ（Goal削除時のカスケード用）.
    """

    def __init__(self, goal_repo: GoalRepository, task_repo: TaskRepository) -> None:
        """GoalServiceを初期化する.

        Args:
            goal_repo: Goalリポジトリ.
            task_repo: Taskリポジトリ.
        """
        self.goal_repo = goal_repo
        self.task_repo = task_repo

    def get_all_goals(self) -> list[Goal]:
        """全Goalを取得する.

        Returns:
            Goalのリスト.
        """
        return self.goal_repo.get_all()

    def get_goal(self, goal_id: str) -> Goal | None:
        """IDでGoalを取得する.

        Args:
            goal_id: GoalのID.

        Returns:
            該当するGoal。見つからない場合はNone.
        """
        return self.goal_repo.get_by_id(goal_id)

    def create_goal(
        self,
        why: str,
        when_target: str,
        when_type: WhenType,
        what: str,
        how: str,
    ) -> Goal:
        """新しいGoalを作成する.

        Args:
            why: なぜ学習するのか.
            when_target: いつまでに.
            when_type: When指定タイプ.
            what: 何を学習するのか.
            how: どうやって学習するのか.

        Returns:
            作成されたGoal.

        Raises:
            ValueError: 必須フィールドが空の場合.
        """
        self._validate_fields(why=why, when_target=when_target, what=what, how=how)
        color = self._assign_color()
        goal = Goal(
            why=why,
            when_target=when_target,
            when_type=when_type,
            what=what,
            how=how,
            color=color,
        )
        self.goal_repo.add(goal)
        logger.info(f"Created goal: {goal.what}")
        return goal

    def update_goal(
        self,
        goal_id: str,
        why: str,
        when_target: str,
        when_type: WhenType,
        what: str,
        how: str,
    ) -> Goal | None:
        """Goalを更新する.

        Args:
            goal_id: 更新対象のGoal ID.
            why: なぜ学習するのか.
            when_target: いつまでに.
            when_type: When指定タイプ.
            what: 何を学習するのか.
            how: どうやって学習するのか.

        Returns:
            更新されたGoal。見つからない場合はNone.

        Raises:
            ValueError: 必須フィールドが空の場合.
        """
        self._validate_fields(why=why, when_target=when_target, what=what, how=how)
        goal = self.goal_repo.get_by_id(goal_id)
        if goal is None:
            return None
        goal.why = why
        goal.when_target = when_target
        goal.when_type = when_type
        goal.what = what
        goal.how = how
        goal.updated_at = datetime.now()
        self.goal_repo.update(goal)
        logger.info(f"Updated goal: {goal.what}")
        return goal

    def delete_goal(self, goal_id: str) -> bool:
        """Goalと関連Taskを削除する.

        Args:
            goal_id: 削除対象のGoal ID.

        Returns:
            削除に成功した場合True.
        """
        result = self.goal_repo.delete(goal_id)
        if result:
            deleted_tasks = self.task_repo.delete_by_goal_id(goal_id)
            logger.info(f"Deleted goal {goal_id} with {deleted_tasks} associated tasks")
        return result

    def _validate_fields(self, **fields: str) -> None:
        """フィールドのバリデーション.

        Args:
            **fields: 検証するフィールド名と値.

        Raises:
            ValueError: 空のフィールドがある場合.
        """
        for name, value in fields.items():
            if not value.strip():
                msg = f"{name}は必須です"
                raise ValueError(msg)

    def _assign_color(self) -> str:
        """使用頻度が低い色を自動割り当てする.

        Returns:
            割り当てるカラーコード.
        """
        existing_goals = self.goal_repo.get_all()
        used_colors = [g.color for g in existing_goals]
        for color in GOAL_COLORS:
            if color not in used_colors:
                return color
        return GOAL_COLORS[len(existing_goals) % len(GOAL_COLORS)]
