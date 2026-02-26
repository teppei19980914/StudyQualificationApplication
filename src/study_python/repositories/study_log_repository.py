"""StudyLog（学習ログ）のリポジトリ."""

from __future__ import annotations

import logging

from study_python.models.study_log import StudyLog
from study_python.repositories.json_storage import JsonStorage


logger = logging.getLogger(__name__)


class StudyLogRepository:
    """StudyLogのCRUD操作を提供するリポジトリ.

    Attributes:
        storage: JSON永続化ストレージ.
    """

    def __init__(self, storage: JsonStorage) -> None:
        """StudyLogRepositoryを初期化する.

        Args:
            storage: JSON永続化ストレージ.
        """
        self.storage = storage

    def get_all(self) -> list[StudyLog]:
        """全StudyLogを取得する.

        Returns:
            StudyLogのリスト.
        """
        data = self.storage.load()
        return [StudyLog.from_dict(d) for d in data]

    def get_by_task_id(self, task_id: str) -> list[StudyLog]:
        """Task IDでStudyLogをフィルタ取得する.

        Args:
            task_id: フィルタするTaskのID.

        Returns:
            該当するStudyLogのリスト（日付順）.
        """
        logs = self.get_all()
        filtered = [log for log in logs if log.task_id == task_id]
        return sorted(filtered, key=lambda log: log.study_date)

    def get_by_task_ids(self, task_ids: list[str]) -> list[StudyLog]:
        """複数のTask IDでStudyLogを一括取得する.

        Args:
            task_ids: フィルタするTaskのIDリスト.

        Returns:
            該当するStudyLogのリスト（日付順）.
        """
        id_set = set(task_ids)
        logs = self.get_all()
        filtered = [log for log in logs if log.task_id in id_set]
        return sorted(filtered, key=lambda log: log.study_date)

    def add(self, study_log: StudyLog) -> None:
        """StudyLogを追加する.

        Args:
            study_log: 追加するStudyLog.
        """
        data = self.storage.load()
        data.append(study_log.to_dict())
        self.storage.save(data)
        logger.info(f"Added study log: {study_log.id} for task {study_log.task_id}")

    def delete(self, log_id: str) -> bool:
        """StudyLogを削除する.

        Args:
            log_id: 削除するStudyLogのID.

        Returns:
            削除に成功した場合True.
        """
        data = self.storage.load()
        original_len = len(data)
        data = [d for d in data if d["id"] != log_id]
        if len(data) < original_len:
            self.storage.save(data)
            logger.info(f"Deleted study log: {log_id}")
            return True
        logger.warning(f"Study log not found for delete: {log_id}")
        return False

    def delete_by_task_id(self, task_id: str) -> int:
        """Task IDに紐づくStudyLogを全削除する.

        Args:
            task_id: 削除対象のTask ID.

        Returns:
            削除した件数.
        """
        data = self.storage.load()
        original_len = len(data)
        data = [d for d in data if d.get("task_id") != task_id]
        deleted_count = original_len - len(data)
        if deleted_count > 0:
            self.storage.save(data)
            logger.info(f"Deleted {deleted_count} study logs for task: {task_id}")
        return deleted_count
