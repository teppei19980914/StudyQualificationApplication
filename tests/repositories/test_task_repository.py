"""TaskRepositoryのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.models.task import Task
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.task_repository import TaskRepository


@pytest.fixture
def repo(tmp_path: Path) -> TaskRepository:
    storage = JsonStorage(tmp_path / "tasks.json")
    return TaskRepository(storage)


def _make_task(**kwargs) -> Task:
    defaults = {
        "goal_id": "goal-1",
        "title": "テストタスク",
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 3, 15),
    }
    defaults.update(kwargs)
    return Task(**defaults)


class TestTaskRepositoryGetAll:
    """get_allメソッドのテスト."""

    def test_get_all_empty(self, repo):
        assert repo.get_all() == []

    def test_get_all_returns_tasks(self, repo):
        task = _make_task()
        repo.add(task)
        tasks = repo.get_all()
        assert len(tasks) == 1
        assert tasks[0].id == task.id


class TestTaskRepositoryGetByGoalId:
    """get_by_goal_idメソッドのテスト."""

    def test_get_by_goal_id(self, repo):
        repo.add(_make_task(goal_id="goal-1", title="タスク1"))
        repo.add(_make_task(goal_id="goal-2", title="タスク2"))
        repo.add(_make_task(goal_id="goal-1", title="タスク3"))
        tasks = repo.get_by_goal_id("goal-1")
        assert len(tasks) == 2

    def test_get_by_goal_id_empty(self, repo):
        assert repo.get_by_goal_id("nonexistent") == []

    def test_get_by_goal_id_sorted_by_order(self, repo):
        repo.add(_make_task(goal_id="goal-1", title="後", order=2))
        repo.add(_make_task(goal_id="goal-1", title="先", order=1))
        tasks = repo.get_by_goal_id("goal-1")
        assert tasks[0].title == "先"
        assert tasks[1].title == "後"


class TestTaskRepositoryGetById:
    """get_by_idメソッドのテスト."""

    def test_get_by_id_found(self, repo):
        task = _make_task()
        repo.add(task)
        found = repo.get_by_id(task.id)
        assert found is not None
        assert found.title == task.title

    def test_get_by_id_not_found(self, repo):
        assert repo.get_by_id("nonexistent") is None


class TestTaskRepositoryAdd:
    """addメソッドのテスト."""

    def test_add_task(self, repo):
        task = _make_task()
        repo.add(task)
        assert len(repo.get_all()) == 1

    def test_add_preserves_data(self, repo):
        task = _make_task(title="特定のタスク", progress=50)
        repo.add(task)
        loaded = repo.get_by_id(task.id)
        assert loaded is not None
        assert loaded.title == "特定のタスク"
        assert loaded.progress == 50


class TestTaskRepositoryUpdate:
    """updateメソッドのテスト."""

    def test_update_existing(self, repo):
        task = _make_task()
        repo.add(task)
        task.title = "更新されたタスク"
        task.progress = 75
        result = repo.update(task)
        assert result is True
        updated = repo.get_by_id(task.id)
        assert updated is not None
        assert updated.title == "更新されたタスク"
        assert updated.progress == 75

    def test_update_nonexistent_returns_false(self, repo):
        task = _make_task()
        assert repo.update(task) is False


class TestTaskRepositoryDelete:
    """deleteメソッドのテスト."""

    def test_delete_existing(self, repo):
        task = _make_task()
        repo.add(task)
        assert repo.delete(task.id) is True
        assert len(repo.get_all()) == 0

    def test_delete_nonexistent_returns_false(self, repo):
        assert repo.delete("nonexistent") is False

    def test_delete_preserves_others(self, repo):
        task1 = _make_task(title="タスク1")
        task2 = _make_task(title="タスク2")
        repo.add(task1)
        repo.add(task2)
        repo.delete(task1.id)
        remaining = repo.get_all()
        assert len(remaining) == 1
        assert remaining[0].id == task2.id


class TestTaskRepositoryDeleteByGoalId:
    """delete_by_goal_idメソッドのテスト."""

    def test_delete_by_goal_id(self, repo):
        repo.add(_make_task(goal_id="goal-1", title="タスク1"))
        repo.add(_make_task(goal_id="goal-1", title="タスク2"))
        repo.add(_make_task(goal_id="goal-2", title="タスク3"))
        deleted = repo.delete_by_goal_id("goal-1")
        assert deleted == 2
        assert len(repo.get_all()) == 1

    def test_delete_by_goal_id_none_found(self, repo):
        repo.add(_make_task(goal_id="goal-1"))
        deleted = repo.delete_by_goal_id("goal-99")
        assert deleted == 0
        assert len(repo.get_all()) == 1
