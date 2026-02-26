"""MotivationCalculatorのテスト."""

from datetime import date, timedelta

import pytest

from study_python.models.study_log import StudyLog
from study_python.services.motivation_calculator import (
    MilestoneType,
    MotivationCalculator,
    StreakData,
    TodayStudyData,
    WeeklyComparisonData,
)


@pytest.fixture
def calculator() -> MotivationCalculator:
    return MotivationCalculator()


def _make_log(study_date: date, duration_minutes: int, task_id: str = "t1") -> StudyLog:
    """テスト用StudyLogを作成する."""
    return StudyLog(
        task_id=task_id,
        study_date=study_date,
        duration_minutes=duration_minutes,
    )


class TestStreakData:
    """StreakDataのテスト."""

    def test_create(self):
        data = StreakData(current_streak=5, longest_streak=10, studied_today=True)
        assert data.current_streak == 5
        assert data.longest_streak == 10
        assert data.studied_today is True


class TestTodayStudyData:
    """TodayStudyDataのテスト."""

    def test_create(self):
        data = TodayStudyData(total_minutes=60, session_count=2, studied=True)
        assert data.total_minutes == 60
        assert data.session_count == 2
        assert data.studied is True


class TestWeeklyComparisonData:
    """WeeklyComparisonDataのテスト."""

    def test_create(self):
        data = WeeklyComparisonData(
            this_week_minutes=120,
            last_week_minutes=90,
            difference_minutes=30,
            change_percent=33.3,
        )
        assert data.this_week_minutes == 120
        assert data.last_week_minutes == 90
        assert data.difference_minutes == 30
        assert data.change_percent == 33.3

    def test_create_with_none_percent(self):
        data = WeeklyComparisonData(
            this_week_minutes=60,
            last_week_minutes=0,
            difference_minutes=60,
            change_percent=None,
        )
        assert data.change_percent is None


class TestCalculateStreak:
    """calculate_streakのテスト."""

    def test_empty_logs(self, calculator):
        result = calculator.calculate_streak([], today=date(2026, 2, 26))
        assert result.current_streak == 0
        assert result.longest_streak == 0
        assert result.studied_today is False

    def test_studied_today_only(self, calculator):
        logs = [_make_log(date(2026, 2, 26), 30)]
        result = calculator.calculate_streak(logs, today=date(2026, 2, 26))
        assert result.current_streak == 1
        assert result.longest_streak == 1
        assert result.studied_today is True

    def test_consecutive_days_including_today(self, calculator):
        logs = [
            _make_log(date(2026, 2, 24), 30),
            _make_log(date(2026, 2, 25), 30),
            _make_log(date(2026, 2, 26), 30),
        ]
        result = calculator.calculate_streak(logs, today=date(2026, 2, 26))
        assert result.current_streak == 3
        assert result.studied_today is True

    def test_streak_maintained_when_not_studied_today(self, calculator):
        """今日未学習でも昨日まで連続していればストリーク維持."""
        logs = [
            _make_log(date(2026, 2, 24), 30),
            _make_log(date(2026, 2, 25), 30),
        ]
        result = calculator.calculate_streak(logs, today=date(2026, 2, 26))
        assert result.current_streak == 2
        assert result.studied_today is False

    def test_streak_broken(self, calculator):
        """1日空いたらストリークが途切れる."""
        logs = [
            _make_log(date(2026, 2, 23), 30),
            # 2/24は休み
            _make_log(date(2026, 2, 25), 30),
            _make_log(date(2026, 2, 26), 30),
        ]
        result = calculator.calculate_streak(logs, today=date(2026, 2, 26))
        assert result.current_streak == 2

    def test_longest_streak_different_from_current(self, calculator):
        """最長ストリークが現在のストリークと異なるケース."""
        logs = [
            # 過去に5日連続
            _make_log(date(2026, 2, 10), 30),
            _make_log(date(2026, 2, 11), 30),
            _make_log(date(2026, 2, 12), 30),
            _make_log(date(2026, 2, 13), 30),
            _make_log(date(2026, 2, 14), 30),
            # 途切れて現在2日連続
            _make_log(date(2026, 2, 25), 30),
            _make_log(date(2026, 2, 26), 30),
        ]
        result = calculator.calculate_streak(logs, today=date(2026, 2, 26))
        assert result.current_streak == 2
        assert result.longest_streak == 5

    def test_multiple_logs_same_day(self, calculator):
        """同じ日に複数ログがあっても1日としてカウント."""
        logs = [
            _make_log(date(2026, 2, 25), 30, task_id="t1"),
            _make_log(date(2026, 2, 25), 45, task_id="t2"),
            _make_log(date(2026, 2, 26), 60),
        ]
        result = calculator.calculate_streak(logs, today=date(2026, 2, 26))
        assert result.current_streak == 2

    def test_single_day_in_past(self, calculator):
        """過去の1日だけ学習、今日は未学習."""
        logs = [_make_log(date(2026, 2, 20), 30)]
        result = calculator.calculate_streak(logs, today=date(2026, 2, 26))
        assert result.current_streak == 0
        assert result.longest_streak == 1
        assert result.studied_today is False

    def test_default_today(self, calculator):
        """todayを指定しない場合はdate.today()が使われる."""
        result = calculator.calculate_streak([])
        assert result.current_streak == 0
        assert result.studied_today is False


