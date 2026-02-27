"""TodayStudyBannerのテスト."""

from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.today_study_banner import TodayStudyBanner
from study_python.services.motivation_calculator import TodayStudyData


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestTodayStudyBanner:
    """TodayStudyBannerのテスト."""

    def test_create_widget(self, qtbot, theme_manager):
        banner = TodayStudyBanner(theme_manager)
        qtbot.addWidget(banner)
        assert banner is not None
        assert banner.minimumHeight() == 60

    def test_initial_data_is_none(self, qtbot, theme_manager):
        banner = TodayStudyBanner(theme_manager)
        qtbot.addWidget(banner)
        assert banner._data is None

    def test_set_data_studied(self, qtbot, theme_manager):
        banner = TodayStudyBanner(theme_manager)
        qtbot.addWidget(banner)

        data = TodayStudyData(total_minutes=45, session_count=2, studied=True)
        banner.set_data(data)

        assert banner._data is not None
        assert banner._data.studied is True
        assert (
            banner._message_label.text()
            == "\u4eca\u65e5\u3082\u5b66\u7fd2\u3057\u307e\u3057\u305f\uff01"
        )
        assert "45min" in banner._detail_label.text()
        assert "2\u30bb\u30c3\u30b7\u30e7\u30f3" in banner._detail_label.text()

    def test_set_data_not_studied(self, qtbot, theme_manager):
        banner = TodayStudyBanner(theme_manager)
        qtbot.addWidget(banner)

        data = TodayStudyData(total_minutes=0, session_count=0, studied=False)
        banner.set_data(data)

        assert banner._data is not None
        assert banner._data.studied is False
        assert (
            "\u307e\u3060\u5b66\u7fd2\u3057\u3066\u3044\u307e\u305b\u3093"
            in banner._message_label.text()
        )
        assert banner._detail_label.text() == ""

    def test_set_data_studied_with_hours(self, qtbot, theme_manager):
        banner = TodayStudyBanner(theme_manager)
        qtbot.addWidget(banner)

        data = TodayStudyData(total_minutes=90, session_count=3, studied=True)
        banner.set_data(data)

        assert "1h 30min" in banner._detail_label.text()
        assert "3\u30bb\u30c3\u30b7\u30e7\u30f3" in banner._detail_label.text()

    def test_format_duration_minutes_only(self, qtbot, theme_manager):
        assert TodayStudyBanner._format_duration(45) == "45min"

    def test_format_duration_with_hours(self, qtbot, theme_manager):
        assert TodayStudyBanner._format_duration(90) == "1h 30min"

    def test_format_duration_zero(self, qtbot, theme_manager):
        assert TodayStudyBanner._format_duration(0) == "0min"

    def test_transition_from_not_studied_to_studied(self, qtbot, theme_manager):
        """未学習→学習済みへの状態遷移."""
        banner = TodayStudyBanner(theme_manager)
        qtbot.addWidget(banner)

        not_studied = TodayStudyData(total_minutes=0, session_count=0, studied=False)
        banner.set_data(not_studied)
        assert banner._data.studied is False

        studied = TodayStudyData(total_minutes=30, session_count=1, studied=True)
        banner.set_data(studied)
        assert banner._data.studied is True
        assert "\u5b66\u7fd2\u3057\u307e\u3057\u305f" in banner._message_label.text()
