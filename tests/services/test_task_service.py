"""TaskServiceのテスト."""

from datetime import date
from pathlib import Path

import pytest

from study_python.models.task import TaskStatus
from study_python.repositories.json_storage import JsonStorage
from study_python.repositories.task_repository import TaskRepository
from study_python.services.task_service import TaskService


@pytest.fixture
def service(tmp_path: Path) -> TaskService:
    storage = JsonStorage(tmp_path / "tasks.json")
    repo = TaskRepository(storage)
    return TaskService(repo)


class TestTaskServiceCreate:
    """create_taskのテスト."""

    def test_create_task(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="セクション1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        assert task.title == "セクション1"
        assert task.status == TaskStatus.NOT_STARTED
        assert task.progress == 0
        assert task.order == 0

    def test_create_task_auto_increments_order(self, service):
        service.create_task(
            goal_id="goal-1",
            title="タスク1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        task2 = service.create_task(
            goal_id="goal-1",
            title="タスク2",
            start_date=date(2026, 3, 16),
            end_date=date(2026, 3, 31),
        )
        assert task2.order == 1

    def test_create_task_with_memo(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            memo="メモ内容",
        )
        assert task.memo == "メモ内容"

    def test_create_task_empty_title_raises(self, service):
        with pytest.raises(ValueError, match="タスク名は必須"):
            service.create_task(
                goal_id="goal-1",
                title="",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 15),
            )

    def test_create_task_whitespace_title_raises(self, service):
        with pytest.raises(ValueError, match="タスク名は必須"):
            service.create_task(
                goal_id="goal-1",
                title="   ",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 15),
            )

    def test_create_task_end_before_start_raises(self, service):
        with pytest.raises(ValueError, match="終了日は開始日以降"):
            service.create_task(
                goal_id="goal-1",
                title="test",
                start_date=date(2026, 3, 15),
                end_date=date(2026, 3, 1),
            )


class TestTaskServiceUpdate:
    """update_taskのテスト."""

    def test_update_task(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="original",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        updated = service.update_task(
            task_id=task.id,
            title="updated",
            start_date=date(2026, 3, 5),
            end_date=date(2026, 3, 20),
            status=TaskStatus.IN_PROGRESS,
            progress=50,
            memo="更新メモ",
        )
        assert updated is not None
        assert updated.title == "updated"
        assert updated.progress == 50
        assert updated.status == TaskStatus.IN_PROGRESS

    def test_update_nonexistent_returns_none(self, service):
        result = service.update_task(
            task_id="nonexistent",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            status=TaskStatus.NOT_STARTED,
            progress=0,
        )
        assert result is None

    def test_update_empty_title_raises(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        with pytest.raises(ValueError, match="タスク名は必須"):
            service.update_task(
                task_id=task.id,
                title="",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 15),
                status=TaskStatus.NOT_STARTED,
                progress=0,
            )

    def test_update_invalid_progress_raises(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        with pytest.raises(ValueError, match="進捗率は0-100"):
            service.update_task(
                task_id=task.id,
                title="test",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 15),
                status=TaskStatus.NOT_STARTED,
                progress=150,
            )

    def test_update_end_before_start_raises(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        with pytest.raises(ValueError, match="終了日は開始日以降"):
            service.update_task(
                task_id=task.id,
                title="test",
                start_date=date(2026, 3, 15),
                end_date=date(2026, 3, 1),
                status=TaskStatus.NOT_STARTED,
                progress=0,
            )


class TestTaskServiceDelete:
    """delete_taskのテスト."""

    def test_delete_task(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        assert service.delete_task(task.id) is True

    def test_delete_nonexistent_returns_false(self, service):
        assert service.delete_task("nonexistent") is False


class TestTaskServiceGetTasks:
    """タスク取得のテスト."""

    def test_get_tasks_for_goal(self, service):
        service.create_task(
            goal_id="goal-1",
            title="タスク1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        service.create_task(
            goal_id="goal-2",
            title="タスク2",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        tasks = service.get_tasks_for_goal("goal-1")
        assert len(tasks) == 1

    def test_get_all_tasks(self, service):
        service.create_task(
            goal_id="goal-1",
            title="タスク1",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        service.create_task(
            goal_id="goal-2",
            title="タスク2",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        assert len(service.get_all_tasks()) == 2


class TestTaskServiceUpdateProgress:
    """update_progressのテスト."""

    def test_progress_zero_sets_not_started(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        updated = service.update_progress(task.id, 0)
        assert updated is not None
        assert updated.status == TaskStatus.NOT_STARTED

    def test_progress_50_sets_in_progress(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        updated = service.update_progress(task.id, 50)
        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS

    def test_progress_100_sets_completed(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        updated = service.update_progress(task.id, 100)
        assert updated is not None
        assert updated.status == TaskStatus.COMPLETED

    def test_progress_1_sets_in_progress(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        updated = service.update_progress(task.id, 1)
        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS

    def test_progress_99_sets_in_progress(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        updated = service.update_progress(task.id, 99)
        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS

    def test_progress_invalid_raises(self, service):
        task = service.create_task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        with pytest.raises(ValueError):
            service.update_progress(task.id, -1)

    def test_progress_nonexistent_returns_none(self, service):
        result = service.update_progress("nonexistent", 50)
        assert result is None
