"""Task（ガントチャートタスク）のリポジトリ."""

from __future__ import annotations

import logging

from study_python.models.task import Task
from study_python.repositories.json_storage import JsonStorage


logger = logging.getLogger(__name__)


class TaskRepository:
    """TaskのCRUD操作を提供するリポジトリ.

    Attributes:
        storage: JSON永続化ストレージ.
    """

    def __init__(self, storage: JsonStorage) -> None:
        """TaskRepositoryを初期化する.

        Args:
            storage: JSON永続化ストレージ.
        """
        self.storage = storage

    def get_all(self) -> list[Task]:
        """全Taskを取得する.

        Returns:
            Taskのリスト.
        """
        data = self.storage.load()
        return [Task.from_dict(d) for d in data]

    def get_by_goal_id(self, goal_id: str) -> list[Task]:
        """Goal IDでTaskをフィルタ取得する.

        Args:
            goal_id: フィルタするGoalのID.

        Returns:
            該当するTaskのリスト（order順）.
        """
        tasks = self.get_all()
        filtered = [t for t in tasks if t.goal_id == goal_id]
        return sorted(filtered, key=lambda t: t.order)

    def get_by_book_id(self, book_id: str) -> list[Task]:
        """Book IDでTaskをフィルタ取得する.

        Args:
            book_id: フィルタするBookのID.

        Returns:
            該当するTaskのリスト（order順）.
        """
        tasks = self.get_all()
        filtered = [t for t in tasks if t.book_id == book_id]
        return sorted(filtered, key=lambda t: t.order)

    def get_by_id(self, task_id: str) -> Task | None:
        """IDでTaskを取得する.

        Args:
            task_id: 取得するTaskのID.

        Returns:
            該当するTask。見つからない場合はNone.
        """
        tasks = self.get_all()
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    def add(self, task: Task) -> None:
        """Taskを追加する.

        Args:
            task: 追加するTask.
        """
        data = self.storage.load()
        data.append(task.to_dict())
        self.storage.save(data)
        logger.info(f"Added task: {task.id} - {task.title}")

    def update(self, task: Task) -> bool:
        """Taskを更新する.

        Args:
            task: 更新するTask.

        Returns:
            更新に成功した場合True.
        """
        data = self.storage.load()
        for i, d in enumerate(data):
            if d["id"] == task.id:
                data[i] = task.to_dict()
                self.storage.save(data)
                logger.info(f"Updated task: {task.id}")
                return True
        logger.warning(f"Task not found for update: {task.id}")
        return False

    def delete(self, task_id: str) -> bool:
        """Taskを削除する.

        Args:
            task_id: 削除するTaskのID.

        Returns:
            削除に成功した場合True.
        """
        data = self.storage.load()
        original_len = len(data)
        data = [d for d in data if d["id"] != task_id]
        if len(data) < original_len:
            self.storage.save(data)
            logger.info(f"Deleted task: {task_id}")
            return True
        logger.warning(f"Task not found for delete: {task_id}")
        return False

    def delete_by_goal_id(self, goal_id: str) -> int:
        """Goal IDに紐づくTaskを全削除する.

        Args:
            goal_id: 削除対象のGoal ID.

        Returns:
            削除した件数.
        """
        data = self.storage.load()
        original_len = len(data)
        data = [d for d in data if d.get("goal_id") != goal_id]
        deleted_count = original_len - len(data)
        if deleted_count > 0:
            self.storage.save(data)
            logger.info(f"Deleted {deleted_count} tasks for goal: {goal_id}")
        return deleted_count
