"""ガントチャートタスクのビジネスロジック."""

from __future__ import annotations

import logging
from datetime import date, datetime

from study_python.models.task import Task, TaskStatus
from study_python.repositories.task_repository import TaskRepository


logger = logging.getLogger(__name__)


class TaskService:
    """Taskのビジネスロジックを提供するサービス.

    Attributes:
        task_repo: Taskリポジトリ.
    """

    def __init__(self, task_repo: TaskRepository) -> None:
        """TaskServiceを初期化する.

        Args:
            task_repo: Taskリポジトリ.
        """
        self.task_repo = task_repo

    def get_tasks_for_goal(self, goal_id: str) -> list[Task]:
        """Goal IDに紐づくTaskを取得する.

        Args:
            goal_id: GoalのID.

        Returns:
            Taskのリスト（order順）.
        """
        return self.task_repo.get_by_goal_id(goal_id)

    def get_all_tasks(self) -> list[Task]:
        """全Taskを取得する.

        Returns:
            Taskのリスト.
        """
        return self.task_repo.get_all()

    def create_task(
        self,
        goal_id: str,
        title: str,
        start_date: date,
        end_date: date,
        memo: str = "",
    ) -> Task:
        """新しいTaskを作成する.

        Args:
            goal_id: 紐づくGoalのID.
            title: タスク名.
            start_date: 開始日.
            end_date: 終了日.
            memo: メモ.

        Returns:
            作成されたTask.

        Raises:
            ValueError: タイトルが空の場合、または日付が不正な場合.
        """
        if not title.strip():
            msg = "タスク名は必須です"
            raise ValueError(msg)
        existing_tasks = self.task_repo.get_by_goal_id(goal_id)
        order = len(existing_tasks)
        task = Task(
            goal_id=goal_id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            memo=memo,
            order=order,
        )
        self.task_repo.add(task)
        logger.info(f"Created task: {task.title} for goal {goal_id}")
        return task

    def update_task(
        self,
        task_id: str,
        title: str,
        start_date: date,
        end_date: date,
        status: TaskStatus,
        progress: int,
        memo: str = "",
    ) -> Task | None:
        """Taskを更新する.

        Args:
            task_id: 更新対象のTask ID.
            title: タスク名.
            start_date: 開始日.
            end_date: 終了日.
            status: ステータス.
            progress: 進捗率（0-100）.
            memo: メモ.

        Returns:
            更新されたTask。見つからない場合はNone.

        Raises:
            ValueError: タイトルが空、進捗率が範囲外、または日付が不正な場合.
        """
        if not title.strip():
            msg = "タスク名は必須です"
            raise ValueError(msg)
        if not 0 <= progress <= 100:
            msg = f"進捗率は0-100の範囲で指定してください: {progress}"
            raise ValueError(msg)
        if end_date < start_date:
            msg = "終了日は開始日以降に設定してください"
            raise ValueError(msg)
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            return None
        task.title = title
        task.start_date = start_date
        task.end_date = end_date
        task.status = status
        task.progress = progress
        task.memo = memo
        task.updated_at = datetime.now()
        self.task_repo.update(task)
        logger.info(f"Updated task: {task.title}")
        return task

    def delete_task(self, task_id: str) -> bool:
        """Taskを削除する.

        Args:
            task_id: 削除対象のTask ID.

        Returns:
            削除に成功した場合True.
        """
        return self.task_repo.delete(task_id)

    def update_progress(self, task_id: str, progress: int) -> Task | None:
        """タスクの進捗率を更新する.

        進捗率に応じてステータスも自動更新する:
        - 0%: 未着手
        - 1-99%: 進行中
        - 100%: 完了

        Args:
            task_id: Task ID.
            progress: 進捗率（0-100）.

        Returns:
            更新されたTask。見つからない場合はNone.

        Raises:
            ValueError: 進捗率が範囲外の場合.
        """
        if not 0 <= progress <= 100:
            msg = f"進捗率は0-100の範囲で指定してください: {progress}"
            raise ValueError(msg)
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            return None
        task.progress = progress
        if progress == 0:
            task.status = TaskStatus.NOT_STARTED
        elif progress == 100:
            task.status = TaskStatus.COMPLETED
        else:
            task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now()
        self.task_repo.update(task)
        logger.info(f"Updated progress for {task.title}: {progress}%")
        return task
