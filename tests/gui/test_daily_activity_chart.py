"""DailyActivityChartのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.daily_activity_chart import DailyActivityChart
from study_python.services.study_stats_calculator import (
    ActivityBucketData,
    ActivityChartData,
    ActivityPeriodType,
    DailyActivityData,
    DailyStudyData,
)


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestDailyActivityChart:
    """DailyActivityChartのテスト."""

    def test_create_widget(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)
        assert chart is not None
        assert chart.minimumHeight() == 180

    def test_set_data_stores_data(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        data = DailyActivityData(
            days=[
                DailyStudyData(date(2026, 2, 25), 30),
                DailyStudyData(date(2026, 2, 26), 60),
            ],
            max_minutes=60,
            period_start=date(2026, 2, 25),
            period_end=date(2026, 2, 26),
        )
        chart.set_data(data)
        assert chart._data is not None
        assert chart._data.max_minutes == 60

    def test_set_data_with_empty_data(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        data = DailyActivityData(
            days=[],
            max_minutes=0,
            period_start=date(2026, 2, 26),
            period_end=date(2026, 2, 26),
        )
        chart.set_data(data)
        assert chart._data is not None

    def test_size_hint_without_data(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        hint = chart.sizeHint()
        assert hint.width() >= 200
        assert hint.height() == 180

    def test_size_hint_with_data(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        from datetime import timedelta

        start = date(2026, 1, 28)
        days = [DailyStudyData(start + timedelta(days=i), i * 10) for i in range(30)]
        data = DailyActivityData(
            days=days,
            max_minutes=290,
            period_start=start,
            period_end=start + timedelta(days=29),
        )
        chart.set_data(data)

        hint = chart.sizeHint()
        assert hint.width() > 200
        assert hint.height() == 180

    def test_minimum_size_hint(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        min_hint = chart.minimumSizeHint()
        assert min_hint.width() == 200
        assert min_hint.height() == 180

    def test_initial_data_is_none(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)
        assert chart._data is None

    def test_set_activity_data_stores_data(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        data = ActivityChartData(
            period_type=ActivityPeriodType.MONTHLY,
            buckets=[
                ActivityBucketData(
                    label="1月",
                    total_minutes=60,
                    period_start=date(2026, 1, 1),
                    period_end=date(2026, 1, 31),
                ),
                ActivityBucketData(
                    label="2月",
                    total_minutes=120,
                    period_start=date(2026, 2, 1),
                    period_end=date(2026, 2, 28),
                ),
            ],
            max_minutes=120,
        )
        chart.set_activity_data(data)
        assert chart._activity_data is not None
        assert chart._activity_data.max_minutes == 120
        assert chart._data is None

    def test_set_activity_data_clears_legacy_data(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        # Set legacy data first
        legacy = DailyActivityData(
            days=[DailyStudyData(date(2026, 2, 26), 30)],
            max_minutes=30,
            period_start=date(2026, 2, 26),
            period_end=date(2026, 2, 26),
        )
        chart.set_data(legacy)
        assert chart._data is not None

        # Set activity data — should clear legacy
        data = ActivityChartData(
            period_type=ActivityPeriodType.WEEKLY,
            buckets=[],
            max_minutes=0,
        )
        chart.set_activity_data(data)
        assert chart._data is None
        assert chart._activity_data is not None

    def test_set_data_clears_activity_data(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        # Set activity data first
        activity = ActivityChartData(
            period_type=ActivityPeriodType.YEARLY,
            buckets=[
                ActivityBucketData("2026", 60, date(2026, 1, 1), date(2026, 12, 31)),
            ],
            max_minutes=60,
        )
        chart.set_activity_data(activity)
        assert chart._activity_data is not None

        # Set legacy data — should clear activity data
        legacy = DailyActivityData(
            days=[DailyStudyData(date(2026, 2, 26), 30)],
            max_minutes=30,
            period_start=date(2026, 2, 26),
            period_end=date(2026, 2, 26),
        )
        chart.set_data(legacy)
        assert chart._activity_data is None
        assert chart._data is not None


class TestDailyActivityChartTooltip:
    """ツールチップ機能のテスト."""

    def test_mouse_tracking_enabled(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)
        assert chart.hasMouseTracking() is True

    def test_format_tooltip_minutes_only(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)
        assert chart._format_tooltip("2/27", 45) == "2/27: 45min"

    def test_format_tooltip_hours_and_minutes(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)
        assert chart._format_tooltip("1月", 90) == "1月: 1h 30min"

    def test_format_tooltip_exact_hours(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)
        assert chart._format_tooltip("2026", 60) == "2026: 1h 00min"

    def test_format_tooltip_zero_minutes(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)
        assert chart._format_tooltip("2/27", 0) == "2/27: 0min"

    def test_find_bar_index_valid(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        data = ActivityChartData(
            period_type=ActivityPeriodType.MONTHLY,
            buckets=[
                ActivityBucketData("1月", 60, date(2026, 1, 1), date(2026, 1, 31)),
                ActivityBucketData("2月", 120, date(2026, 2, 1), date(2026, 2, 28)),
            ],
            max_minutes=120,
        )
        chart.set_activity_data(data)

        bar_width = 20.0
        bar_spacing = 5.0
        # First bar: x=48 to x=68
        assert chart._find_bar_index(48 + 10, bar_width, bar_spacing) == 0
        # Second bar: x=73 to x=93
        assert chart._find_bar_index(73 + 10, bar_width, bar_spacing) == 1

    def test_find_bar_index_in_spacing(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        data = ActivityChartData(
            period_type=ActivityPeriodType.MONTHLY,
            buckets=[
                ActivityBucketData("1月", 60, date(2026, 1, 1), date(2026, 1, 31)),
                ActivityBucketData("2月", 120, date(2026, 2, 1), date(2026, 2, 28)),
            ],
            max_minutes=120,
        )
        chart.set_activity_data(data)

        bar_width = 20.0
        bar_spacing = 5.0
        # Spacing between bars: x=68 to x=73
        assert chart._find_bar_index(48 + 21, bar_width, bar_spacing) is None

    def test_find_bar_index_before_chart(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        data = ActivityChartData(
            period_type=ActivityPeriodType.DAILY,
            buckets=[
                ActivityBucketData("2/27", 30, date(2026, 2, 27), date(2026, 2, 27)),
            ],
            max_minutes=30,
        )
        chart.set_activity_data(data)

        assert chart._find_bar_index(10.0, 20.0, 5.0) is None

    def test_find_bar_index_out_of_range(self, qtbot, theme_manager):
        chart = DailyActivityChart(theme_manager)
        qtbot.addWidget(chart)

        data = ActivityChartData(
            period_type=ActivityPeriodType.DAILY,
            buckets=[
                ActivityBucketData("2/27", 30, date(2026, 2, 27), date(2026, 2, 27)),
            ],
            max_minutes=30,
        )
        chart.set_activity_data(data)

        # Far beyond the single bar
        assert chart._find_bar_index(500.0, 20.0, 5.0) is None
