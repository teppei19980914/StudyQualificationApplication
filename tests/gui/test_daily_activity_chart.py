"""DailyActivityChartのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.daily_activity_chart import DailyActivityChart
from study_python.services.study_stats_calculator import (
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
        assert chart.height() == 180

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
