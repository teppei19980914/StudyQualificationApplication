"""StudyStatsCalculatorのテスト."""

from datetime import date

import pytest

from study_python.models.study_log import StudyLog
from study_python.services.study_stats_calculator import (
    ActivityBucketData,
    ActivityChartData,
    ActivityPeriodType,
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


class TestActivityPeriodType:
    """ActivityPeriodTypeのテスト."""

    def test_values(self):
        assert ActivityPeriodType.YEARLY.value == "yearly"
        assert ActivityPeriodType.MONTHLY.value == "monthly"
        assert ActivityPeriodType.WEEKLY.value == "weekly"
        assert ActivityPeriodType.DAILY.value == "daily"

    def test_all_types(self):
        assert len(ActivityPeriodType) == 4


class TestActivityBucketData:
    """ActivityBucketDataのテスト."""

    def test_create(self):
        data = ActivityBucketData(
            label="2026",
            total_minutes=120,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 12, 31),
        )
        assert data.label == "2026"
        assert data.total_minutes == 120
        assert data.period_start == date(2026, 1, 1)
        assert data.period_end == date(2026, 12, 31)


class TestActivityChartData:
    """ActivityChartDataのテスト."""

    def test_create(self):
        buckets = [
            ActivityBucketData(
                label="2025",
                total_minutes=60,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
            ),
        ]
        data = ActivityChartData(
            period_type=ActivityPeriodType.YEARLY,
            buckets=buckets,
            max_minutes=60,
        )
        assert data.period_type == ActivityPeriodType.YEARLY
        assert len(data.buckets) == 1
        assert data.max_minutes == 60


class TestCalculateActivityDispatcher:
    """calculate_activityディスパッチャーのテスト."""

    def test_dispatches_yearly(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.YEARLY, end_date=date(2026, 2, 27)
        )
        assert result.period_type == ActivityPeriodType.YEARLY

    def test_dispatches_monthly(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.MONTHLY, end_date=date(2026, 2, 27)
        )
        assert result.period_type == ActivityPeriodType.MONTHLY

    def test_dispatches_weekly(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.WEEKLY, end_date=date(2026, 2, 27)
        )
        assert result.period_type == ActivityPeriodType.WEEKLY

    def test_dispatches_daily(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.DAILY, end_date=date(2026, 2, 27)
        )
        assert result.period_type == ActivityPeriodType.DAILY

    def test_default_end_date(self, calculator):
        result = calculator.calculate_activity([], ActivityPeriodType.DAILY)
        assert result.period_type == ActivityPeriodType.DAILY
        # 日別は30日分
        assert len(result.buckets) == 30


class TestCalculateActivityYearly:
    """年別アクティビティ計算のテスト."""

    def test_empty_logs(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.YEARLY, end_date=date(2026, 2, 27)
        )
        assert len(result.buckets) == 1
        assert result.buckets[0].label == "2026"
        assert result.buckets[0].total_minutes == 0
        assert result.max_minutes == 0

    def test_single_year(self, calculator):
        logs = [_make_log(date(2026, 1, 15), 60)]
        result = calculator.calculate_activity(
            logs, ActivityPeriodType.YEARLY, end_date=date(2026, 2, 27)
        )
        assert len(result.buckets) == 1
        assert result.buckets[0].label == "2026"
        assert result.buckets[0].total_minutes == 60
        assert result.max_minutes == 60

    def test_multiple_years(self, calculator):
        logs = [
            _make_log(date(2024, 6, 1), 30),
            _make_log(date(2025, 3, 15), 90),
            _make_log(date(2026, 1, 10), 60),
        ]
        result = calculator.calculate_activity(
            logs, ActivityPeriodType.YEARLY, end_date=date(2026, 2, 27)
        )
        assert len(result.buckets) == 3
        assert result.buckets[0].label == "2024"
        assert result.buckets[0].total_minutes == 30
        assert result.buckets[1].label == "2025"
        assert result.buckets[1].total_minutes == 90
        assert result.buckets[2].label == "2026"
        assert result.buckets[2].total_minutes == 60
        assert result.max_minutes == 90

    def test_aggregation_within_year(self, calculator):
        logs = [
            _make_log(date(2026, 1, 10), 30),
            _make_log(date(2026, 2, 15), 45),
        ]
        result = calculator.calculate_activity(
            logs, ActivityPeriodType.YEARLY, end_date=date(2026, 2, 27)
        )
        assert len(result.buckets) == 1
        assert result.buckets[0].total_minutes == 75

    def test_period_start_end(self, calculator):
        logs = [_make_log(date(2025, 6, 1), 60)]
        result = calculator.calculate_activity(
            logs, ActivityPeriodType.YEARLY, end_date=date(2026, 2, 27)
        )
        assert result.buckets[0].period_start == date(2025, 1, 1)
        assert result.buckets[0].period_end == date(2025, 12, 31)
        assert result.buckets[1].period_start == date(2026, 1, 1)
        assert result.buckets[1].period_end == date(2026, 12, 31)


