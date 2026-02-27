"""ConsistencyCard（学習実施率カード）のテスト."""

from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.consistency_card import ConsistencyCard
from study_python.services.motivation_calculator import ConsistencyData


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestConsistencyCard:
    """ConsistencyCard（学習実施率カード）のテスト."""

    def test_create_widget(self, qtbot, theme_manager):
        card = ConsistencyCard(theme_manager)
        qtbot.addWidget(card)
        assert card is not None

    def test_initial_data_is_none(self, qtbot, theme_manager):
        card = ConsistencyCard(theme_manager)
        qtbot.addWidget(card)
        assert card._data is None

    def test_minimum_height(self, qtbot, theme_manager):
        card = ConsistencyCard(theme_manager)
        qtbot.addWidget(card)
        assert card.minimumHeight() == 120

    def test_initial_empty_display(self, qtbot, theme_manager):
        card = ConsistencyCard(theme_manager)
        qtbot.addWidget(card)
        assert "0%" in card._week_label.text()
        assert "0/0\u65e5" in card._week_label.text()
        assert "0%" in card._month_label.text()
        assert "0/0\u65e5" in card._month_label.text()
        assert "0%" in card._overall_label.text()

    def test_set_data_high_rate(self, qtbot, theme_manager):
        """高実施率 (80%以上) の場合."""
        card = ConsistencyCard(theme_manager)
        qtbot.addWidget(card)

        data = ConsistencyData(
            this_week_days=6,
            this_week_total=7,
            this_month_days=25,
            this_month_total=28,
            overall_rate=0.85,
            overall_study_days=85,
            overall_total_days=100,
        )
        card.set_data(data)

        assert card._data is not None
        assert "86%" in card._week_label.text()
        assert "6/7\u65e5" in card._week_label.text()
        assert "89%" in card._month_label.text()
        assert "25/28\u65e5" in card._month_label.text()
        assert "85%" in card._overall_label.text()
        assert "85/100\u65e5" in card._overall_label.text()
        # success色が使われる
        assert "#A6E3A1" in card._overall_label.styleSheet()

    def test_set_data_medium_rate(self, qtbot, theme_manager):
        """中実施率 (50-80%) の場合."""
        card = ConsistencyCard(theme_manager)
        qtbot.addWidget(card)

        data = ConsistencyData(
            this_week_days=3,
            this_week_total=5,
            this_month_days=15,
            this_month_total=28,
            overall_rate=0.6,
            overall_study_days=60,
            overall_total_days=100,
        )
        card.set_data(data)

        assert "60%" in card._week_label.text()
        assert "3/5\u65e5" in card._week_label.text()
        assert "54%" in card._month_label.text()
        assert "15/28\u65e5" in card._month_label.text()
        assert "60%" in card._overall_label.text()
        # warning色が使われる
        assert "#F9E2AF" in card._overall_label.styleSheet()

    def test_set_data_low_rate(self, qtbot, theme_manager):
        """低実施率 (50%未満) の場合."""
        card = ConsistencyCard(theme_manager)
        qtbot.addWidget(card)

        data = ConsistencyData(
            this_week_days=1,
            this_week_total=5,
            this_month_days=5,
            this_month_total=28,
            overall_rate=0.2,
            overall_study_days=20,
            overall_total_days=100,
        )
        card.set_data(data)

        assert "20%" in card._week_label.text()
        assert "1/5\u65e5" in card._week_label.text()
        assert "18%" in card._month_label.text()
        assert "5/28\u65e5" in card._month_label.text()
        assert "20%" in card._overall_label.text()
        # error色が使われる
        assert "#F38BA8" in card._overall_label.styleSheet()

    def test_set_data_zero(self, qtbot, theme_manager):
        """データがゼロの場合."""
        card = ConsistencyCard(theme_manager)
        qtbot.addWidget(card)

        data = ConsistencyData(
            this_week_days=0,
            this_week_total=3,
            this_month_days=0,
            this_month_total=15,
            overall_rate=0.0,
            overall_study_days=0,
            overall_total_days=0,
        )
        card.set_data(data)

        assert "0%" in card._week_label.text()
        assert "0/3\u65e5" in card._week_label.text()
        assert "0%" in card._month_label.text()
        assert "0/15\u65e5" in card._month_label.text()
        assert "0%" in card._overall_label.text()

    def test_rate_color_high(self, qtbot, theme_manager):
        colors = theme_manager.get_colors()
        result = ConsistencyCard._rate_color(0.9, colors)
        assert result == colors.get("success", "#A6E3A1")

    def test_rate_color_medium(self, qtbot, theme_manager):
        colors = theme_manager.get_colors()
        result = ConsistencyCard._rate_color(0.6, colors)
        assert result == colors.get("warning", "#F9E2AF")

    def test_rate_color_low(self, qtbot, theme_manager):
        colors = theme_manager.get_colors()
        result = ConsistencyCard._rate_color(0.3, colors)
        assert result == colors.get("error", "#F38BA8")

    def test_rate_color_boundary_80(self, qtbot, theme_manager):
        colors = theme_manager.get_colors()
        result = ConsistencyCard._rate_color(0.8, colors)
        assert result == colors.get("success", "#A6E3A1")

    def test_rate_color_boundary_50(self, qtbot, theme_manager):
        colors = theme_manager.get_colors()
        result = ConsistencyCard._rate_color(0.5, colors)
        assert result == colors.get("warning", "#F9E2AF")
