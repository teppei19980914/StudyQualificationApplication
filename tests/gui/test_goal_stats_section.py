"""GoalStatsSectionのテスト."""

from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.gui.widgets.goal_stats_section import (
    GoalStatsCard,
    GoalStatsDisplayData,
    GoalStatsSection,
)
from study_python.services.study_log_service import GoalStudyStats, TaskStudyStats


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


def _make_display_data(
    name: str = "テスト目標",
    color: str = "#89B4FA",
    total_minutes: int = 120,
) -> GoalStatsDisplayData:
    """テスト用表示データを生成する."""
    return GoalStatsDisplayData(
        name=name,
        color=color,
        stats=GoalStudyStats(
            goal_id="goal-1",
            task_stats=[
                TaskStudyStats(
                    task_id="task-1",
                    total_minutes=total_minutes,
                    study_days=3,
                    log_count=5,
                ),
            ],
            total_minutes=total_minutes,
            total_study_days=3,
        ),
        task_names={"task-1": "テストタスク"},
    )


class TestGoalStatsCard:
    """GoalStatsCardのテスト."""

    def test_create_card(self, qtbot, theme_manager):
        data = _make_display_data()
        card = GoalStatsCard(data)
        qtbot.addWidget(card)
        assert card is not None

    def test_card_with_hours(self, qtbot, theme_manager):
        data = _make_display_data(total_minutes=90)
        card = GoalStatsCard(data)
        qtbot.addWidget(card)
        assert card is not None

    def test_card_with_minutes_only(self, qtbot, theme_manager):
        data = _make_display_data(total_minutes=30)
        card = GoalStatsCard(data)
        qtbot.addWidget(card)
        assert card is not None

    def test_card_zero_minutes(self, qtbot, theme_manager):
        data = GoalStatsDisplayData(
            name="空目標",
            color="#A6E3A1",
            stats=GoalStudyStats(
                goal_id="goal-2",
                task_stats=[],
                total_minutes=0,
                total_study_days=0,
            ),
            task_names={},
        )
        card = GoalStatsCard(data)
        qtbot.addWidget(card)
        assert card is not None


class TestGoalStatsSection:
    """GoalStatsSectionのテスト."""

    def test_create_section(self, qtbot, theme_manager):
        section = GoalStatsSection(theme_manager)
        qtbot.addWidget(section)
        assert section is not None

    def test_combo_has_two_items(self, qtbot, theme_manager):
        section = GoalStatsSection(theme_manager)
        qtbot.addWidget(section)
        assert section._combo.count() == 2
        assert section._combo.itemText(0) == "目標"
        assert section._combo.itemText(1) == "読書"

    def test_default_type_is_goals(self, qtbot, theme_manager):
        section = GoalStatsSection(theme_manager)
        qtbot.addWidget(section)
        assert section._get_current_type() == "goals"

    def test_set_goal_data_and_display(self, qtbot, theme_manager):
        section = GoalStatsSection(theme_manager)
        qtbot.addWidget(section)

        data = [
            _make_display_data("目標A", "#89B4FA"),
            _make_display_data("目標B", "#A6E3A1"),
        ]
        section.set_goal_data(data)
        assert len(section._cards) == 2

    def test_set_book_data_and_switch(self, qtbot, theme_manager):
        section = GoalStatsSection(theme_manager)
        qtbot.addWidget(section)

        goal_data = [_make_display_data("目標A")]
        book_data = [
            _make_display_data("書籍A", "#F5C2E7"),
            _make_display_data("書籍B", "#CBA6F7"),
            _make_display_data("書籍C", "#F38BA8"),
        ]
        section.set_goal_data(goal_data)
        section.set_book_data(book_data)

        # 初期は目標表示
        assert len(section._cards) == 1

        # 読書に切替
        section._combo.setCurrentIndex(1)
        assert len(section._cards) == 3

        # 目標に戻す
        section._combo.setCurrentIndex(0)
        assert len(section._cards) == 1

    def test_empty_data(self, qtbot, theme_manager):
        section = GoalStatsSection(theme_manager)
        qtbot.addWidget(section)

        section.set_goal_data([])
        assert len(section._cards) == 0

    def test_set_book_data_while_goals_selected(self, qtbot, theme_manager):
        """目標選択中に読書データ設定してもカードは更新されない."""
        section = GoalStatsSection(theme_manager)
        qtbot.addWidget(section)

        goal_data = [_make_display_data("目標A")]
        section.set_goal_data(goal_data)
        assert len(section._cards) == 1

        book_data = [_make_display_data("書籍A"), _make_display_data("書籍B")]
        section.set_book_data(book_data)
        # 目標が選択されているのでカード数は変わらない
        assert len(section._cards) == 1

    def test_clear_cards_on_update(self, qtbot, theme_manager):
        """データ更新時に前のカードがクリアされる."""
        section = GoalStatsSection(theme_manager)
        qtbot.addWidget(section)

        data1 = [_make_display_data("目標A")]
        section.set_goal_data(data1)
        assert len(section._cards) == 1

        data2 = [_make_display_data("目標B"), _make_display_data("目標C")]
        section.set_goal_data(data2)
        assert len(section._cards) == 2
