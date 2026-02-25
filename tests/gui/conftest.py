"""GUI用テストフィクスチャ."""

from pathlib import Path

import pytest

from study_python.gui.theme.theme_manager import ThemeManager
from study_python.repositories.goal_repository import GoalRepository
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.task_repository import TaskRepository
from study_python.services.goal_service import GoalService
from study_python.services.task_service import TaskService


@pytest.fixture
def theme_manager(tmp_path: Path) -> ThemeManager:
    return ThemeManager(settings_path=tmp_path / "settings.json")


@pytest.fixture
def goal_service(tmp_path: Path) -> GoalService:
    goal_storage = JsonStorage(tmp_path / "goals.json")
    task_storage = JsonStorage(tmp_path / "tasks.json")
    goal_repo = GoalRepository(goal_storage)
    task_repo = TaskRepository(task_storage)
    return GoalService(goal_repo, task_repo)


@pytest.fixture
def task_service(tmp_path: Path) -> TaskService:
    storage = JsonStorage(tmp_path / "tasks.json")
    repo = TaskRepository(storage)
    return TaskService(repo)