class TestCalculateTodayStudy:
    """calculate_today_studyのテスト."""

    def test_no_study_today(self, calculator):
        logs = [_make_log(date(2026, 2, 25), 30)]
        result = calculator.calculate_today_study(logs, today=date(2026, 2, 26))
        assert result.total_minutes == 0
        assert result.session_count == 0
        assert result.studied is False

    def test_one_session_today(self, calculator):
        logs = [_make_log(date(2026, 2, 26), 45)]
        result = calculator.calculate_today_study(logs, today=date(2026, 2, 26))
        assert result.total_minutes == 45
        assert result.session_count == 1
        assert result.studied is True

    def test_multiple_sessions_today(self, calculator):
        logs = [
            _make_log(date(2026, 2, 26), 30, task_id="t1"),
            _make_log(date(2026, 2, 26), 45, task_id="t2"),
            _make_log(date(2026, 2, 26), 15, task_id="t1"),
        ]
        result = calculator.calculate_today_study(logs, today=date(2026, 2, 26))
        assert result.total_minutes == 90
        assert result.session_count == 3
        assert result.studied is True

    def test_only_past_logs(self, calculator):
        logs = [
            _make_log(date(2026, 2, 24), 30),
            _make_log(date(2026, 2, 25), 60),
        ]
        result = calculator.calculate_today_study(logs, today=date(2026, 2, 26))
        assert result.total_minutes == 0
        assert result.session_count == 0
        assert result.studied is False

    def test_empty_logs(self, calculator):
        result = calculator.calculate_today_study([], today=date(2026, 2, 26))
        assert result.total_minutes == 0
        assert result.session_count == 0
        assert result.studied is False

    def test_default_today(self, calculator):
        result = calculator.calculate_today_study([])
        assert result.studied is False