class TestCalculateActivityMonthly:
    """月別アクティビティ計算のテスト."""

    def test_empty_logs(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.MONTHLY, end_date=date(2026, 2, 27)
        )
        assert len(result.buckets) == 12
        assert all(b.total_minutes == 0 for b in result.buckets)
        assert result.max_minutes == 0

    def test_12_months(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.MONTHLY, end_date=date(2026, 2, 27)
        )
        # 2025年3月〜2026年2月
        assert result.buckets[0].label == "3月"
        assert result.buckets[-1].label == "2月"

    def test_aggregation(self, calculator):
        logs = [
            _make_log(date(2026, 2, 10), 30),
            _make_log(date(2026, 2, 20), 45),
            _make_log(date(2026, 1, 15), 60),
        ]
        result = calculator.calculate_activity(
            logs, ActivityPeriodType.MONTHLY, end_date=date(2026, 2, 27)
        )
        # 最後のバケット（2月）
        assert result.buckets[-1].total_minutes == 75
        # 1月
        assert result.buckets[-2].total_minutes == 60
        assert result.max_minutes == 75

    def test_label_format(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.MONTHLY, end_date=date(2026, 6, 15)
        )
        # 2025年7月〜2026年6月
        assert result.buckets[0].label == "7月"
        assert result.buckets[-1].label == "6月"

    def test_period_boundaries(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.MONTHLY, end_date=date(2026, 2, 27)
        )
        # 最後のバケット=2月
        feb_bucket = result.buckets[-1]
        assert feb_bucket.period_start == date(2026, 2, 1)
        assert feb_bucket.period_end == date(2026, 2, 28)

    def test_december_period_end(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.MONTHLY, end_date=date(2026, 12, 15)
        )
        dec_bucket = result.buckets[-1]
        assert dec_bucket.period_end == date(2026, 12, 31)


class TestCalculateActivityWeekly:
    """週別アクティビティ計算のテスト."""

    def test_empty_logs(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.WEEKLY, end_date=date(2026, 2, 27)
        )
        assert len(result.buckets) == 12
        assert all(b.total_minutes == 0 for b in result.buckets)
        assert result.max_minutes == 0

    def test_12_weeks(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.WEEKLY, end_date=date(2026, 2, 27)
        )
        assert len(result.buckets) == 12

    def test_aggregation(self, calculator):
        # 2026-02-27 is a Friday, current monday = 2026-02-23
        logs = [
            _make_log(date(2026, 2, 23), 30),  # Monday of current week
            _make_log(date(2026, 2, 25), 45),  # Wednesday of current week
        ]
        result = calculator.calculate_activity(
            logs, ActivityPeriodType.WEEKLY, end_date=date(2026, 2, 27)
        )
        assert result.buckets[-1].total_minutes == 75
        assert result.max_minutes == 75

    def test_label_format(self, calculator):
        # 2026-02-27 is a Friday, current monday = 2026-02-23
        result = calculator.calculate_activity(
            [], ActivityPeriodType.WEEKLY, end_date=date(2026, 2, 27)
        )
        assert result.buckets[-1].label == "2/23~"

    def test_period_boundaries(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.WEEKLY, end_date=date(2026, 2, 27)
        )
        last_bucket = result.buckets[-1]
        # Monday to Sunday
        assert last_bucket.period_start == date(2026, 2, 23)
        assert last_bucket.period_end == date(2026, 3, 1)


class TestCalculateActivityDaily:
    """日別アクティビティバケット計算のテスト."""

    def test_empty_logs(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.DAILY, end_date=date(2026, 2, 27)
        )
        assert len(result.buckets) == 30
        assert all(b.total_minutes == 0 for b in result.buckets)
        assert result.max_minutes == 0

    def test_30_days(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.DAILY, end_date=date(2026, 2, 27)
        )
        assert len(result.buckets) == 30
        # First bucket: Jan 29
        assert result.buckets[0].period_start == date(2026, 1, 29)
        # Last bucket: Feb 27
        assert result.buckets[-1].period_end == date(2026, 2, 27)

    def test_aggregation(self, calculator):
        logs = [
            _make_log(date(2026, 2, 27), 30),
            _make_log(date(2026, 2, 27), 45),
        ]
        result = calculator.calculate_activity(
            logs, ActivityPeriodType.DAILY, end_date=date(2026, 2, 27)
        )
        assert result.buckets[-1].total_minutes == 75
        assert result.max_minutes == 75

    def test_label_format(self, calculator):
        result = calculator.calculate_activity(
            [], ActivityPeriodType.DAILY, end_date=date(2026, 2, 27)
        )
        assert result.buckets[-1].label == "2/27"
        assert result.buckets[0].label == "1/29"

    def test_logs_outside_period_excluded(self, calculator):
        logs = [
            _make_log(date(2026, 1, 1), 60),  # outside 30 days
            _make_log(date(2026, 2, 27), 30),
        ]
        result = calculator.calculate_activity(
            logs, ActivityPeriodType.DAILY, end_date=date(2026, 2, 27)
        )
        total = sum(b.total_minutes for b in result.buckets)
        assert total == 30
