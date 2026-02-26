"""モチベーション関連の統計計算ロジック."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

from study_python.models.study_log import StudyLog


logger = logging.getLogger(__name__)


class MilestoneType(Enum):
    """マイルストーンの種類.

    Attributes:
        TOTAL_HOURS: 累計学習時間.
        STUDY_DAYS: 学習日数.
        STREAK: 連続学習日数.
    """

    TOTAL_HOURS = "total_hours"
    STUDY_DAYS = "study_days"
    STREAK = "streak"


@dataclass
class StreakData:
    """連続学習日数データ.

    Attributes:
        current_streak: 現在の連続学習日数.
        longest_streak: 過去最長の連続学習日数.
        studied_today: 今日学習したか.
    """

    current_streak: int
    longest_streak: int
    studied_today: bool


@dataclass
class TodayStudyData:
    """今日の学習状況データ.

    Attributes:
        total_minutes: 今日の合計学習時間（分）.
        session_count: 今日のセッション数.
        studied: 今日学習したか.
    """

    total_minutes: int
    session_count: int
    studied: bool


@dataclass
class Milestone:
    """マイルストーン.

    Attributes:
        milestone_type: マイルストーンの種類.
        value: 達成した閾値.
        label: 表示テキスト.
    """

    milestone_type: MilestoneType
    value: int
    label: str


@dataclass
class MilestoneData:
    """マイルストーンデータ.

    Attributes:
        achieved: 達成済みマイルストーンのリスト.
        next_milestone: 次に達成するマイルストーン.
    """

    achieved: list[Milestone] = field(default_factory=list)
    next_milestone: Milestone | None = None


@dataclass
class WeeklyComparisonData:
    """週間比較データ.

    Attributes:
        this_week_minutes: 今週の合計学習時間（分）.
        last_week_minutes: 先週の合計学習時間（分）.
        difference_minutes: 差分（正=増加, 負=減少）.
        change_percent: 変化率（先週が0の場合はNone）.
    """

    this_week_minutes: int
    last_week_minutes: int
    difference_minutes: int
    change_percent: float | None


# マイルストーン閾値定義
_TOTAL_HOURS_THRESHOLDS = [1, 5, 10, 25, 50, 100, 250, 500, 1000]
_STUDY_DAYS_THRESHOLDS = [3, 7, 14, 30, 60, 100, 200, 365]
_STREAK_THRESHOLDS = [3, 7, 14, 30, 60, 100]


class MotivationCalculator:
    """モチベーション関連の統計計算を行うクラス.

    StudyLogのリストからストリーク、今日の学習状況、
    マイルストーン、週間比較データを生成する。
    """

    def calculate_streak(
        self,
        logs: list[StudyLog],
        today: date | None = None,
    ) -> StreakData:
        """連続学習日数を計算する.

        今日未学習でも昨日まで連続していればストリーク維持とする。

        Args:
            logs: 学習ログのリスト.
            today: 基準日（デフォルト今日）.

        Returns:
            ストリークデータ.
        """
        if today is None:
            today = date.today()

        study_dates = {log.study_date for log in logs}
        studied_today = today in study_dates

        # 現在のストリーク計算
        # 今日学習済み → 今日から遡る
        # 今日未学習 → 昨日から遡る
        current_streak = 0
        check_date = today if studied_today else today - timedelta(days=1)
        while check_date in study_dates:
            current_streak += 1
            check_date -= timedelta(days=1)

        # 最長ストリーク計算
        longest_streak = self._calculate_longest_streak(study_dates)

        logger.debug(
            f"Streak calculated: current={current_streak}, "
            f"longest={longest_streak}, studied_today={studied_today}"
        )

        return StreakData(
            current_streak=current_streak,
            longest_streak=longest_streak,
            studied_today=studied_today,
        )

    def calculate_today_study(
        self,
        logs: list[StudyLog],
        today: date | None = None,
    ) -> TodayStudyData:
        """今日の学習状況を計算する.

        Args:
            logs: 学習ログのリスト.
            today: 基準日（デフォルト今日）.

        Returns:
            今日の学習状況データ.
        """
        if today is None:
            today = date.today()

        today_logs = [log for log in logs if log.study_date == today]
        total_minutes = sum(log.duration_minutes for log in today_logs)
        session_count = len(today_logs)

        logger.debug(f"Today study: {total_minutes}min, {session_count} sessions")

        return TodayStudyData(
            total_minutes=total_minutes,
            session_count=session_count,
            studied=session_count > 0,
        )

    def calculate_milestones(
        self,
        logs: list[StudyLog],
        current_streak: int = 0,
    ) -> MilestoneData:
        """マイルストーンを計算する.

        達成済みの直近マイルストーンと次のマイルストーンを返す。

        Args:
            logs: 学習ログのリスト.
            current_streak: 現在の連続学習日数.

        Returns:
            マイルストーンデータ.
        """
        total_minutes = sum(log.duration_minutes for log in logs)
        total_hours = total_minutes / 60
        study_days = len({log.study_date for log in logs})

        achieved: list[Milestone] = []
        next_milestone: Milestone | None = None

        # 累計時間のマイルストーン
        for threshold in _TOTAL_HOURS_THRESHOLDS:
            if total_hours >= threshold:
                achieved.append(
                    Milestone(
                        milestone_type=MilestoneType.TOTAL_HOURS,
                        value=threshold,
                        label=f"累計{threshold}時間達成！",
                    )
                )
            elif next_milestone is None:
                next_milestone = Milestone(
                    milestone_type=MilestoneType.TOTAL_HOURS,
                    value=threshold,
                    label=f"累計{threshold}時間",
                )
                break

        # 学習日数のマイルストーン
        for threshold in _STUDY_DAYS_THRESHOLDS:
            if study_days >= threshold:
                achieved.append(
                    Milestone(
                        milestone_type=MilestoneType.STUDY_DAYS,
                        value=threshold,
                        label=f"学習{threshold}日達成！",
                    )
                )
            else:
                if next_milestone is None:
                    next_milestone = Milestone(
                        milestone_type=MilestoneType.STUDY_DAYS,
                        value=threshold,
                        label=f"学習{threshold}日",
                    )
                break

        # ストリークのマイルストーン
        for threshold in _STREAK_THRESHOLDS:
            if current_streak >= threshold:
                achieved.append(
                    Milestone(
                        milestone_type=MilestoneType.STREAK,
                        value=threshold,
                        label=f"連続{threshold}日達成！",
                    )
                )
            else:
                if next_milestone is None:
                    next_milestone = Milestone(
                        milestone_type=MilestoneType.STREAK,
                        value=threshold,
                        label=f"連続{threshold}日",
                    )
                break

        # 達成済みは最近のもの（閾値が大きいもの）を上位に
        achieved.sort(key=lambda m: m.value, reverse=True)

        # 上位5件に絞る
        achieved = achieved[:5]

        logger.debug(
            f"Milestones: {len(achieved)} achieved, "
            f"next={next_milestone.label if next_milestone else 'None'}"
        )

        return MilestoneData(
            achieved=achieved,
            next_milestone=next_milestone,
        )

    def calculate_weekly_comparison(
        self,
        logs: list[StudyLog],
        today: date | None = None,
    ) -> WeeklyComparisonData:
        """今週と先週の学習時間を比較する.

        今週 = 今日の週の月曜日〜今日
        先週 = 前週の月曜日〜日曜日

        Args:
            logs: 学習ログのリスト.
            today: 基準日（デフォルト今日）.

        Returns:
            週間比較データ.
        """
        if today is None:
            today = date.today()

        # 今週の月曜日
        this_monday = today - timedelta(days=today.weekday())
        # 先週の月曜日・日曜日
        last_monday = this_monday - timedelta(days=7)
        last_sunday = this_monday - timedelta(days=1)

        this_week_minutes = sum(
            log.duration_minutes
            for log in logs
            if this_monday <= log.study_date <= today
        )
        last_week_minutes = sum(
            log.duration_minutes
            for log in logs
            if last_monday <= log.study_date <= last_sunday
        )

        difference = this_week_minutes - last_week_minutes
        change_percent: float | None = None
        if last_week_minutes > 0:
            change_percent = round((difference / last_week_minutes) * 100, 1)

        logger.debug(
            f"Weekly comparison: this={this_week_minutes}min, "
            f"last={last_week_minutes}min, diff={difference}min"
        )

        return WeeklyComparisonData(
            this_week_minutes=this_week_minutes,
            last_week_minutes=last_week_minutes,
            difference_minutes=difference,
            change_percent=change_percent,
        )

    @staticmethod
    def _calculate_longest_streak(study_dates: set[date]) -> int:
        """全期間の最長連続学習日数を計算する.

        Args:
            study_dates: 学習した日付のセット.

        Returns:
            最長連続日数.
        """
        if not study_dates:
            return 0

        sorted_dates = sorted(study_dates)
        longest = 1
        current = 1

        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
                current += 1
                longest = max(longest, current)
            else:
                current = 1

        return longest