class TestCalculateMilestones:
    """calculate_milestonesのテスト."""

    def test_no_logs(self, calculator):
        result = calculator.calculate_milestones([])
        assert result.achieved == []
        assert result.next_milestone is not None
        assert result.next_milestone.milestone_type == MilestoneType.TOTAL_HOURS
        assert result.next_milestone.value == 1

    def test_one_hour_achieved(self, calculator):
        """累計1時間達成."""
        logs = [_make_log(date(2026, 2, 26), 60)]
        result = calculator.calculate_milestones(logs)
        achieved_hours = [
            m for m in result.achieved if m.milestone_type == MilestoneType.TOTAL_HOURS
        ]
        assert any(m.value == 1 for m in achieved_hours)

    def test_study_days_milestone(self, calculator):
        """学習日数マイルストーン."""
        logs = [_make_log(date(2026, 2, 20) + timedelta(days=i), 30) for i in range(7)]
        result = calculator.calculate_milestones(logs)
        achieved_days = [
            m for m in result.achieved if m.milestone_type == MilestoneType.STUDY_DAYS
        ]
        assert any(m.value == 3 for m in achieved_days)
        assert any(m.value == 7 for m in achieved_days)

    def test_streak_milestone(self, calculator):
        """ストリークマイルストーン."""
        result = calculator.calculate_milestones([], current_streak=7)
        achieved_streaks = [
            m for m in result.achieved if m.milestone_type == MilestoneType.STREAK
        ]
        assert any(m.value == 3 for m in achieved_streaks)
        assert any(m.value == 7 for m in achieved_streaks)

    def test_next_milestone_when_partially_achieved(self, calculator):
        """一部達成時の次のマイルストーン."""
        # 2時間 = 120分（1h達成、5hが次）
        logs = [_make_log(date(2026, 2, 26), 120)]
        result = calculator.calculate_milestones(logs)
        assert result.next_milestone is not None
        assert result.next_milestone.value == 5
        assert result.next_milestone.milestone_type == MilestoneType.TOTAL_HOURS

    def test_achieved_sorted_by_value_descending(self, calculator):
        """達成済みは閾値降順でソート."""
        # 600分=10時間、7日間学習
        logs = [_make_log(date(2026, 2, 20) + timedelta(days=i), 86) for i in range(7)]
        result = calculator.calculate_milestones(logs, current_streak=7)
        if len(result.achieved) >= 2:
            values = [m.value for m in result.achieved]
            assert values == sorted(values, reverse=True)

    def test_max_5_achieved(self, calculator):
        """達成済みは上位5件に制限."""
        # 大量の学習でたくさんのマイルストーンを達成
        logs = [
            _make_log(date(2025, 1, 1) + timedelta(days=i), 180) for i in range(120)
        ]
        result = calculator.calculate_milestones(logs, current_streak=100)
        assert len(result.achieved) <= 5

    def test_milestone_labels(self, calculator):
        """マイルストーンのラベルが正しい."""
        logs = [_make_log(date(2026, 2, 26), 60)]
        result = calculator.calculate_milestones(logs)
        achieved_hours = [
            m for m in result.achieved if m.milestone_type == MilestoneType.TOTAL_HOURS
        ]
        assert any("1時間" in m.label for m in achieved_hours)

    def test_next_milestone_label(self, calculator):
        """次のマイルストーンのラベルが正しい."""
        result = calculator.calculate_milestones([])
        assert result.next_milestone is not None
        assert "1時間" in result.next_milestone.label


