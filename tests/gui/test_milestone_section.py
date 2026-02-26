"""MilestoneSectionのテスト."""

from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.milestone_section import MilestoneSection
from study_python.services.motivation_calculator import (
    Milestone,
    MilestoneData,
    MilestoneType,
)


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


class TestMilestoneSection:
    """MilestoneSectionのテスト."""

    def test_create_widget(self, qtbot, theme_manager):
        section = MilestoneSection(theme_manager)
        qtbot.addWidget(section)
        assert section is not None

    def test_initial_data_is_none(self, qtbot, theme_manager):
        section = MilestoneSection(theme_manager)
        qtbot.addWidget(section)
        assert section._data is None

    def test_initial_empty_label(self, qtbot, theme_manager):
        section = MilestoneSection(theme_manager)
        qtbot.addWidget(section)
        assert len(section._milestone_labels) == 1
        assert (
            "\u30de\u30a4\u30eb\u30b9\u30c8\u30fc\u30f3\u306f\u3042\u308a\u307e\u305b\u3093"
            in section._milestone_labels[0].text()
        )

    def test_set_data_with_achievements(self, qtbot, theme_manager):
        section = MilestoneSection(theme_manager)
        qtbot.addWidget(section)

        data = MilestoneData(
            achieved=[
                Milestone(
                    MilestoneType.TOTAL_HOURS,
                    10,
                    "\u7d2f\u8a0810\u6642\u9593\u9054\u6210\uff01",
                ),
                Milestone(
                    MilestoneType.STUDY_DAYS, 7, "\u5b66\u7fd27\u65e5\u9054\u6210\uff01"
                ),
            ],
            next_milestone=Milestone(
                MilestoneType.TOTAL_HOURS, 25, "\u7d2f\u8a0825\u6642\u9593"
            ),
        )
        section.set_data(data)

        assert section._data is not None
        assert len(section._milestone_labels) == 2
        assert (
            "\u7d2f\u8a0810\u6642\u9593\u9054\u6210"
            in section._milestone_labels[0].text()
        )
        assert "\u5b66\u7fd27\u65e5\u9054\u6210" in section._milestone_labels[1].text()

    def test_set_data_with_next_milestone(self, qtbot, theme_manager):
        section = MilestoneSection(theme_manager)
        qtbot.addWidget(section)

        data = MilestoneData(
            achieved=[],
            next_milestone=Milestone(
                MilestoneType.TOTAL_HOURS, 1, "\u7d2f\u8a081\u6642\u9593"
            ),
        )
        section.set_data(data)

        assert "\u6b21\u306e\u76ee\u6a19" in section._next_label.text()
        assert "\u7d2f\u8a081\u6642\u9593" in section._next_label.text()

    def test_set_data_no_next_milestone(self, qtbot, theme_manager):
        section = MilestoneSection(theme_manager)
        qtbot.addWidget(section)

        data = MilestoneData(
            achieved=[
                Milestone(
                    MilestoneType.TOTAL_HOURS,
                    1000,
                    "\u7d2f\u8a081000\u6642\u9593\u9054\u6210\uff01",
                ),
            ],
            next_milestone=None,
        )
        section.set_data(data)

        assert section._next_label.isHidden()

    def test_set_data_empty_achievements(self, qtbot, theme_manager):
        section = MilestoneSection(theme_manager)
        qtbot.addWidget(section)

        data = MilestoneData(
            achieved=[],
            next_milestone=Milestone(
                MilestoneType.TOTAL_HOURS, 1, "\u7d2f\u8a081\u6642\u9593"
            ),
        )
        section.set_data(data)

        assert len(section._milestone_labels) == 1
        assert (
            "\u30de\u30a4\u30eb\u30b9\u30c8\u30fc\u30f3\u306f\u3042\u308a\u307e\u305b\u3093"
            in section._milestone_labels[0].text()
        )

    def test_clear_and_update(self, qtbot, theme_manager):
        """データ更新時に前のラベルがクリアされる."""
        section = MilestoneSection(theme_manager)
        qtbot.addWidget(section)

        # 最初のデータ
        data1 = MilestoneData(
            achieved=[
                Milestone(
                    MilestoneType.TOTAL_HOURS,
                    1,
                    "\u7d2f\u8a081\u6642\u9593\u9054\u6210\uff01",
                ),
            ],
            next_milestone=None,
        )
        section.set_data(data1)
        assert len(section._milestone_labels) == 1

        # 更新データ
        data2 = MilestoneData(
            achieved=[
                Milestone(
                    MilestoneType.TOTAL_HOURS,
                    10,
                    "\u7d2f\u8a0810\u6642\u9593\u9054\u6210\uff01",
                ),
                Milestone(
                    MilestoneType.STUDY_DAYS, 7, "\u5b66\u7fd27\u65e5\u9054\u6210\uff01"
                ),
            ],
            next_milestone=Milestone(
                MilestoneType.TOTAL_HOURS, 25, "\u7d2f\u8a0825\u6642\u9593"
            ),
        )
        section.set_data(data2)
        assert len(section._milestone_labels) == 2
