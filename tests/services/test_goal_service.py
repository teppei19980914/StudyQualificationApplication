"""GoalServiceのテスト."""

from pathlib import Path

import pytest

from study_python.models.goal import GOAL_COLORS, WhenType
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.task_repository import TaskRepository
from study_python.services.goal_service import GoalService


@pytest.fixture
def service(tmp_path: Path) -> GoalService:
    goal_storage = JsonStorage(tmp_path / "goals.json")
    task_storage = JsonStorage(tmp_path / "tasks.json")
    goal_repo = GoalRepository(goal_storage)
    task_repo = TaskRepository(task_storage)
    return GoalService(goal_repo, task_repo)


class TestGoalServiceCreate:
    """create_goalのテスト."""

    def test_create_goal(self, service):
        goal = service.create_goal(
            why="キャリアアップ",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="AWS資格",
            how="Udemy",
        )
        assert goal.why == "キャリアアップ"
        assert goal.what == "AWS資格"
        assert goal.color == GOAL_COLORS[0]

    def test_create_goal_assigns_different_colors(self, service):
        g1 = service.create_goal(
            why="a",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="目標1",
            how="方法1",
        )
        g2 = service.create_goal(
            why="b",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="目標2",
            how="方法2",
        )
        assert g1.color != g2.color

    def test_create_goal_empty_why_raises(self, service):
        with pytest.raises(ValueError, match="why"):
            service.create_goal(
                why="",
                when_target="2026-06-30",
                when_type=WhenType.DATE,
                what="test",
                how="test",
            )

    def test_create_goal_empty_what_raises(self, service):
        with pytest.raises(ValueError, match="what"):
            service.create_goal(
                why="test",
                when_target="2026-06-30",
                when_type=WhenType.DATE,
                what="",
                how="test",
            )

    def test_create_goal_whitespace_only_raises(self, service):
        with pytest.raises(ValueError, match="why"):
            service.create_goal(
                why="   ",
                when_target="2026-06-30",
                when_type=WhenType.DATE,
                what="test",
                how="test",
            )

    def test_create_goal_empty_when_target_raises(self, service):
        with pytest.raises(ValueError, match="when_target"):
            service.create_goal(
                why="test",
                when_target="",
                when_type=WhenType.DATE,
                what="test",
                how="test",
            )

    def test_create_goal_empty_how_raises(self, service):
        with pytest.raises(ValueError, match="how"):
            service.create_goal(
                why="test",
                when_target="2026-06-30",
                when_type=WhenType.DATE,
                what="test",
                how="",
            )


class TestGoalServiceGetAll:
    """get_all_goalsのテスト."""

    def test_get_all_empty(self, service):
        assert service.get_all_goals() == []

    def test_get_all_returns_created(self, service):
        service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        goals = service.get_all_goals()
        assert len(goals) == 1


class TestGoalServiceGetGoal:
    """get_goalのテスト."""

    def test_get_goal_found(self, service):
        created = service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        found = service.get_goal(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_goal_not_found(self, service):
        assert service.get_goal("nonexistent") is None


class TestGoalServiceUpdate:
    """update_goalのテスト."""

    def test_update_goal(self, service):
        created = service.create_goal(
            why="original",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="original",
            how="original",
        )
        updated = service.update_goal(
            goal_id=created.id,
            why="updated",
            when_target="2026-12-31",
            when_type=WhenType.PERIOD,
            what="updated",
            how="updated",
        )
        assert updated is not None
        assert updated.why == "updated"
        assert updated.when_type == WhenType.PERIOD

    def test_update_nonexistent_returns_none(self, service):
        result = service.update_goal(
            goal_id="nonexistent",
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        assert result is None

    def test_update_with_empty_field_raises(self, service):
        created = service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        with pytest.raises(ValueError):
            service.update_goal(
                goal_id=created.id,
                why="",
                when_target="2026-06-30",
                when_type=WhenType.DATE,
                what="test",
                how="test",
            )


class TestGoalServiceDelete:
    """delete_goalのテスト."""

    def test_delete_goal(self, service):
        created = service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        assert service.delete_goal(created.id) is True
        assert len(service.get_all_goals()) == 0

    def test_delete_nonexistent_returns_false(self, service):
        assert service.delete_goal("nonexistent") is False

    def test_delete_goal_cascades_tasks(self, service, tmp_path):
        from datetime import date

        from study_python.models.task import Task

        goal = service.create_goal(
            why="test",
            when_target="2026-06-30",
            when_type=WhenType.DATE,
            what="test",
            how="test",
        )
        task = Task(
            goal_id=goal.id,
            title="テストタスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        service.task_repo.add(task)
        assert len(service.task_repo.get_all()) == 1
        service.delete_goal(goal.id)
        assert len(service.task_repo.get_all()) == 0


class TestGoalServiceColorAssignment:
    """色の自動割り当てテスト."""

    def test_colors_cycle_when_exhausted(self, service):
        for i in range(len(GOAL_COLORS) + 1):
            service.create_goal(
                why=f"reason{i}",
                when_target="2026-06-30",
                when_type=WhenType.DATE,
                what=f"goal{i}",
                how=f"method{i}",
            )
        goals = service.get_all_goals()
        assert len(goals) == len(GOAL_COLORS) + 1
