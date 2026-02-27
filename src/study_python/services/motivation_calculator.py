"""モチベーション関連の統計計算ロジック."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

from study_python.models.study_log import StudyLog


logger = logging.getLogger(__name__)


class MilestoneType(Enum):
    """実績の種類（将来の通知機能用）.

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
    """実績の閾値達成通知.

    Attributes:
        milestone_type: 実績の種類.
        value: 達成した閾値.
        label: 表示テキスト.
    """

    milestone_type: MilestoneType
    value: int
    label: str


@dataclass
class MilestoneData:
    """実績データ.

    累計値と閾値達成通知の両方を保持する。

    Attributes:
        total_hours: 累計学習時間（時間）.
        study_days: 累計学習日数.
        current_streak: 連続学習日数.
        achieved: 達成済み閾値通知のリスト.
        next_milestone: 次に達成する閾値通知.
    """

    total_hours: float = 0.0
    study_days: int = 0
    current_streak: int = 0
    achieved: list[Milestone] = field(default_factory=list)
    next_milestone: Milestone | None = None


@dataclass
class PersonalRecordData:
    """自己ベスト記録データ.

    Attributes:
        best_day_minutes: 1日最大学習時間（分）.
        best_day_date: その日付.
        best_week_minutes: 1週間最大学習時間（分）.
        best_week_start: その週の月曜日.
        longest_streak: 最長連続学習日数.
        total_hours: 累計学習時間（時間）.
        total_study_days: 累計学習日数.
    """

    best_day_minutes: int
    best_day_date: date | None
    best_week_minutes: int
    best_week_start: date | None
    longest_streak: int
    total_hours: float
    total_study_days: int


@dataclass
class ConsistencyData:
    """学習実施率データ.

    Attributes:
        this_week_days: 今週の学習日数 (0-7).
        this_week_total: 今週の経過曜日数 (1-7).
        this_month_days: 今月の学習日数.
        this_month_total: 今月の経過日数.
        overall_rate: 全期間の実施率 (0.0-1.0).
        overall_study_days: 全期間の学習日数.
        overall_total_days: 初学習日からの経過日数.
    """

    this_week_days: int
    this_week_total: int
    this_month_days: int
    this_month_total: int
    overall_rate: float
    overall_study_days: int
    overall_total_days: int


# 実績閾値定義（達成通知用）
_TOTAL_HOURS_THRESHOLDS = [1, 5, 10, 25, 50, 100, 250, 500, 1000]
_STUDY_DAYS_THRESHOLDS = [3, 7, 14, 30, 60, 100, 200, 365]
_STREAK_THRESHOLDS = [3, 7, 14, 30, 60, 100]


class MotivationCalculator:
    """モチベーション関連の統計計算を行うクラス.

    StudyLogのリストからストリーク、今日の学習状況、
    実績、自己ベスト、実施率データを生成する。
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
        """実績を計算する.

        累計値と閾値達成通知の両方を返す。

        Args:
            logs: 学習ログのリスト.
            current_streak: 現在の連続学習日数.

        Returns:
            実績データ.
        """
        total_minutes = sum(log.duration_minutes for log in logs)
        total_hours = round(total_minutes / 60, 1)
        study_days = len({log.study_date for log in logs})

        achieved: list[Milestone] = []
        next_milestone: Milestone | None = None

        # 累計時間の閾値達成
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

        # 学習日数の閾値達成
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

        # ストリークの閾値達成
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
            f"Milestones: total_hours={total_hours}, "
            f"study_days={study_days}, current_streak={current_streak}, "
            f"{len(achieved)} achieved, "
            f"next={next_milestone.label if next_milestone else 'None'}"
        )

        return MilestoneData(
            total_hours=total_hours,
            study_days=study_days,
            current_streak=current_streak,
            achieved=achieved,
            next_milestone=next_milestone,
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

    def calculate_personal_records(
        self,
        logs: list[StudyLog],
        _today: date | None = None,
    ) -> PersonalRecordData:
        """自己ベスト記録を計算する.

        Args:
            logs: 学習ログのリスト.
            _today: 基準日（デフォルト今日、未使用だが将来拡張用）.

        Returns:
            自己ベスト記録データ.
        """
        if not logs:
            return PersonalRecordData(
                best_day_minutes=0,
                best_day_date=None,
                best_week_minutes=0,
                best_week_start=None,
                longest_streak=0,
                total_hours=0.0,
                total_study_days=0,
            )

        # 日別合計
        daily_totals: dict[date, int] = defaultdict(int)
        for log in logs:
            daily_totals[log.study_date] += log.duration_minutes

        best_day_date = max(daily_totals, key=daily_totals.get)  # type: ignore[arg-type]
        best_day_minutes = daily_totals[best_day_date]

        # ISO週別合計（月曜始まり）
        weekly_totals: dict[date, int] = defaultdict(int)
        for log in logs:
            monday = log.study_date - timedelta(days=log.study_date.weekday())
            weekly_totals[monday] += log.duration_minutes

        best_week_start = max(weekly_totals, key=weekly_totals.get)  # type: ignore[arg-type]
        best_week_minutes = weekly_totals[best_week_start]

        # 最長ストリーク
        study_dates = {log.study_date for log in logs}
        longest_streak = self._calculate_longest_streak(study_dates)

        # 累計
        total_minutes = sum(log.duration_minutes for log in logs)
        total_hours = round(total_minutes / 60, 1)
        total_study_days = len(study_dates)

        logger.debug(
            f"Personal records: best_day={best_day_minutes}min on {best_day_date}, "
            f"best_week={best_week_minutes}min from {best_week_start}, "
            f"longest_streak={longest_streak}"
        )

        return PersonalRecordData(
            best_day_minutes=best_day_minutes,
            best_day_date=best_day_date,
            best_week_minutes=best_week_minutes,
            best_week_start=best_week_start,
            longest_streak=longest_streak,
            total_hours=total_hours,
            total_study_days=total_study_days,
        )

    def calculate_consistency(
        self,
        logs: list[StudyLog],
        today: date | None = None,
    ) -> ConsistencyData:
        """学習の実施率を計算する.

        Args:
            logs: 学習ログのリスト.
            today: 基準日（デフォルト今日）.

        Returns:
            学習実施率データ.
        """
        if today is None:
            today = date.today()

        study_dates = {log.study_date for log in logs}

        # 今週（月曜〜today）
        this_monday = today - timedelta(days=today.weekday())
        this_week_total = today.weekday() + 1  # 月=1, 火=2, ..., 日=7
        this_week_days = len({d for d in study_dates if this_monday <= d <= today})

        # 今月（1日〜today）
        this_month_start = today.replace(day=1)
        this_month_total = today.day
        this_month_days = len(
            {d for d in study_dates if this_month_start <= d <= today}
        )

        # 全期間
        overall_study_days = len(study_dates)
        if study_dates:
            first_date = min(study_dates)
            overall_total_days = (today - first_date).days + 1
            overall_rate = round(overall_study_days / overall_total_days, 3)
        else:
            overall_total_days = 0
            overall_rate = 0.0

        logger.debug(
            f"Consistency: week={this_week_days}/{this_week_total}, "
            f"month={this_month_days}/{this_month_total}, "
            f"overall={overall_rate:.1%}"
        )

        return ConsistencyData(
            this_week_days=this_week_days,
            this_week_total=this_week_total,
            this_month_days=this_month_days,
            this_month_total=this_month_total,
            overall_rate=overall_rate,
            overall_study_days=overall_study_days,
            overall_total_days=overall_total_days,
        )
