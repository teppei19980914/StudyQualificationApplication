"""TaskDialog内の学習ログ管理ロジック."""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from datetime import date

from study_python.models.study_log import StudyLog
from study_python.services.study_log_service import StudyLogService, TaskStudyStats


logger = logging.getLogger(__name__)


@dataclass
class StudyLogDisplayEntry:
    """表示用学習ログエントリ.

    Attributes:
        log_id: ログID（削除用）.
        study_date: 学習実施日.
        duration_minutes: 学習時間（分）.
        memo: メモ.
    """

    log_id: str
    study_date: date
    duration_minutes: int
    memo: str


class TaskStudyLogLogic:
    """TaskDialog内の学習ログビジネスロジック.

    Attributes:
        _study_log_service: 学習ログサービス.
        _task_id: 対象タスクID.
        _task_name: 対象タスク名（記録時に保存用）.
    """

    def __init__(
        self,
        study_log_service: StudyLogService,
        task_id: str,
        task_name: str,
    ) -> None:
        """TaskStudyLogLogicを初期化する.

        Args:
            study_log_service: 学習ログサービス.
            task_id: 対象タスクID.
            task_name: 対象タスク名.
        """
        self._study_log_service = study_log_service
        self._task_id = task_id
        self._task_name = task_name
        self._timer_start: float | None = None

    def get_logs(self) -> list[StudyLogDisplayEntry]:
        """タスクの学習ログ一覧を取得する（日付降順）.

        Returns:
            表示用エントリのリスト.
        """
        logs = self._study_log_service.get_logs_for_task(self._task_id)
        entries = [
            StudyLogDisplayEntry(
                log_id=log.id,
                study_date=log.study_date,
                duration_minutes=log.duration_minutes,
                memo=log.memo,
            )
            for log in logs
        ]
        entries.sort(key=lambda e: e.study_date, reverse=True)
        return entries

    def get_stats(self) -> TaskStudyStats:
        """タスクの学習統計を取得する.

        Returns:
            タスクの学習統計.
        """
        return self._study_log_service.get_task_stats(self._task_id)

    def add_log(
        self,
        study_date: date,
        duration_minutes: int,
        memo: str = "",
    ) -> StudyLog:
        """学習ログを追加する.

        Args:
            study_date: 学習実施日.
            duration_minutes: 学習時間（分）.
            memo: メモ.

        Returns:
            作成されたStudyLog.

        Raises:
            ValueError: 学習時間が不正な場合.
        """
        return self._study_log_service.add_study_log(
            task_id=self._task_id,
            study_date=study_date,
            duration_minutes=duration_minutes,
            memo=memo,
            task_name=self._task_name,
        )

    def delete_log(self, log_id: str) -> bool:
        """学習ログを削除する.

        Args:
            log_id: 削除するログID.

        Returns:
            削除に成功した場合True.
        """
        return self._study_log_service.delete_log(log_id)

    @staticmethod
    def validate_duration(hours: int, minutes: int) -> int:
        """時間と分から合計分数を計算し検証する.

        Args:
            hours: 時間.
            minutes: 分.

        Returns:
            合計分数.

        Raises:
            ValueError: 合計が0以下の場合.
        """
        total = hours * 60 + minutes
        if total <= 0:
            msg = "学習時間は1分以上で入力してください。"
            raise ValueError(msg)
        return total

    @staticmethod
    def format_duration(minutes: int) -> str:
        """学習時間を表示用にフォーマットする.

        Args:
            minutes: 学習時間（分）.

        Returns:
            フォーマット済み文字列（例: "1h 30min", "45min"）.
        """
        if minutes >= 60:
            h = minutes // 60
            m = minutes % 60
            if m > 0:
                return f"{h}h {m:02}min"
            return f"{h}h 00min"
        return f"{minutes}min"

    def start_timer(self) -> None:
        """タイマーを開始する."""
        self._timer_start = time.monotonic()

    def stop_timer(self) -> int:
        """タイマーを停止し経過分数を返す（最小1分、切り上げ）.

        Returns:
            経過分数（タイマー未開始の場合は0）.
        """
        if self._timer_start is None:
            return 0
        elapsed = time.monotonic() - self._timer_start
        self._timer_start = None
        return max(1, math.ceil(elapsed / 60))

    @property
    def is_timer_running(self) -> bool:
        """タイマーが実行中かどうかを返す."""
        return self._timer_start is not None

    @property
    def elapsed_seconds(self) -> int:
        """タイマーの経過秒数を返す.

        Returns:
            経過秒数（タイマー未開始の場合は0）.
        """
        if self._timer_start is None:
            return 0
        return int(time.monotonic() - self._timer_start)
