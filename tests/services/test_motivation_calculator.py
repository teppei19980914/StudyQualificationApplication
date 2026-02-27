"""MotivationCalculatorのテスト."""

from datetime import date, timedelta

import pytest

from study_python.models.study_log import StudyLog
from study_python.services.motivation_calculator import (
    ConsistencyData,
    MilestoneType,
    MotivationCalculator,
    PersonalRecordData,
    StreakData,
    TodayStudyData,
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

    def test_no_logs_cumulative(self, calculator):
        """ログなしの累計値."""
        result = calculator.calculate_milestones([])
        assert result.total_hours == 0.0
        assert result.study_days == 0
        assert result.current_streak == 0

    def test_total_hours(self, calculator):
        """累計学習時間の計算."""
        logs = [_make_log(date(2026, 2, 26), 90)]
        result = calculator.calculate_milestones(logs)
        assert result.total_hours == 1.5

    def test_study_days(self, calculator):
        """累計学習日数の計算."""
        logs = [_make_log(date(2026, 2, 20) + timedelta(days=i), 30) for i in range(7)]
        result = calculator.calculate_milestones(logs)
        assert result.study_days == 7

    def test_current_streak(self, calculator):
        """連続学習日数の受け渡し."""
        result = calculator.calculate_milestones([], current_streak=7)
        assert result.current_streak == 7

    def test_total_hours_rounding(self, calculator):
        """累計時間が小数第1位に丸められる."""
        # 100分 = 1.6666... → 1.7
        logs = [_make_log(date(2026, 2, 26), 100)]
        result = calculator.calculate_milestones(logs)
        assert result.total_hours == 1.7

    def test_multiple_logs_same_day(self, calculator):
        """同じ日の複数ログは1日としてカウント."""
        logs = [
            _make_log(date(2026, 2, 26), 30, task_id="t1"),
            _make_log(date(2026, 2, 26), 45, task_id="t2"),
        ]
        result = calculator.calculate_milestones(logs)
        assert result.study_days == 1
        assert result.total_hours == 1.2  # 75分 = 1.25 → 1.2

    def test_large_values(self, calculator):
        """大量学習のケース."""
        logs = [
            _make_log(date(2025, 1, 1) + timedelta(days=i), 180) for i in range(120)
        ]
        result = calculator.calculate_milestones(logs, current_streak=100)
        assert result.total_hours == 360.0
        assert result.study_days == 120
        assert result.current_streak == 100

    def test_zero_streak_default(self, calculator):
        """current_streakのデフォルト値は0."""
        logs = [_make_log(date(2026, 2, 26), 60)]
        result = calculator.calculate_milestones(logs)
        assert result.current_streak == 0

    def test_no_logs_achieved(self, calculator):
        """ログなしの閾値達成."""
        result = calculator.calculate_milestones([])
        assert result.achieved == []
        assert result.next_milestone is not None
        assert result.next_milestone.milestone_type == MilestoneType.TOTAL_HOURS
        assert result.next_milestone.value == 1

    def test_one_hour_achieved(self, calculator):
        """累計1時間達成の閾値通知."""
        logs = [_make_log(date(2026, 2, 26), 60)]
        result = calculator.calculate_milestones(logs)
        achieved_hours = [
            m for m in result.achieved if m.milestone_type == MilestoneType.TOTAL_HOURS
        ]
        assert any(m.value == 1 for m in achieved_hours)

    def test_study_days_milestone(self, calculator):
        """学習日数の閾値達成."""
        logs = [_make_log(date(2026, 2, 20) + timedelta(days=i), 30) for i in range(7)]
        result = calculator.calculate_milestones(logs)
        achieved_days = [
            m for m in result.achieved if m.milestone_type == MilestoneType.STUDY_DAYS
        ]
        assert any(m.value == 3 for m in achieved_days)
        assert any(m.value == 7 for m in achieved_days)

    def test_streak_milestone(self, calculator):
        """ストリークの閾値達成."""
        result = calculator.calculate_milestones([], current_streak=7)
        achieved_streaks = [
            m for m in result.achieved if m.milestone_type == MilestoneType.STREAK
        ]
        assert any(m.value == 3 for m in achieved_streaks)
        assert any(m.value == 7 for m in achieved_streaks)

    def test_next_milestone_when_partially_achieved(self, calculator):
        """一部達成時の次の閾値."""
        # 2時間 = 120分（1h達成、5hが次）
        logs = [_make_log(date(2026, 2, 26), 120)]
        result = calculator.calculate_milestones(logs)
        assert result.next_milestone is not None
        assert result.next_milestone.value == 5
        assert result.next_milestone.milestone_type == MilestoneType.TOTAL_HOURS

    def test_achieved_sorted_by_value_descending(self, calculator):
        """達成済みは閾値降順でソート."""
        logs = [_make_log(date(2026, 2, 20) + timedelta(days=i), 86) for i in range(7)]
        result = calculator.calculate_milestones(logs, current_streak=7)
        if len(result.achieved) >= 2:
            values = [m.value for m in result.achieved]
            assert values == sorted(values, reverse=True)

    def test_max_5_achieved(self, calculator):
        """達成済みは上位5件に制限."""
        logs = [
            _make_log(date(2025, 1, 1) + timedelta(days=i), 180) for i in range(120)
        ]
        result = calculator.calculate_milestones(logs, current_streak=100)
        assert len(result.achieved) <= 5

    def test_milestone_labels(self, calculator):
        """閾値達成のラベルが正しい."""
        logs = [_make_log(date(2026, 2, 26), 60)]
        result = calculator.calculate_milestones(logs)
        achieved_hours = [
            m for m in result.achieved if m.milestone_type == MilestoneType.TOTAL_HOURS
        ]
        assert any("1時間" in m.label for m in achieved_hours)

    def test_next_milestone_label(self, calculator):
        """次の閾値のラベルが正しい."""
        result = calculator.calculate_milestones([])
        assert result.next_milestone is not None
        assert "1時間" in result.next_milestone.label


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


class TestPersonalRecordData:
    """PersonalRecordDataのテスト."""

    def test_create(self):
        data = PersonalRecordData(
            best_day_minutes=180,
            best_day_date=date(2026, 2, 20),
            best_week_minutes=600,
            best_week_start=date(2026, 2, 17),
            longest_streak=14,
            total_hours=50.5,
            total_study_days=30,
        )
        assert data.best_day_minutes == 180
        assert data.best_day_date == date(2026, 2, 20)
        assert data.best_week_minutes == 600
        assert data.best_week_start == date(2026, 2, 17)
        assert data.longest_streak == 14
        assert data.total_hours == 50.5
        assert data.total_study_days == 30

    def test_create_empty(self):
        data = PersonalRecordData(
            best_day_minutes=0,
            best_day_date=None,
            best_week_minutes=0,
            best_week_start=None,
            longest_streak=0,
            total_hours=0.0,
            total_study_days=0,
        )
        assert data.best_day_date is None
        assert data.best_week_start is None


class TestConsistencyData:
    """ConsistencyDataのテスト."""

    def test_create(self):
        data = ConsistencyData(
            this_week_days=5,
            this_week_total=7,
            this_month_days=20,
            this_month_total=28,
            overall_rate=0.75,
            overall_study_days=90,
            overall_total_days=120,
        )
        assert data.this_week_days == 5
        assert data.this_week_total == 7
        assert data.this_month_days == 20
        assert data.this_month_total == 28
        assert data.overall_rate == 0.75
        assert data.overall_study_days == 90
        assert data.overall_total_days == 120


class TestCalculatePersonalRecords:
    """calculate_personal_recordsのテスト."""

    def test_empty_logs(self, calculator):
        result = calculator.calculate_personal_records([])
        assert result.best_day_minutes == 0
        assert result.best_day_date is None
        assert result.best_week_minutes == 0
        assert result.best_week_start is None
        assert result.longest_streak == 0
        assert result.total_hours == 0.0
        assert result.total_study_days == 0

    def test_single_log(self, calculator):
        logs = [_make_log(date(2026, 2, 20), 60)]
        result = calculator.calculate_personal_records(logs)
        assert result.best_day_minutes == 60
        assert result.best_day_date == date(2026, 2, 20)
        assert result.best_week_minutes == 60
        # 2026-02-20は金曜、月曜=2/16
        assert result.best_week_start == date(2026, 2, 16)
        assert result.longest_streak == 1
        assert result.total_hours == 1.0
        assert result.total_study_days == 1

    def test_multiple_days_best_day(self, calculator):
        """複数日から最大の1日を特定."""
        logs = [
            _make_log(date(2026, 2, 18), 30),
            _make_log(date(2026, 2, 19), 120),
            _make_log(date(2026, 2, 20), 60),
        ]
        result = calculator.calculate_personal_records(logs)
        assert result.best_day_minutes == 120
        assert result.best_day_date == date(2026, 2, 19)

    def test_same_day_multiple_sessions(self, calculator):
        """同じ日に複数セッションは合計で判定."""
        logs = [
            _make_log(date(2026, 2, 18), 30, task_id="t1"),
            _make_log(date(2026, 2, 18), 40, task_id="t2"),
            _make_log(date(2026, 2, 19), 60),
        ]
        result = calculator.calculate_personal_records(logs)
        # 2/18: 30+40=70 > 2/19: 60
        assert result.best_day_minutes == 70
        assert result.best_day_date == date(2026, 2, 18)

    def test_best_week(self, calculator):
        """週間最大の特定."""
        logs = [
            # week 1 (2/16-2/22): 90
            _make_log(date(2026, 2, 16), 30),
            _make_log(date(2026, 2, 18), 60),
            # week 2 (2/23-3/1): 150
            _make_log(date(2026, 2, 23), 90),
            _make_log(date(2026, 2, 25), 60),
        ]
        result = calculator.calculate_personal_records(logs)
        assert result.best_week_minutes == 150
        assert result.best_week_start == date(2026, 2, 23)

    def test_longest_streak(self, calculator):
        """最長ストリーク."""
        logs = [
            _make_log(date(2026, 2, 10), 30),
            _make_log(date(2026, 2, 11), 30),
            _make_log(date(2026, 2, 12), 30),
            # gap
            _make_log(date(2026, 2, 20), 30),
            _make_log(date(2026, 2, 21), 30),
        ]
        result = calculator.calculate_personal_records(logs)
        assert result.longest_streak == 3

    def test_total_hours_and_days(self, calculator):
        """累計時間と日数."""
        logs = [
            _make_log(date(2026, 2, 18), 90),
            _make_log(date(2026, 2, 19), 90),
            _make_log(date(2026, 2, 20), 120),
        ]
        result = calculator.calculate_personal_records(logs)
        # 90+90+120=300分=5.0時間
        assert result.total_hours == 5.0
        assert result.total_study_days == 3


class TestCalculateConsistency:
    """calculate_consistencyのテスト."""

    def test_empty_logs(self, calculator):
        result = calculator.calculate_consistency([], today=date(2026, 2, 26))
        assert result.this_week_days == 0
        assert result.this_month_days == 0
        assert result.overall_rate == 0.0
        assert result.overall_study_days == 0
        assert result.overall_total_days == 0

    def test_this_week_days(self, calculator):
        """今週の学習日数."""
        # 2026-02-26は木曜、月曜=2/23、経過曜日=4(月火水木)
        today = date(2026, 2, 26)
        logs = [
            _make_log(date(2026, 2, 23), 30),  # 月
            _make_log(date(2026, 2, 24), 30),  # 火
            _make_log(date(2026, 2, 26), 30),  # 木
        ]
        result = calculator.calculate_consistency(logs, today=today)
        assert result.this_week_days == 3
        assert result.this_week_total == 4  # 月火水木

    def test_this_month_days(self, calculator):
        """今月の学習日数."""
        today = date(2026, 2, 15)
        logs = [
            _make_log(date(2026, 2, 1), 30),
            _make_log(date(2026, 2, 5), 30),
            _make_log(date(2026, 2, 10), 30),
            _make_log(date(2026, 2, 15), 30),
        ]
        result = calculator.calculate_consistency(logs, today=today)
        assert result.this_month_days == 4
        assert result.this_month_total == 15

    def test_overall_rate(self, calculator):
        """全期間の実施率."""
        today = date(2026, 2, 26)
        # 2/20から2/26の7日間中、3日学習
        logs = [
            _make_log(date(2026, 2, 20), 30),
            _make_log(date(2026, 2, 22), 30),
            _make_log(date(2026, 2, 26), 30),
        ]
        result = calculator.calculate_consistency(logs, today=today)
        assert result.overall_study_days == 3
        assert result.overall_total_days == 7  # 2/20~2/26
        assert result.overall_rate == round(3 / 7, 3)

    def test_monday_as_today(self, calculator):
        """今日が月曜の場合、今週は1日のみ."""
        today = date(2026, 2, 23)  # 月曜
        logs = [_make_log(date(2026, 2, 23), 30)]
        result = calculator.calculate_consistency(logs, today=today)
        assert result.this_week_days == 1
        assert result.this_week_total == 1

    def test_first_day_of_month(self, calculator):
        """月初の場合、今月は1日のみ."""
        today = date(2026, 2, 1)
        logs = [_make_log(date(2026, 2, 1), 30)]
        result = calculator.calculate_consistency(logs, today=today)
        assert result.this_month_days == 1
        assert result.this_month_total == 1

    def test_all_days_studied(self, calculator):
        """全日学習した場合."""
        today = date(2026, 2, 26)
        # 2/20から毎日
        logs = [_make_log(date(2026, 2, 20) + timedelta(days=i), 30) for i in range(7)]
        result = calculator.calculate_consistency(logs, today=today)
        assert result.overall_study_days == 7
        assert result.overall_total_days == 7
        assert result.overall_rate == 1.0

    def test_past_logs_not_in_this_week(self, calculator):
        """先週のログは今週に含まれない."""
        today = date(2026, 2, 26)  # 木曜
        logs = [
            _make_log(date(2026, 2, 22), 30),  # 先週日曜
            _make_log(date(2026, 2, 26), 30),  # 今週木曜
        ]
        result = calculator.calculate_consistency(logs, today=today)
        assert result.this_week_days == 1

    def test_default_today(self, calculator):
        result = calculator.calculate_consistency([])
        assert result.this_week_days == 0
        assert result.overall_rate == 0.0

    def test_multiple_sessions_same_day_counted_once(self, calculator):
        """同じ日の複数セッションは1日としてカウント."""
        today = date(2026, 2, 26)
        logs = [
            _make_log(date(2026, 2, 26), 30, task_id="t1"),
            _make_log(date(2026, 2, 26), 45, task_id="t2"),
        ]
        result = calculator.calculate_consistency(logs, today=today)
        assert result.this_week_days == 1
        assert result.this_month_days == 1
        assert result.overall_study_days == 1
