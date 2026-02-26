"""学習統計の計算ロジック."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from study_python.models.study_log import StudyLog


logger = logging.getLogger(__name__)


@dataclass
class DailyStudyData:
    """1日分の集計済み学習データ.

    Attributes:
        study_date: 日付.
        total_minutes: その日の合計学習時間（分）.
    """

    study_date: date
    total_minutes: int


@dataclass
class DailyActivityData:
    """チャート描画用の日別学習アクティビティデータ.

    Attributes:
        days: 日別の学習データリスト（期間分、0分の日も含む）.
        max_minutes: 期間内の最大学習時間（分）.バー高さスケーリング用.
        period_start: 期間の開始日.
        period_end: 期間の終了日.
    """

    days: list[DailyStudyData]
    max_minutes: int
    period_start: date
    period_end: date


class StudyStatsCalculator:
    """学習統計の計算を行うクラス.

    StudyLogのリストからチャート描画用のデータを生成する。
    """

    def calculate_daily_activity(
        self,
        logs: list[StudyLog],
        period_days: int = 30,
        end_date: date | None = None,
    ) -> DailyActivityData:
        """日別学習アクティビティを計算する.

        指定期間の日ごとの合計学習時間を集計する。
        学習しなかった日は0分のエントリとして含む。

        Args:
            logs: 学習ログのリスト.
            period_days: 表示期間の日数（デフォルト30日）.
            end_date: 期間の終了日（デフォルト今日）.

        Returns:
            日別学習アクティビティデータ.
        """
        if end_date is None:
            end_date = date.today()

        period_start = end_date - timedelta(days=period_days - 1)

        # ログを日別にグループ化して合計
        daily_totals: dict[date, int] = defaultdict(int)
        for log in logs:
            if period_start <= log.study_date <= end_date:
                daily_totals[log.study_date] += log.duration_minutes

        # 期間内の全日のエントリを生成（0分の日も含む）
        days: list[DailyStudyData] = []
        current = period_start
        while current <= end_date:
            days.append(
                DailyStudyData(
                    study_date=current,
                    total_minutes=daily_totals.get(current, 0),
                )
            )
            current += timedelta(days=1)

        max_minutes = max((d.total_minutes for d in days), default=0)

        logger.debug(
            f"Calculated daily activity: {period_days} days, "
            f"max={max_minutes}min, "
            f"active_days={sum(1 for d in days if d.total_minutes > 0)}"
        )

        return DailyActivityData(
            days=days,
            max_minutes=max_minutes,
            period_start=period_start,
            period_end=end_date,
        )
