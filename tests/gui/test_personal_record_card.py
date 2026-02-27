"""PersonalRecordCardのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.personal_record_card import PersonalRecordCard
from study_python.services.motivation_calculator import PersonalRecordData


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestPersonalRecordCard:
    """PersonalRecordCardのテスト."""

    def test_create_widget(self, qtbot, theme_manager):
        card = PersonalRecordCard(theme_manager)
        qtbot.addWidget(card)
        assert card is not None

    def test_initial_data_is_none(self, qtbot, theme_manager):
        card = PersonalRecordCard(theme_manager)
        qtbot.addWidget(card)
        assert card._data is None

    def test_minimum_height(self, qtbot, theme_manager):
        card = PersonalRecordCard(theme_manager)
        qtbot.addWidget(card)
        assert card.minimumHeight() == 120

    def test_initial_empty_display(self, qtbot, theme_manager):
        card = PersonalRecordCard(theme_manager)
        qtbot.addWidget(card)
        assert "---" in card._best_day_label.text()
        assert "---" in card._best_week_label.text()
        assert "0\u65e5" in card._longest_streak_label.text()
        assert "0.0h" in card._total_label.text()

    def test_set_data_with_records(self, qtbot, theme_manager):
        card = PersonalRecordCard(theme_manager)
        qtbot.addWidget(card)

        data = PersonalRecordData(
            best_day_minutes=180,
            best_day_date=date(2026, 2, 20),
            best_week_minutes=600,
            best_week_start=date(2026, 2, 16),
            longest_streak=14,
            total_hours=50.5,
            total_study_days=30,
        )
        card.set_data(data)

        assert card._data is not None
        assert "3h 00min" in card._best_day_label.text()
        assert "2026-02-20" in card._best_day_label.text()
        assert "10h 00min" in card._best_week_label.text()
        assert "2026-02-16" in card._best_week_label.text()
        assert "14\u65e5" in card._longest_streak_label.text()
        assert "50.5h" in card._total_label.text()
        assert "30\u65e5" in card._total_label.text()

    def test_set_data_empty_records(self, qtbot, theme_manager):
        card = PersonalRecordCard(theme_manager)
        qtbot.addWidget(card)

        data = PersonalRecordData(
            best_day_minutes=0,
            best_day_date=None,
            best_week_minutes=0,
            best_week_start=None,
            longest_streak=0,
            total_hours=0.0,
            total_study_days=0,
        )
        card.set_data(data)

        assert "---" in card._best_day_label.text()
        assert "---" in card._best_week_label.text()
        assert "0\u65e5" in card._longest_streak_label.text()
        assert "0.0h" in card._total_label.text()

    def test_set_data_minutes_only(self, qtbot, theme_manager):
        """1時間未満の場合のフォーマット確認."""
        card = PersonalRecordCard(theme_manager)
        qtbot.addWidget(card)

        data = PersonalRecordData(
            best_day_minutes=45,
            best_day_date=date(2026, 2, 10),
            best_week_minutes=45,
            best_week_start=date(2026, 2, 9),
            longest_streak=1,
            total_hours=0.8,
            total_study_days=1,
        )
        card.set_data(data)

        assert "45min" in card._best_day_label.text()
        assert "45min" in card._best_week_label.text()

    def test_format_duration_minutes(self, qtbot, theme_manager):
        assert PersonalRecordCard._format_duration(45) == "45min"

    def test_format_duration_hours(self, qtbot, theme_manager):
        assert PersonalRecordCard._format_duration(90) == "1h 30min"

    def test_format_duration_zero(self, qtbot, theme_manager):
        assert PersonalRecordCard._format_duration(0) == "0min"
