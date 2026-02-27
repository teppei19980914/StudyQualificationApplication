"""MilestoneButtonのテスト."""

from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.milestone_button import MilestoneButton
from study_python.services.motivation_calculator import (
    Milestone,
    MilestoneData,
    MilestoneType,
)


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestMilestoneButton:
    """MilestoneButtonのテスト."""

    def test_create_button(self, qtbot, theme_manager):
        button = MilestoneButton(theme_manager)
        qtbot.addWidget(button)
        assert button is not None
        assert "\U0001f3c6" in button.text()
        assert "実績" in button.text()

    def test_initial_data_none(self, qtbot, theme_manager):
        button = MilestoneButton(theme_manager)
        qtbot.addWidget(button)
        assert button._data is None

    def test_set_data(self, qtbot, theme_manager):
        button = MilestoneButton(theme_manager)
        qtbot.addWidget(button)

        data = MilestoneData(
            total_hours=10.5,
            study_days=15,
            current_streak=3,
            achieved=[
                Milestone(MilestoneType.TOTAL_HOURS, 10, "累計10時間達成！"),
            ],
            next_milestone=Milestone(MilestoneType.TOTAL_HOURS, 25, "累計25時間"),
        )
        button.set_data(data)
        assert button._data is not None
        assert button._data.total_hours == 10.5
        assert button._data.study_days == 15
        assert len(button._data.achieved) == 1

    def test_fixed_height(self, qtbot, theme_manager):
        button = MilestoneButton(theme_manager)
        qtbot.addWidget(button)
        assert button.height() == 36

    def test_tooltip(self, qtbot, theme_manager):
        button = MilestoneButton(theme_manager)
        qtbot.addWidget(button)
        assert button.toolTip() == "実績"
