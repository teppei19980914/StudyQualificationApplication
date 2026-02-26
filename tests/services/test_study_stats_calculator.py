"""StudyStatsCalculatorのテスト."""

from datetime import date

import pytest

from study_python.models.study_log import StudyLog
from study_python.services.study_stats_calculator import (
    DailyActivityData,
    DailyStudyData,
    StudyStatsCalculator,
)


@pytest.fixture
def calculator() -> StudyStatsCalculator:
    return StudyStatsCalculator()


def _make_log(study_date: date, duration_minutes: int, task_id: str = "t1") -> StudyLog:
    """テスト用StudyLogを作成する."""
    return StudyLog(
        task_id=task_id,
        study_date=study_date,
        duration_minutes=duration_minutes,
    )


class TestDailyStudyData:
    """DailyStudyDataのテスト."""

    def test_create(self):
        data = DailyStudyData(study_date=date(2026, 2, 26), total_minutes=60)
        assert data.study_date == date(2026, 2, 26)
        assert data.total_minutes == 60


class TestDailyActivityData:
    """DailyActivityDataのテスト."""

    def test_create(self):
        days = [
            DailyStudyData(study_date=date(2026, 2, 25), total_minutes=30),
            DailyStudyData(study_date=date(2026, 2, 26), total_minutes=60),
        ]
        data = DailyActivityData(
            days=days,
            max_minutes=60,
            period_start=date(2026, 2, 25),
            period_end=date(2026, 2, 26),
        )
        assert len(data.days) == 2
        assert data.max_minutes == 60
        assert data.period_start == date(2026, 2, 25)
        assert data.period_end == date(2026, 2, 26)


class TestStudyStatsCalculator:
    """StudyStatsCalculatorのテスト."""

    def test_empty_logs_returns_zero_filled_days(self, calculator):
        result = calculator.calculate_daily_activity(
            logs=[], period_days=7, end_date=date(2026, 2, 26)
        )
        assert len(result.days) == 7
        assert all(d.total_minutes == 0 for d in result.days)
        assert result.max_minutes == 0

    def test_days_count_matches_period(self, calculator):
        result = calculator.calculate_daily_activity(
            logs=[], period_days=30, end_date=date(2026, 2, 26)
        )
        assert len(result.days) == 30

    def test_period_start_end(self, calculator):
        result = calculator.calculate_daily_activity(
            logs=[], period_days=7, end_date=date(2026, 2, 26)
        )
        assert result.period_start == date(2026, 2, 20)
        assert result.period_end == date(2026, 2, 26)

    def test_single_log(self, calculator):
        logs = [_make_log(date(2026, 2, 26), 45)]
        result = calculator.calculate_daily_activity(
            logs=logs, period_days=7, end_date=date(2026, 2, 26)
        )
        assert result.days[-1].total_minutes == 45
        assert result.days[-1].study_date == date(2026, 2, 26)
        assert result.max_minutes == 45

    def test_multiple_logs_same_day_aggregated(self, calculator):
        logs = [
            _make_log(date(2026, 2, 26), 30),
            _make_log(date(2026, 2, 26), 45),
        ]
        result = calculator.calculate_daily_activity(
            logs=logs, period_days=7, end_date=date(2026, 2, 26)
        )
        assert result.days[-1].total_minutes == 75
        assert result.max_minutes == 75

    def test_logs_outside_period_excluded(self, calculator):
        logs = [
            _make_log(date(2026, 2, 10), 60),  # 期間外
            _make_log(date(2026, 2, 25), 30),  # 期間内
        ]
        result = calculator.calculate_daily_activity(
            logs=logs, period_days=7, end_date=date(2026, 2, 26)
        )
        # 期間外のログは含まれない
        total = sum(d.total_minutes for d in result.days)
        assert total == 30

    def test_custom_period_days(self, calculator):
        logs = [_make_log(date(2026, 2, 26), 60)]
        result = calculator.calculate_daily_activity(
            logs=logs, period_days=14, end_date=date(2026, 2, 26)
        )
        assert len(result.days) == 14
        assert result.period_start == date(2026, 2, 13)

    def test_max_minutes_calculated_correctly(self, calculator):
        logs = [
            _make_log(date(2026, 2, 24), 30),
            _make_log(date(2026, 2, 25), 120),
            _make_log(date(2026, 2, 26), 60),
        ]
        result = calculator.calculate_daily_activity(
            logs=logs, period_days=7, end_date=date(2026, 2, 26)
        )
        assert result.max_minutes == 120

    def test_days_sorted_chronologically(self, calculator):
        logs = [_make_log(date(2026, 2, 26), 60)]
        result = calculator.calculate_daily_activity(
            logs=logs, period_days=7, end_date=date(2026, 2, 26)
        )
        dates = [d.study_date for d in result.days]
        assert dates == sorted(dates)

    def test_zero_minute_days_included(self, calculator):
        logs = [
            _make_log(date(2026, 2, 20), 30),
            _make_log(date(2026, 2, 26), 60),
        ]
        result = calculator.calculate_daily_activity(
            logs=logs, period_days=7, end_date=date(2026, 2, 26)
        )
        zero_days = [d for d in result.days if d.total_minutes == 0]
        assert len(zero_days) == 5

    def test_default_end_date_is_today(self, calculator):
        result = calculator.calculate_daily_activity(logs=[], period_days=7)
        assert result.period_end == date.today()

    def test_multiple_tasks_same_day(self, calculator):
        logs = [
            _make_log(date(2026, 2, 26), 30, task_id="t1"),
            _make_log(date(2026, 2, 26), 45, task_id="t2"),
        ]
        result = calculator.calculate_daily_activity(
            logs=logs, period_days=7, end_date=date(2026, 2, 26)
        )
        assert result.days[-1].total_minutes == 75

    def test_period_days_1(self, calculator):
        logs = [_make_log(date(2026, 2, 26), 60)]
        result = calculator.calculate_daily_activity(
            logs=logs, period_days=1, end_date=date(2026, 2, 26)
        )
        assert len(result.days) == 1
        assert result.days[0].total_minutes == 60
        assert result.period_start == date(2026, 2, 26)
