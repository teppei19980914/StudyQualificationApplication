"""WeeklyComparisonCardのテスト."""

from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.weekly_comparison_card import WeeklyComparisonCard
from study_python.services.motivation_calculator import WeeklyComparisonData


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestWeeklyComparisonCard:
    """WeeklyComparisonCardのテスト."""

    def test_create_widget(self, qtbot, theme_manager):
        card = WeeklyComparisonCard(theme_manager)
        qtbot.addWidget(card)
        assert card is not None

    def test_initial_data_is_none(self, qtbot, theme_manager):
        card = WeeklyComparisonCard(theme_manager)
        qtbot.addWidget(card)
        assert card._data is None

    def test_set_data_increase(self, qtbot, theme_manager):
        card = WeeklyComparisonCard(theme_manager)
        qtbot.addWidget(card)

        data = WeeklyComparisonData(
            this_week_minutes=90,
            last_week_minutes=60,
            difference_minutes=30,
            change_percent=50.0,
        )
        card.set_data(data)

        assert card._data is not None
        assert "\u4eca\u9031: 1h 30min" in card._this_week_label.text()
        assert "\u5148\u9031: 1h 00min" in card._last_week_label.text()
        assert "\u2191" in card._diff_label.text()
        assert "+30min" in card._diff_label.text()
        assert "+50.0%" in card._diff_label.text()

    def test_set_data_decrease(self, qtbot, theme_manager):
        card = WeeklyComparisonCard(theme_manager)
        qtbot.addWidget(card)

        data = WeeklyComparisonData(
            this_week_minutes=30,
            last_week_minutes=60,
            difference_minutes=-30,
            change_percent=-50.0,
        )
        card.set_data(data)

        assert "\u2193" in card._diff_label.text()
        assert "-30min" in card._diff_label.text()
        assert "-50.0%" in card._diff_label.text()

    def test_set_data_no_change(self, qtbot, theme_manager):
        card = WeeklyComparisonCard(theme_manager)
        qtbot.addWidget(card)

        data = WeeklyComparisonData(
            this_week_minutes=60,
            last_week_minutes=60,
            difference_minutes=0,
            change_percent=0.0,
        )
        card.set_data(data)

        assert "\u5909\u5316\u306a\u3057" in card._diff_label.text()

    def test_set_data_no_last_week(self, qtbot, theme_manager):
        card = WeeklyComparisonCard(theme_manager)
        qtbot.addWidget(card)

        data = WeeklyComparisonData(
            this_week_minutes=60,
            last_week_minutes=0,
            difference_minutes=60,
            change_percent=None,
        )
        card.set_data(data)

        assert "\u2191" in card._diff_label.text()
        assert "%" not in card._diff_label.text()

    def test_set_data_both_zero(self, qtbot, theme_manager):
        card = WeeklyComparisonCard(theme_manager)
        qtbot.addWidget(card)

        data = WeeklyComparisonData(
            this_week_minutes=0,
            last_week_minutes=0,
            difference_minutes=0,
            change_percent=None,
        )
        card.set_data(data)

        assert "\u5909\u5316\u306a\u3057" in card._diff_label.text()

    def test_format_duration_minutes(self, qtbot, theme_manager):
        assert WeeklyComparisonCard._format_duration(45) == "45min"

    def test_format_duration_hours(self, qtbot, theme_manager):
        assert WeeklyComparisonCard._format_duration(90) == "1h 30min"

    def test_format_duration_zero(self, qtbot, theme_manager):
        assert WeeklyComparisonCard._format_duration(0) == "0min"