class TestCalculateWeeklyComparison:
    """calculate_weekly_comparisonのテスト."""

    def test_empty_logs(self, calculator):
        result = calculator.calculate_weekly_comparison([], today=date(2026, 2, 26))
        assert result.this_week_minutes == 0
        assert result.last_week_minutes == 0
        assert result.difference_minutes == 0
        assert result.change_percent is None

    def test_this_week_only(self, calculator):
        """今週のみ学習."""
        # 2026-02-26は木曜日、今週の月曜日=2/23
        today = date(2026, 2, 26)
        logs = [
            _make_log(date(2026, 2, 23), 60),  # 月曜
            _make_log(date(2026, 2, 25), 30),  # 水曜
        ]
        result = calculator.calculate_weekly_comparison(logs, today=today)
        assert result.this_week_minutes == 90
        assert result.last_week_minutes == 0
        assert result.difference_minutes == 90
        assert result.change_percent is None

    def test_last_week_only(self, calculator):
        """先週のみ学習."""
        today = date(2026, 2, 26)
        # 先週の月曜=2/16、日曜=2/22
        logs = [
            _make_log(date(2026, 2, 16), 60),
            _make_log(date(2026, 2, 18), 30),
        ]
        result = calculator.calculate_weekly_comparison(logs, today=today)
        assert result.this_week_minutes == 0
        assert result.last_week_minutes == 90
        assert result.difference_minutes == -90
        assert result.change_percent == -100.0

    def test_both_weeks(self, calculator):
        """両方の週で学習."""
        today = date(2026, 2, 26)
        logs = [
            _make_log(date(2026, 2, 17), 60),  # 先週
            _make_log(date(2026, 2, 24), 90),  # 今週
        ]
        result = calculator.calculate_weekly_comparison(logs, today=today)
        assert result.this_week_minutes == 90
        assert result.last_week_minutes == 60
        assert result.difference_minutes == 30
        assert result.change_percent == 50.0

    def test_decrease(self, calculator):
        """今週が先週より少ない."""
        today = date(2026, 2, 26)
        logs = [
            _make_log(date(2026, 2, 17), 120),  # 先週
            _make_log(date(2026, 2, 24), 60),  # 今週
        ]
        result = calculator.calculate_weekly_comparison(logs, today=today)
        assert result.difference_minutes == -60
        assert result.change_percent == -50.0

    def test_logs_outside_two_weeks_excluded(self, calculator):
        """2週間外のログは含まれない."""
        today = date(2026, 2, 26)
        logs = [
            _make_log(date(2026, 2, 1), 120),  # 2週間以上前
            _make_log(date(2026, 2, 24), 30),  # 今週
        ]
        result = calculator.calculate_weekly_comparison(logs, today=today)
        assert result.this_week_minutes == 30
        assert result.last_week_minutes == 0

    def test_monday_as_today(self, calculator):
        """今日が月曜日の場合."""
        # 2026-02-23は月曜日
        today = date(2026, 2, 23)
        logs = [
            _make_log(date(2026, 2, 23), 60),  # 今週月曜
            _make_log(date(2026, 2, 16), 30),  # 先週月曜
        ]
        result = calculator.calculate_weekly_comparison(logs, today=today)
        assert result.this_week_minutes == 60
        assert result.last_week_minutes == 30

    def test_sunday_as_today(self, calculator):
        """今日が日曜日の場合."""
        # 2026-03-01は日曜日、今週の月曜は2/23
        today = date(2026, 3, 1)
        logs = [
            _make_log(date(2026, 2, 23), 60),  # 今週月曜
            _make_log(date(2026, 3, 1), 30),  # 今週日曜（今日）
        ]
        result = calculator.calculate_weekly_comparison(logs, today=today)
        assert result.this_week_minutes == 90

    def test_default_today(self, calculator):
        result = calculator.calculate_weekly_comparison([])
        assert result.this_week_minutes == 0
        assert result.last_week_minutes == 0


class TestCalculateLongestStreak:
    """_calculate_longest_streakのテスト."""

    def test_empty_dates(self):
        result = MotivationCalculator._calculate_longest_streak(set())
        assert result == 0

    def test_single_date(self):
        result = MotivationCalculator._calculate_longest_streak({date(2026, 2, 26)})
        assert result == 1

    def test_consecutive_dates(self):
        dates = {
            date(2026, 2, 24),
            date(2026, 2, 25),
            date(2026, 2, 26),
        }
        result = MotivationCalculator._calculate_longest_streak(dates)
        assert result == 3

    def test_non_consecutive_dates(self):
        dates = {
            date(2026, 2, 20),
            date(2026, 2, 22),
            date(2026, 2, 26),
        }
        result = MotivationCalculator._calculate_longest_streak(dates)
        assert result == 1

    def test_multiple_streaks(self):
        dates = {
            date(2026, 2, 10),
            date(2026, 2, 11),
            # gap
            date(2026, 2, 20),
            date(2026, 2, 21),
            date(2026, 2, 22),
        }
        result = MotivationCalculator._calculate_longest_streak(dates)
        assert result == 3
