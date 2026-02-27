"""学習統計の計算ロジック."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

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


class ActivityPeriodType(Enum):
    """アクティビティチャートの期間種別.

    Attributes:
        YEARLY: 年別.
        MONTHLY: 月別.
        WEEKLY: 週別.
        DAILY: 日別.
    """

    YEARLY = "yearly"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"


@dataclass
class ActivityBucketData:
    """チャート1バケット分のデータ.

    Attributes:
        label: X軸ラベル（"2025", "1月", "2/17~", "2/26" など）.
        total_minutes: バケット内合計学習時間（分）.
        period_start: バケット開始日.
        period_end: バケット終了日.
    """

    label: str
    total_minutes: int
    period_start: date
    period_end: date


@dataclass
class ActivityChartData:
    """期間別アクティビティチャート描画用データ.

    Attributes:
        period_type: 期間種別.
        buckets: バケットデータのリスト.
        max_minutes: 全バケット中の最大学習時間（分）.バー高さスケーリング用.
    """

    period_type: ActivityPeriodType
    buckets: list[ActivityBucketData]
    max_minutes: int


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

    def calculate_activity(
        self,
        logs: list[StudyLog],
        period_type: ActivityPeriodType,
        end_date: date | None = None,
    ) -> ActivityChartData:
        """期間別アクティビティを計算する.

        period_typeに応じた集計メソッドにディスパッチする。

        Args:
            logs: 学習ログのリスト.
            period_type: 期間種別.
            end_date: 期間の終了日（デフォルト今日）.

        Returns:
            期間別アクティビティチャートデータ.
        """
        if end_date is None:
            end_date = date.today()

        dispatch = {
            ActivityPeriodType.YEARLY: self._calculate_yearly_activity,
            ActivityPeriodType.MONTHLY: self._calculate_monthly_activity,
            ActivityPeriodType.WEEKLY: self._calculate_weekly_activity,
            ActivityPeriodType.DAILY: self._calculate_daily_activity_buckets,
        }
        return dispatch[period_type](logs, end_date)

    def _calculate_yearly_activity(
        self,
        logs: list[StudyLog],
        end_date: date,
    ) -> ActivityChartData:
        """年別アクティビティを計算する.

        初ログの年から end_date の年まで。ログなし時は今年のみ。

        Args:
            logs: 学習ログのリスト.
            end_date: 基準日.

        Returns:
            年別アクティビティチャートデータ.
        """
        current_year = end_date.year

        if not logs:
            bucket = ActivityBucketData(
                label=str(current_year),
                total_minutes=0,
                period_start=date(current_year, 1, 1),
                period_end=date(current_year, 12, 31),
            )
            return ActivityChartData(
                period_type=ActivityPeriodType.YEARLY,
                buckets=[bucket],
                max_minutes=0,
            )

        min_year = min(log.study_date.year for log in logs)
        yearly_totals: dict[int, int] = defaultdict(int)
        for log in logs:
            yearly_totals[log.study_date.year] += log.duration_minutes

        buckets: list[ActivityBucketData] = []
        for year in range(min_year, current_year + 1):
            buckets.append(
                ActivityBucketData(
                    label=str(year),
                    total_minutes=yearly_totals.get(year, 0),
                    period_start=date(year, 1, 1),
                    period_end=date(year, 12, 31),
                )
            )

        max_minutes = max((b.total_minutes for b in buckets), default=0)

        logger.debug(f"Yearly activity: {len(buckets)} years, max={max_minutes}min")

        return ActivityChartData(
            period_type=ActivityPeriodType.YEARLY,
            buckets=buckets,
            max_minutes=max_minutes,
        )

    def _calculate_monthly_activity(
        self,
        logs: list[StudyLog],
        end_date: date,
    ) -> ActivityChartData:
        """月別アクティビティを計算する（直近12ヶ月）.

        Args:
            logs: 学習ログのリスト.
            end_date: 基準日.

        Returns:
            月別アクティビティチャートデータ.
        """
        # 直近12ヶ月のバケットを生成
        buckets: list[ActivityBucketData] = []
        for i in range(11, -1, -1):
            # i ヶ月前の1日
            year = end_date.year
            month = end_date.month - i
            while month <= 0:
                month += 12
                year -= 1
            first_day = date(year, month, 1)
            # 月末日
            if month == 12:
                last_day = date(year, 12, 31)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)

            buckets.append(
                ActivityBucketData(
                    label=f"{month}月",
                    total_minutes=0,
                    period_start=first_day,
                    period_end=last_day,
                )
            )

        # ログを集計
        for log in logs:
            for bucket in buckets:
                if bucket.period_start <= log.study_date <= bucket.period_end:
                    bucket.total_minutes += log.duration_minutes
                    break

        max_minutes = max((b.total_minutes for b in buckets), default=0)

        logger.debug(f"Monthly activity: 12 months, max={max_minutes}min")

        return ActivityChartData(
            period_type=ActivityPeriodType.MONTHLY,
            buckets=buckets,
            max_minutes=max_minutes,
        )

    def _calculate_weekly_activity(
        self,
        logs: list[StudyLog],
        end_date: date,
    ) -> ActivityChartData:
        """週別アクティビティを計算する（直近12週、月曜起点）.

        Args:
            logs: 学習ログのリスト.
            end_date: 基準日.

        Returns:
            週別アクティビティチャートデータ.
        """
        # end_dateの属する週の月曜日
        current_monday = end_date - timedelta(days=end_date.weekday())

        buckets: list[ActivityBucketData] = []
        for i in range(11, -1, -1):
            monday = current_monday - timedelta(weeks=i)
            sunday = monday + timedelta(days=6)
            label = f"{monday.month}/{monday.day}~"
            buckets.append(
                ActivityBucketData(
                    label=label,
                    total_minutes=0,
                    period_start=monday,
                    period_end=sunday,
                )
            )

        # ログを集計
        for log in logs:
            for bucket in buckets:
                if bucket.period_start <= log.study_date <= bucket.period_end:
                    bucket.total_minutes += log.duration_minutes
                    break

        max_minutes = max((b.total_minutes for b in buckets), default=0)

        logger.debug(f"Weekly activity: 12 weeks, max={max_minutes}min")

        return ActivityChartData(
            period_type=ActivityPeriodType.WEEKLY,
            buckets=buckets,
            max_minutes=max_minutes,
        )

    def _calculate_daily_activity_buckets(
        self,
        logs: list[StudyLog],
        end_date: date,
    ) -> ActivityChartData:
        """日別アクティビティをバケット形式で計算する（直近30日）.

        Args:
            logs: 学習ログのリスト.
            end_date: 基準日.

        Returns:
            日別アクティビティチャートデータ.
        """
        period_start = end_date - timedelta(days=29)

        daily_totals: dict[date, int] = defaultdict(int)
        for log in logs:
            if period_start <= log.study_date <= end_date:
                daily_totals[log.study_date] += log.duration_minutes

        buckets: list[ActivityBucketData] = []
        current = period_start
        while current <= end_date:
            buckets.append(
                ActivityBucketData(
                    label=f"{current.month}/{current.day}",
                    total_minutes=daily_totals.get(current, 0),
                    period_start=current,
                    period_end=current,
                )
            )
            current += timedelta(days=1)

        max_minutes = max((b.total_minutes for b in buckets), default=0)

        logger.debug(f"Daily activity buckets: 30 days, max={max_minutes}min")

        return ActivityChartData(
            period_type=ActivityPeriodType.DAILY,
            buckets=buckets,
            max_minutes=max_minutes,
        )
