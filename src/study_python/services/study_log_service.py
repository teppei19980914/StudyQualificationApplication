"""学習ログのビジネスロジック."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from study_python.models.study_log import StudyLog
from study_python.repositories.study_log_repository import StudyLogRepository


logger = logging.getLogger(__name__)


@dataclass
class TaskStudyStats:
    """タスク単位の学習統計.

    Attributes:
        task_id: タスクID.
        total_minutes: 合計学習時間（分）.
        study_days: 学習日数（ユニーク日数）.
        log_count: ログ件数.
    """

    task_id: str
    total_minutes: int
    study_days: int
    log_count: int

    @property
    def total_hours(self) -> float:
        """合計学習時間を時間単位で返す.

        Returns:
            合計学習時間（時間）.
        """
        return self.total_minutes / 60.0


@dataclass
class GoalStudyStats:
    """目標単位の学習統計.

    Attributes:
        goal_id: 目標ID.
        task_stats: タスクごとの統計リスト.
        total_minutes: 合計学習時間（分）.
        total_study_days: 全タスク横断のユニーク学習日数.
    """

    goal_id: str
    task_stats: list[TaskStudyStats]
    total_minutes: int
    total_study_days: int

    @property
    def total_hours(self) -> float:
        """合計学習時間を時間単位で返す.

        Returns:
            合計学習時間（時間）.
        """
        return self.total_minutes / 60.0


class StudyLogService:
    """学習ログのビジネスロジックを提供するサービス.

    Attributes:
        study_log_repo: StudyLogリポジトリ.
    """

    def __init__(self, study_log_repo: StudyLogRepository) -> None:
        """StudyLogServiceを初期化する.

        Args:
            study_log_repo: StudyLogリポジトリ.
        """
        self.study_log_repo = study_log_repo

    def add_study_log(
        self,
        task_id: str,
        study_date: date,
        duration_minutes: int,
        memo: str = "",
    ) -> StudyLog:
        """学習ログを追加する.

        Args:
            task_id: タスクID.
            study_date: 学習実施日.
            duration_minutes: 学習時間（分）.
            memo: メモ.

        Returns:
            作成されたStudyLog.

        Raises:
            ValueError: 学習時間が不正な場合.
        """
        study_log = StudyLog(
            task_id=task_id,
            study_date=study_date,
            duration_minutes=duration_minutes,
            memo=memo,
        )
        self.study_log_repo.add(study_log)
        logger.info(f"Added study log: {duration_minutes}min for task {task_id}")
        return study_log

    def get_logs_for_task(self, task_id: str) -> list[StudyLog]:
        """タスクの学習ログを取得する.

        Args:
            task_id: タスクID.

        Returns:
            StudyLogのリスト（日付順）.
        """
        return self.study_log_repo.get_by_task_id(task_id)

    def get_all_logs(self) -> list[StudyLog]:
        """全学習ログを取得する.

        Returns:
            StudyLogのリスト.
        """
        return self.study_log_repo.get_all()

    def delete_log(self, log_id: str) -> bool:
        """学習ログを削除する.

        Args:
            log_id: 削除するログID.

        Returns:
            削除に成功した場合True.
        """
        return self.study_log_repo.delete(log_id)

    def get_task_stats(self, task_id: str) -> TaskStudyStats:
        """タスク単位の学習統計を取得する.

        Args:
            task_id: タスクID.

        Returns:
            タスクの学習統計.
        """
        logs = self.study_log_repo.get_by_task_id(task_id)
        return self._calculate_task_stats(task_id, logs)

    def get_goal_stats(self, goal_id: str, task_ids: list[str]) -> GoalStudyStats:
        """目標単位の学習統計を取得する.

        Args:
            goal_id: 目標ID.
            task_ids: 目標に紐づくタスクIDリスト.

        Returns:
            目標の学習統計.
        """
        all_logs = self.study_log_repo.get_by_task_ids(task_ids)

        # タスクごとにグループ化
        logs_by_task: dict[str, list[StudyLog]] = {}
        for log in all_logs:
            logs_by_task.setdefault(log.task_id, []).append(log)

        task_stats = [
            self._calculate_task_stats(tid, logs_by_task.get(tid, []))
            for tid in task_ids
        ]

        total_minutes = sum(ts.total_minutes for ts in task_stats)
        all_dates = {log.study_date for log in all_logs}
        total_study_days = len(all_dates)

        return GoalStudyStats(
            goal_id=goal_id,
            task_stats=task_stats,
            total_minutes=total_minutes,
            total_study_days=total_study_days,
        )

    def _calculate_task_stats(
        self, task_id: str, logs: list[StudyLog]
    ) -> TaskStudyStats:
        """タスクの学習統計を計算する.

        Args:
            task_id: タスクID.
            logs: 学習ログのリスト.

        Returns:
            タスクの学習統計.
        """
        total_minutes = sum(log.duration_minutes for log in logs)
        unique_dates = {log.study_date for log in logs}
        return TaskStudyStats(
            task_id=task_id,
            total_minutes=total_minutes,
            study_days=len(unique_dates),
            log_count=len(logs),
        )
