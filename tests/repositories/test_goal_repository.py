"""GoalRepositoryのテスト."""

from pathlib import Path

import pytest

from study_python.models.goal import Goal, WhenType
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage


@pytest.fixture
def repo(tmp_path: Path) -> GoalRepository:
    storage = JsonStorage(tmp_path / "goals.json")
    return GoalRepository(storage)


def _make_goal(**kwargs: str) -> Goal:
    defaults = {
        "why": "テスト理由",
        "when_target": "2026-06-30",
        "when_type": WhenType.DATE,
        "what": "テスト目標",
        "how": "テスト方法",
    }
    defaults.update(kwargs)
    return Goal(**defaults)


class TestGoalRepositoryGetAll:
    """get_allメソッドのテスト."""

    def test_get_all_empty(self, repo):
        assert repo.get_all() == []

    def test_get_all_returns_goals(self, repo):
        goal = _make_goal()
        repo.add(goal)
        goals = repo.get_all()
        assert len(goals) == 1
        assert goals[0].id == goal.id

    def test_get_all_multiple(self, repo):
        repo.add(_make_goal(what="目標1"))
        repo.add(_make_goal(what="目標2"))
        assert len(repo.get_all()) == 2


class TestGoalRepositoryGetById:
    """get_by_idメソッドのテスト."""

    def test_get_by_id_found(self, repo):
        goal = _make_goal()
        repo.add(goal)
        found = repo.get_by_id(goal.id)
        assert found is not None
        assert found.id == goal.id
        assert found.what == goal.what

    def test_get_by_id_not_found(self, repo):
        assert repo.get_by_id("nonexistent") is None


class TestGoalRepositoryAdd:
    """addメソッドのテスト."""

    def test_add_goal(self, repo):
        goal = _make_goal()
        repo.add(goal)
        assert len(repo.get_all()) == 1

    def test_add_preserves_data(self, repo):
        goal = _make_goal(why="特定の理由", what="特定の目標")
        repo.add(goal)
        loaded = repo.get_by_id(goal.id)
        assert loaded is not None
        assert loaded.why == "特定の理由"
        assert loaded.what == "特定の目標"


class TestGoalRepositoryUpdate:
    """updateメソッドのテスト."""

    def test_update_existing(self, repo):
        goal = _make_goal()
        repo.add(goal)
        goal.what = "更新された目標"
        result = repo.update(goal)
        assert result is True
        updated = repo.get_by_id(goal.id)
        assert updated is not None
        assert updated.what == "更新された目標"

    def test_update_nonexistent_returns_false(self, repo):
        goal = _make_goal()
        result = repo.update(goal)
        assert result is False


class TestGoalRepositoryDelete:
    """deleteメソッドのテスト."""

    def test_delete_existing(self, repo):
        goal = _make_goal()
        repo.add(goal)
        result = repo.delete(goal.id)
        assert result is True
        assert len(repo.get_all()) == 0

    def test_delete_nonexistent_returns_false(self, repo):
        result = repo.delete("nonexistent")
        assert result is False

    def test_delete_preserves_others(self, repo):
        goal1 = _make_goal(what="目標1")
        goal2 = _make_goal(what="目標2")
        repo.add(goal1)
        repo.add(goal2)
        repo.delete(goal1.id)
        remaining = repo.get_all()
        assert len(remaining) == 1
        assert remaining[0].id == goal2.id
