"""MilestonePopupのテスト."""

from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.milestone_popup import MilestonePopup
from study_python.services.motivation_calculator import (
    Milestone,
    MilestoneData,
    MilestoneType,
)


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestMilestonePopup:
    """MilestonePopupのテスト."""

    def test_create_popup(self, qtbot, theme_manager):
        data = MilestoneData()
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)
        assert popup is not None

    def test_shows_total_hours(self, qtbot, theme_manager):
        data = MilestoneData(total_hours=47.5, study_days=23, current_streak=5)
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)

        assert len(popup._stat_labels) == 3
        assert "47.5時間" in popup._stat_labels[0].text()

    def test_shows_study_days(self, qtbot, theme_manager):
        data = MilestoneData(total_hours=10.0, study_days=15, current_streak=3)
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)

        assert "15日" in popup._stat_labels[1].text()

    def test_shows_current_streak(self, qtbot, theme_manager):
        data = MilestoneData(total_hours=5.0, study_days=10, current_streak=7)
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)

        assert "7日" in popup._stat_labels[2].text()

    def test_shows_zero_values(self, qtbot, theme_manager):
        data = MilestoneData()
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)

        assert "0.0時間" in popup._stat_labels[0].text()
        assert "0日" in popup._stat_labels[1].text()
        assert "0日" in popup._stat_labels[2].text()

    def test_window_title(self, qtbot, theme_manager):
        data = MilestoneData()
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)

        assert popup.windowTitle() == "実績"

    def test_shows_achievements(self, qtbot, theme_manager):
        data = MilestoneData(
            total_hours=10.0,
            study_days=7,
            achieved=[
                Milestone(MilestoneType.TOTAL_HOURS, 10, "累計10時間達成！"),
                Milestone(MilestoneType.STUDY_DAYS, 7, "学習7日達成！"),
            ],
        )
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)

        assert len(popup._milestone_labels) == 2
        assert "累計10時間達成" in popup._milestone_labels[0].text()
        assert "学習7日達成" in popup._milestone_labels[1].text()

    def test_shows_empty_message(self, qtbot, theme_manager):
        data = MilestoneData()
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)

        assert len(popup._milestone_labels) == 1
        assert "実績はありません" in popup._milestone_labels[0].text()

    def test_shows_next_milestone(self, qtbot, theme_manager):
        data = MilestoneData(
            next_milestone=Milestone(MilestoneType.TOTAL_HOURS, 1, "累計1時間"),
        )
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)

        assert not popup._next_label.isHidden()
        assert "次の目標" in popup._next_label.text()
        assert "累計1時間" in popup._next_label.text()

    def test_hides_next_when_none(self, qtbot, theme_manager):
        data = MilestoneData(
            achieved=[
                Milestone(MilestoneType.TOTAL_HOURS, 1000, "累計1000時間達成！"),
            ],
        )
        popup = MilestonePopup(data, theme_manager)
        qtbot.addWidget(popup)

        assert popup._next_label.isHidden()
