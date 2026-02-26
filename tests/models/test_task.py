"""Taskモデルのテスト."""

from datetime import date, datetime

import pytest

from study_python.models.task import Task, TaskStatus


class TestTaskCreation:
    """Taskの生成テスト."""

    def test_create_task_with_required_fields(self):
        task = Task(
            goal_id="goal-1",
            title="セクション1を学習",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        assert task.goal_id == "goal-1"
        assert task.title == "セクション1を学習"
        assert task.start_date == date(2026, 3, 1)
        assert task.end_date == date(2026, 3, 15)
        assert task.status == TaskStatus.NOT_STARTED
        assert task.progress == 0
        assert task.memo == ""
        assert task.book_id == ""
        assert task.order == 0
        assert task.id  # UUIDが生成される

    def test_create_task_with_all_fields(self):
        task = Task(
            id="task-1",
            goal_id="goal-1",
            title="テスト",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            status=TaskStatus.IN_PROGRESS,
            progress=50,
            memo="半分完了",
            book_id="book-1",
            order=1,
        )
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.progress == 50
        assert task.memo == "半分完了"
        assert task.book_id == "book-1"
        assert task.order == 1

    def test_create_task_same_start_end_date(self):
        task = Task(
            goal_id="goal-1",
            title="1日タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 1),
        )
        assert task.duration_days == 1


class TestTaskValidation:
    """Taskのバリデーションテスト."""

    def test_progress_below_zero_raises(self):
        with pytest.raises(ValueError, match="進捗率は0-100"):
            Task(
                goal_id="goal-1",
                title="test",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 15),
                progress=-1,
            )

    def test_progress_above_100_raises(self):
        with pytest.raises(ValueError, match="進捗率は0-100"):
            Task(
                goal_id="goal-1",
                title="test",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 15),
                progress=101,
            )

    def test_end_date_before_start_date_raises(self):
        with pytest.raises(ValueError, match="終了日は開始日以降"):
            Task(
                goal_id="goal-1",
                title="test",
                start_date=date(2026, 3, 15),
                end_date=date(2026, 3, 1),
            )

    def test_progress_boundary_zero(self):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            progress=0,
        )
        assert task.progress == 0

    def test_progress_boundary_100(self):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            progress=100,
        )
        assert task.progress == 100


class TestTaskDuration:
    """duration_daysのテスト."""

    def test_duration_multiple_days(self):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
        )
        assert task.duration_days == 15

    def test_duration_single_day(self):
        task = Task(
            goal_id="goal-1",
            title="test",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 1),
        )
        assert task.duration_days == 1


class TestTaskSerialization:
    """Taskの直列化テスト."""

    def test_to_dict(self):
        now = datetime(2026, 2, 25, 10, 0, 0)
        task = Task(
            id="task-1",
            goal_id="goal-1",
            title="テストタスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            status=TaskStatus.IN_PROGRESS,
            progress=30,
            memo="進行中",
            order=2,
            created_at=now,
            updated_at=now,
        )
        d = task.to_dict()
        assert d["id"] == "task-1"
        assert d["goal_id"] == "goal-1"
        assert d["title"] == "テストタスク"
        assert d["start_date"] == "2026-03-01"
        assert d["end_date"] == "2026-03-15"
        assert d["status"] == "in_progress"
        assert d["progress"] == 30
        assert d["memo"] == "進行中"
        assert d["book_id"] == ""
        assert d["order"] == 2

    def test_from_dict(self):
        data = {
            "id": "task-1",
            "goal_id": "goal-1",
            "title": "テストタスク",
            "start_date": "2026-03-01",
            "end_date": "2026-03-15",
            "status": "completed",
            "progress": 100,
            "memo": "完了",
            "order": 0,
            "created_at": "2026-02-25T10:00:00",
            "updated_at": "2026-02-25T10:00:00",
        }
        task = Task.from_dict(data)
        assert task.id == "task-1"
        assert task.goal_id == "goal-1"
        assert task.start_date == date(2026, 3, 1)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100

    def test_from_dict_missing_book_id(self):
        data = {
            "id": "task-2",
            "goal_id": "goal-1",
            "title": "旧データ",
            "start_date": "2026-03-01",
            "end_date": "2026-03-15",
            "status": "not_started",
            "progress": 0,
            "created_at": "2026-02-25T10:00:00",
            "updated_at": "2026-02-25T10:00:00",
        }
        task = Task.from_dict(data)
        assert task.book_id == ""

    def test_to_dict_with_book_id(self):
        now = datetime(2026, 2, 25, 10, 0, 0)
        task = Task(
            id="task-3",
            goal_id="goal-1",
            title="書籍タスク",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 15),
            book_id="book-1",
            created_at=now,
            updated_at=now,
        )
        d = task.to_dict()
        assert d["book_id"] == "book-1"

    def test_roundtrip_serialization(self):
        original = Task(
            goal_id="goal-1",
            title="往復テスト",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
            status=TaskStatus.IN_PROGRESS,
            progress=45,
            memo="テストメモ",
        )
        restored = Task.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.goal_id == original.goal_id
        assert restored.title == original.title
        assert restored.start_date == original.start_date
        assert restored.end_date == original.end_date
        assert restored.status == original.status
        assert restored.progress == original.progress


class TestTaskStatus:
    """TaskStatus列挙型のテスト."""

    def test_not_started_value(self):
        assert TaskStatus.NOT_STARTED.value == "not_started"

    def test_in_progress_value(self):
        assert TaskStatus.IN_PROGRESS.value == "in_progress"

    def test_completed_value(self):
        assert TaskStatus.COMPLETED.value == "completed"

    def test_from_string(self):
        assert TaskStatus("not_started") == TaskStatus.NOT_STARTED
        assert TaskStatus("in_progress") == TaskStatus.IN_PROGRESS
        assert TaskStatus("completed") == TaskStatus.COMPLETED

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            TaskStatus("invalid")
