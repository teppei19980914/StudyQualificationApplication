"""GoalPageとGanttPageのテスト."""

from pathlib import Path

import pytest

from study_python.gui.pages.gantt_page import GanttPage
from study_python.gui.pages.goal_page import GoalCard, GoalPage
from study_python.gui.theme.theme_manager import ThemeManager
from study_python.models.goal import Goal, WhenType
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.task_repository import TaskRepository
from study_python.services.goal_service import GoalService
from study_python.services.task_service import TaskService


@pytest.fixture
def services(tmp_path: Path):
    goal_storage = JsonStorage(tmp_path / "goals.json")
    task_storage = JsonStorage(tmp_path / "tasks.json")
    goal_repo = GoalRepository(goal_storage)
    task_repo = TaskRepository(task_storage)
    goal_service = GoalService(goal_repo, task_repo)
    task_service = TaskService(task_repo)
    theme_manager = ThemeManager(tmp_path / "settings.json")
    return goal_service, task_service, theme_manager


class TestGoalCard:
    """GoalCardのテスト."""

    def test_create_card(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="テスト理由",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS資格",
            how="Udemy",
            color="#4A9EFF",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        assert card.objectName() == "goal_card"

    def test_card_edit_signal(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        with qtbot.waitSignal(card.edit_requested, timeout=1000):
            card.edit_requested.emit(goal.id)

    def test_card_delete_signal(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        with qtbot.waitSignal(card.delete_requested, timeout=1000):
            card.delete_requested.emit(goal.id)

    def test_card_period_type_format(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="test",
            when_target="3ヶ月",
            when_type=WhenType.PERIOD,
            what="TOEIC",
            how="test",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        assert card._format_when() == "目標: 3ヶ月"

    def test_card_date_type_format(self, qtbot, services):
        _, _, theme_manager = services
        goal = Goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        card = GoalCard(goal, theme_manager)
        qtbot.addWidget(card)
        assert "2026/06/30" in card._format_when()


class TestGoalPage:
    """GoalPageのテスト."""

    def test_create_page(self, qtbot, services):
        goal_service, _, theme_manager = services
        page = GoalPage(goal_service, theme_manager)
        qtbot.addWidget(page)
        assert page is not None

    def test_empty_state(self, qtbot, services):
        goal_service, _, theme_manager = services
        page = GoalPage(goal_service, theme_manager)
        qtbot.addWidget(page)
        # 空の状態でも表示できる
        assert page._cards_layout.count() >= 1  # stretch item

    def test_theme_changed(self, qtbot, services):
        goal_service, _, theme_manager = services
        page = GoalPage(goal_service, theme_manager)
        qtbot.addWidget(page)
        page.on_theme_changed()  # エラーなく実行

    def test_goals_changed_signal_exists(self, qtbot, services):
        goal_service, _, theme_manager = services
        page = GoalPage(goal_service, theme_manager)
        qtbot.addWidget(page)
        # Signal exists
        assert hasattr(page, "goals_changed")


class TestGanttPage:
    """GanttPageのテスト."""

    def test_create_page(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        assert page is not None

    def test_refresh_empty(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()  # エラーなく実行

    def test_refresh_with_goals(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        goal_service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="テスト",
            how="test",
        )
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()
        assert page._goal_combo.count() == 1

    def test_theme_changed(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.on_theme_changed()

    def test_goal_combo_selection(self, qtbot, services):
        goal_service, task_service, theme_manager = services
        goal_service.create_goal(
            why="test1",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="目標1",
            how="test",
        )
        goal_service.create_goal(
            why="test2",
            when_target="2026-12-31",
            when_type=WhenType.DATE,
            what="目標2",
            how="test",
        )
        page = GanttPage(goal_service, task_service, theme_manager)
        qtbot.addWidget(page)
        page.refresh()
        assert page._goal_combo.count() == 2
